#!/usr/bin/env python
"""
Simplified data upload script for hybrid search
Using Qdrant's recommended approach with fastembed integration
Based on: https://qdrant.tech/documentation/beginner-tutorials/hybrid-search-fastembed/
"""
import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams
import time
import requests
import re
from bs4 import BeautifulSoup
from functools import lru_cache
import json

# Load environment variables
load_dotenv()

# Get environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
CSV_FILE = os.getenv("CSV_FILE", "jan-25-released-games copy.csv")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 15))  # Reduced batch size for stability
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")
VECTOR_SIZE = 384  # BGE-small-en model size

print(f"Configuration:")
print(f"  QDRANT_URL: {QDRANT_URL}")
print(f"  COLLECTION_NAME: {COLLECTION_NAME}")
print(f"  CSV_FILE: {CSV_FILE}")
print(f"  EMBEDDING_MODEL: {EMBEDDING_MODEL}")
print(f"  SPARSE_MODEL: {SPARSE_MODEL}")
print(f"  BATCH_SIZE: {BATCH_SIZE}")

# Initialize Qdrant client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Configure the client with models
client.set_model(EMBEDDING_MODEL)
client.set_sparse_model(SPARSE_MODEL)

@lru_cache(maxsize=1000)
def get_steam_game_details(app_id):
    """Fetch detailed game information from Steam API"""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get(str(app_id), {}).get('success'):
                game_data = data[str(app_id)]['data']
                
                # Clean HTML from descriptions
                detailed_description = clean_html_description(game_data.get('detailed_description', ''))
                short_description = clean_html_description(game_data.get('short_description', ''))
                
                # Extract pricing information
                price_overview = game_data.get('price_overview', {})
                price = price_overview.get('final_formatted', '').replace('$', '') if price_overview else '0.00'
                try:
                    price = float(price)
                except:
                    price = 0.0
                
                # Get header image
                header_image = game_data.get('header_image', '')
                image_filename = f"{app_id}_header.jpg" if header_image else ''
                
                # Get reviews data
                recommendations = game_data.get('recommendations', {})
                total_reviews = recommendations.get('total', 0) if recommendations else 0
                
                # Determine price range
                if price == 0:
                    price_range = "free"
                elif price < 10:
                    price_range = "low_range"
                elif price < 30:
                    price_range = "mid_range"
                else:
                    price_range = "high_range"
                
                # Extract release year
                release_date = game_data.get('release_date', {})
                release_date_str = release_date.get('date', '') if release_date else ''
                release_year = ''
                if release_date_str:
                    # Try to extract year from date string
                    match = re.search(r'(\d{4})', release_date_str)
                    if match:
                        release_year = match.group(1)
                
                return {
                    'detailed_description': detailed_description[:1000],  # Limit length
                    'short_description': short_description,
                    'price': price,
                    'image_url': header_image,
                    'file_name': image_filename,
                    'total_reviews': total_reviews,
                    'price_range': price_range,
                    'release_year': release_year
                }
        
        # Sleep briefly to avoid rate limiting
        time.sleep(0.5)
        return None
    except Exception as e:
        print(f"Error fetching Steam data for app ID {app_id}: {str(e)}")
        return None

def clean_html_description(html_text):
    """Clean HTML tags and unwanted text from game descriptions"""
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = re.sub(r'\s+', ' ', soup.get_text()).strip()
        phrases = ["Wishlist now", "Buy now", "Early Access Game", "Available now", "About the Game"]
        for phrase in phrases:
            text = re.sub(rf'(?i){re.escape(phrase)}', '', text)
        return text
    except Exception as e:
        print(f"Error cleaning HTML: {str(e)}")
        return html_text  # Return original if cleaning fails

def check_collection_exists():
    """Check if the collection exists in Qdrant"""
    try:
        collections = client.get_collections()
        for collection in collections.collections:
            if collection.name == COLLECTION_NAME:
                collection_info = client.get_collection(COLLECTION_NAME)
                print(f"Collection '{COLLECTION_NAME}' exists with {collection_info.points_count} points.")
                return collection_info.points_count > 0
        print(f"Collection '{COLLECTION_NAME}' does not exist.")
        return False
    except Exception as e:
        print(f"Error checking collection: {str(e)}")
        return False

def create_collection():
    """Create a collection with named vectors for hybrid search"""
    try:
        # Delete collection if it exists
        try:
            client.delete_collection(collection_name=COLLECTION_NAME)
            print(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            print(f"Collection {COLLECTION_NAME} doesn't exist yet or couldn't be deleted")
        
        # Get vector and sparse vector configs directly from the client
        vectors_config = client.get_fastembed_vector_params()
        sparse_vectors_config = client.get_fastembed_sparse_vector_params()
        
        print(f"Creating collection with vector configs:")
        print(f"  Dense vectors: {json.dumps(vectors_config, default=str)}")
        print(f"  Sparse vectors: {json.dumps(sparse_vectors_config, default=str)}")
        
        # Create the collection with named vectors
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_vectors_config
        )
        
        print(f"Created new collection: {COLLECTION_NAME} with named vectors for hybrid search")
        return True
    except Exception as e:
        print(f"Error creating collection: {str(e)}")
        return False

def format_game_text(row):
    """Format game data for embedding to create better quality vectors"""
    parts = []
    
    # Add name and genre info
    parts.append(f"Name: {row.get('name', '')}")
    if row.get('genres'):
        parts.append(f"{row.get('name', '')} is a {row.get('genres', '')} game")
    
    # Add descriptions (prioritize enriched data)
    if row.get('short_description'):
        parts.append(f"Short Description: {row.get('short_description', '')}")
    if row.get('detailed_description'):
        parts.append(f"Description: {row.get('detailed_description', '')}")
    elif row.get('description'):
        parts.append(f"Description: {row.get('description', '')}")
    if row.get('about_the_game'):
        parts.append(f"About: {row.get('about_the_game', '')}")
    
    # Add metadata
    if row.get('categories'):
        parts.append(f"Categories: {row.get('categories', '')}")
    if row.get('genres'):
        parts.append(f"Genres: {row.get('genres', '')}")
    if row.get('tags'):
        parts.append(f"Tags: {row.get('tags', '')}")
    if row.get('developers'):
        parts.append(f"Developers: {row.get('developers', '')}")
    if row.get('publishers'):
        parts.append(f"Publishers: {row.get('publishers', '')}")
    if row.get('platforms'):
        parts.append(f"Platforms: {row.get('platforms', '')}")
    
    return ". ".join(part for part in parts if part.strip())

def upload_data():
    """Upload data from CSV to Qdrant with enriched information using Qdrant's .add() method"""
    try:
        # Load CSV file
        print(f"Loading data from {CSV_FILE}...")
        df = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df)} games from CSV.")
        
        # Process data in batches
        total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
        points_uploaded = 0
        
        for batch_start in range(0, len(df), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(df))
            batch_df = df.iloc[batch_start:batch_end]
            
            print(f"Processing batch {batch_start//BATCH_SIZE + 1}/{total_batches}...")
            
            # Lists to hold data for the add method
            documents = []  # Text for embedding
            metadata = []   # Metadata/payload
            ids = []        # Document IDs
            
            # First, enrich data for each game in the batch
            print(f"Enriching data for batch {batch_start//BATCH_SIZE + 1}/{total_batches}...")
            for _, row in batch_df.iterrows():
                # Create a dictionary of the row data
                row_dict = row.to_dict()
                
                # Get the Steam App ID
                app_id = row_dict.get('steam_appid', 0)
                if app_id:
                    # Fetch additional data from Steam API
                    steam_data = get_steam_game_details(app_id)
                    if steam_data:
                        # Merge Steam data with our existing data
                        row_dict.update(steam_data)
                        
                        # Calculate review sentiment
                        if row_dict.get('total_reviews', 0) == 0:
                            row_dict['review_sentiment'] = 'no_reviews'
                        elif row_dict.get('total_reviews', 0) < 10:
                            row_dict['review_sentiment'] = 'few_reviews'
                        else:
                            # We would need positive/negative counts to calculate actual sentiment
                            # For now assign a placeholder
                            row_dict['review_sentiment'] = 'mixed'
                
                # Add URL field
                game_name = row_dict.get('name', '')
                if game_name:
                    game_slug = game_name.lower().replace(' ', '-').replace(':', '').replace('\'', '')
                    game_slug = re.sub(r'[^a-z0-9-]', '', game_slug)
                    row_dict['url'] = f"/games/{game_slug}"
                
                # Format game text for embedding
                game_text = format_game_text(row_dict)
                
                # Get game ID
                game_id = int(row_dict.get('steam_appid', 0)) if 'steam_appid' in row_dict else batch_start + len(documents)
                
                # Add to batch lists
                documents.append(game_text)
                metadata.append(row_dict)
                ids.append(game_id)
            
            # Use the client's add method to automatically handle the embedding and upload
            print(f"Uploading batch {batch_start//BATCH_SIZE + 1}/{total_batches} with {len(documents)} documents...")
            result = client.add(
                collection_name=COLLECTION_NAME,
                documents=documents,
                metadata=metadata,
                ids=ids
            )
            
            # Fix for the return type - the result might be a list of points or the count
            if isinstance(result, list):
                batch_points_uploaded = len(result)
            else:
                batch_points_uploaded = result if isinstance(result, int) else len(documents)
                
            points_uploaded += batch_points_uploaded
            print(f"Uploaded batch {batch_start//BATCH_SIZE + 1}/{total_batches} - Total points: {points_uploaded}")
            
            # Small delay to avoid overwhelming Qdrant
            time.sleep(0.5)
        
        print(f"Successfully uploaded {points_uploaded} games to collection '{COLLECTION_NAME}'.")
        return True
    except Exception as e:
        print(f"Error uploading data: {str(e)}")
        return False

def test_collection():
    """Test the collection by doing a hybrid search"""
    try:
        # Check collection info
        collection_info = client.get_collection(COLLECTION_NAME)
        points_count = client.count(collection_name=COLLECTION_NAME)
        print(f"Collection info: {COLLECTION_NAME}")
        print(f"  Status: {collection_info.status}")
        print(f"  Points count: {points_count.count}")
        print(f"  Vectors config: {json.dumps(collection_info.config.params.vectors, default=str)}")
        print(f"  Sparse vectors config: {json.dumps(collection_info.config.params.sparse_vectors, default=str)}")
        
        # Try doing a search with the simple query method
        print("Testing search with the query method (hybrid search)...")
        query_text = "adventure game with good story"
        
        # The query method handles both dense and sparse vectors automatically
        results = client.query(
            collection_name=COLLECTION_NAME,
            query_text=query_text,
            limit=5
        )
        
        print(f"Search results ({len(results)} found):")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.metadata.get('name', 'Unknown')} (score: {result.score:.4f})")
            # Print a snippet of description to verify content
            description = result.metadata.get('short_description', '')
            if description:
                print(f"     {description[:100]}...")
        
        return True
    except Exception as e:
        print(f"Error testing collection: {str(e)}")
        return False

def main():
    print("========== Qdrant Data Upload Utility (Simplified Version) ==========")
    
    # Always recreate the collection to ensure it supports hybrid search
    force_recreate = True
    print("Forcing recreation of collection to support hybrid search...")
    
    if force_recreate:
        print("Recreating collection with named vectors for hybrid search...")
        if create_collection():
            if upload_data():
                print("Data uploaded successfully with hybrid search support!")
                test_collection()
            else:
                print("Failed to upload data.")
        else:
            print("Failed to create collection.")
    else:
        # Check if collection exists with data
        has_data = check_collection_exists()
        
        if not has_data:
            print("Collection doesn't exist or is empty. Creating and uploading data...")
            if create_collection():
                if upload_data():
                    print("Data uploaded successfully!")
                    test_collection()
                else:
                    print("Failed to upload data.")
            else:
                print("Failed to create collection.")
        else:
            print("Collection already exists with data. No action needed.")
            test_collection()
    
    print("========== Finished ==========")

if __name__ == "__main__":
    main() 