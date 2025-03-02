#!/usr/bin/env python
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams, PointStruct, SparseVector
from fastembed import TextEmbedding
from fastembed.sparse import SparseTextEmbedding  # Added for sparse embeddings
import numpy as np
from tqdm import tqdm
import time
import requests
import re
from bs4 import BeautifulSoup
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
CSV_FILE = os.getenv("CSV_FILE", "jan-25-released-games copy.csv")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))

print(f"Configuration:")
print(f"  QDRANT_URL: {QDRANT_URL}")
print(f"  COLLECTION_NAME: {COLLECTION_NAME}")
print(f"  CSV_FILE: {CSV_FILE}")
print(f"  EMBEDDING_MODEL: {EMBEDDING_MODEL}")
print(f"  SPARSE_MODEL: {SPARSE_MODEL}")
print(f"  BATCH_SIZE: {BATCH_SIZE}")

# Initialize Qdrant client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Define models for embedding
dense_embedder = TextEmbedding(EMBEDDING_MODEL)
sparse_embedder = SparseTextEmbedding(SPARSE_MODEL)

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
        
        # Create named vectors configuration
        vectors_config = {
            "fast-bge-small-en-v1.5": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        }
        
        # Add sparse vectors configuration
        sparse_vectors_config = {
            "fast-sparse-splade_pp_en_v1": SparseVectorParams(index=SparseIndexParams())
        }
        
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

def create_embedding_text(row):
    """
    Create a text representation for embedding a game.
    
    Args:
        row: Pandas DataFrame row representing a game
        
    Returns:
        str: Text to be embedded
    """
    name = row.get('name', '')
    genres = row.get('genres', '')
    tags = row.get('tags', '')
    description = row.get('short_description', '')
    
    embedding_text = f"Game: {name}. "
    
    if genres:
        embedding_text += f"Genres: {genres}. "
    
    if tags:
        embedding_text += f"Tags: {tags}. "
    
    if description:
        embedding_text += f"Description: {description}"
    
    return embedding_text

def process_data(df):
    """
    Process the DataFrame to clean data and prepare for embedding.
    
    Args:
        df: Pandas DataFrame of game data
        
    Returns:
        Processed DataFrame
    """
    # Convert steam_appid to string (required for Qdrant IDs)
    if 'steam_appid' in df.columns:
        df['steam_appid'] = df['steam_appid'].astype(str)
    
    # Filter out rows with missing essential data
    if 'name' in df.columns:
        df = df[df['name'].notna()]
    
    return df

def upload_data(csv_file=CSV_FILE, force_recreate=False, collection_name=COLLECTION_NAME):
    """
    Load game data from CSV and upload to Qdrant.
    
    Args:
        csv_file: Path to CSV file with game data
        force_recreate: Whether to recreate the collection if it exists
        collection_name: Name of the collection to create or update
        
    Returns:
        Number of games uploaded
    """
    start_time = time.time()
    
    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    # Create or recreate collection if needed
    if collection_name in collection_names:
        if force_recreate:
            logger.info(f"Recreating collection {collection_name}")
            client.delete_collection(collection_name=collection_name)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
        else:
            logger.info(f"Collection {collection_name} already exists, using existing collection")
    else:
        logger.info(f"Creating collection {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
    
    # Load and process data
    logger.info(f"Loading data from {csv_file}")
    df = pd.read_csv(csv_file)
    df = process_data(df)
    
    total_games = len(df)
    logger.info(f"Loaded {total_games} games from CSV")
    
    # Create embeddings and upload in batches
    points = []
    
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Creating embeddings"):
        game_id = str(row['steam_appid'])
        
        # Create text for embedding
        embedding_text = create_embedding_text(row)
        
        # Create embedding
        embedding = list(dense_embedder.embed(embedding_text))[0]
        
        # Prepare payload
        payload = {
            'name': row.get('name', ''),
            'steam_appid': game_id,
            'price': row.get('price', 0),
            'genres': row.get('genres', ''),
            'tags': row.get('tags', ''),
            'release_date': row.get('release_date', ''),
            'developers': row.get('developers', ''),
            'platforms': row.get('platforms', ''),
            'short_description': row.get('short_description', ''),
            'detailed_description': row.get('detailed_description', '')
        }
        
        # Add point to batch
        points.append(PointStruct(
            id=game_id,
            vector=embedding,
            payload=payload
        ))
        
        # Upload batch if it reaches BATCH_SIZE
        if len(points) >= BATCH_SIZE:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Uploaded batch of {len(points)} games")
            points = []
    
    # Upload any remaining points
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Uploaded final batch of {len(points)} games")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Uploaded {total_games} games in {elapsed_time:.2f} seconds")
    
    return total_games

def test_collection():
    """Test the collection by doing a hybrid search"""
    try:
        # Check collection info
        collection_info = client.get_collection(COLLECTION_NAME)
        points_count = client.count(collection_name=COLLECTION_NAME)
        print(f"Collection info: {COLLECTION_NAME}")
        print(f"  Status: {collection_info.status}")
        print(f"  Points count: {points_count.count}")
        print(f"  Vectors config: {collection_info.config.params.vectors}")
        print(f"  Sparse vectors config: {collection_info.config.params.sparse_vectors}")
        
        # Try doing a search with named vectors
        print(f"Testing search with a query using named vectors...")
        query_text = "adventure game with good story"
        
        # Generate dense embedding
        dense_embedding = list(dense_embedder.embed([query_text]))[0].tolist()
        
        # Generate sparse embedding
        sparse_embedding = list(sparse_embedder.embed([query_text]))[0]
        sparse_vec = SparseVector(
            indices=sparse_embedding.indices.tolist(),
            values=sparse_embedding.values.tolist()
        )
        
        # Search using named vectors (hybrid search)
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=("fast-bge-small-en-v1.5", dense_embedding),
            query_sparse_vector=("fast-sparse-splade_pp_en_v1", sparse_vec),
            limit=5,
            with_payload=True
        )
        
        print(f"Hybrid search results ({len(results)} found):")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.payload.get('name', 'Unknown')} (score: {result.score:.4f})")
            # Print a snippet of description to verify content
            description = result.payload.get('short_description', '')
            if description:
                print(f"     {description[:100]}...")
        
        return True
    except Exception as e:
        print(f"Error testing collection: {str(e)}")
        return False

def main():
    print("========== Qdrant Data Upload Utility ==========")
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload game data to Qdrant')
    parser.add_argument('--csv', type=str, default=CSV_FILE, help='Path to CSV file with game data')
    parser.add_argument('--force-recreate', action='store_true', help='Force recreation of collection if it exists')
    parser.add_argument('--collection', type=str, default=COLLECTION_NAME, help='Name of the collection to create or update')
    
    args = parser.parse_args()
    
    upload_data(csv_file=args.csv, force_recreate=args.force_recreate, collection_name=args.collection) 