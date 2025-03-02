import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVectorParams, SparseIndexParams, SparseVector, Filter, FieldCondition, MatchValue, RecommendStrategy
from fastembed import TextEmbedding
import os
from dotenv import load_dotenv
from tqdm import tqdm
import warnings
import requests
import re
from bs4 import BeautifulSoup
from functools import lru_cache
import numpy as np
import time
from typing import List, Dict, Optional, Union, Any
import math
import json
import random

load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
CSV_FILE = os.getenv("CSV_FILE", "jan-25-released-games copy.csv")

# Connect to Qdrant and initialize models
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Configure the client with models for hybrid search
qdrant.set_model(EMBEDDING_MODEL)
qdrant.set_sparse_model(SPARSE_MODEL)

# Get model names
DENSE_VECTOR_NAME = qdrant.get_vector_field_name()
SPARSE_VECTOR_NAME = qdrant.get_sparse_vector_field_name()

# Initialize embedder for compatibility with existing code
embedder = TextEmbedding(EMBEDDING_MODEL)

@lru_cache(maxsize=10000)
def get_steam_game_description(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get(str(app_id), {}).get('success'):
            detailed = clean_html_description(data[str(app_id)]['data'].get('detailed_description', ''))
            short = clean_html_description(data[str(app_id)]['data'].get('short_description', ''))
            return {'detailed_description': detailed, 'short_description': short}
    return {'detailed_description': '', 'short_description': ''}

def clean_html_description(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    text = re.sub(r'\s+', ' ', soup.get_text()).strip()
    phrases = ["Wishlist now", "Buy now", "Early Access Game", "Available now", "About the Game"]
    for phrase in phrases:
        text = re.sub(rf'(?i){re.escape(phrase)}', '', text)
    return text

def create_embedding_text(row):
    parts = [
        f"{row['name']} is a {row['genres']} game",
        row.get('short_description', ''),
        row.get('detailed_description', '')[:300],
        f"Tags: {row.get('tags', '')}",
        f"Developers: {row.get('developers', '')}",
        f"Platforms: {row.get('platforms', '')}"
    ]
    return ". ".join(part for part in parts if part.strip())

def create_collection():
    """Create the Qdrant collection if it doesn't exist"""
    try:
        qdrant.delete_collection(collection_name=COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        print(f"Collection {COLLECTION_NAME} doesn't exist yet or couldn't be deleted")

    # Create the collection with proper configuration
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qdrant.get_fastembed_vector_params(),
        sparse_vectors_config=qdrant.get_fastembed_sparse_vector_params()
    )
    print(f"Created a new collection: {COLLECTION_NAME}")

def upload_data_to_qdrant():
    """Upload game data to Qdrant if the collection doesn't exist or is empty"""
    # Check if the collection already has data
    try:
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        if collection_info.points_count > 0:
            print(f"Collection {COLLECTION_NAME} already has {collection_info.points_count} points.")
            print("Skipping data upload. To re-upload, delete the collection first.")
            return
    except Exception as e:
        print(f"Error checking collection: {e}")
        # Create a new collection
        create_collection()
    
    # If we reached here, we need to upload data
    print(f"Reading data from {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # Prepare documents and metadata for bulk upload
    documents = []
    metadata = []
    ids = []
    
    print("Processing games for upload...")
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Preparing data"):
        app_id = int(row["steam_appid"])
        desc = get_steam_game_description(app_id)
        
        embedding_text = create_embedding_text({**row, **desc})
        documents.append(embedding_text)
        
        metadata.append({
            "name": row["name"],
            "steam_appid": app_id,
            "price": float(row.get("price", 0.0)),
            "genres": row.get("genres", ""),
            "tags": row.get("tags", ""),
            "release_date": row.get("release_date", ""),
            "developers": row.get("developers", ""),
            "platforms": row.get("platforms", ""),
            "short_description": desc["short_description"],
            "detailed_description": desc["detailed_description"][:1000],
        })
        
        ids.append(app_id)
    
    # Use FastEmbed integration for bulk upload
    print("Uploading data to Qdrant using FastEmbed integration...")
    
    # Process in batches to avoid memory issues
    batch_size = BATCH_SIZE
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        print(f"Uploading batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}...")
        
        batch_documents = documents[i:end]
        batch_metadata = metadata[i:end]
        batch_ids = ids[i:end]
        
        qdrant.add(
            collection_name=COLLECTION_NAME,
            documents=batch_documents,
            metadata=batch_metadata,
            ids=batch_ids
        )
    
    print("Data successfully uploaded to Qdrant!")

def search_games(query, limit=12, use_hybrid=True, use_sparse=False, use_dense=False, filter_params=None):
    """
    Search for games using different vector search methods.
    
    Args:
        query (str): The search query
        limit (int): Number of results to return
        use_hybrid (bool): Whether to use hybrid search (dense + sparse vectors)
        use_sparse (bool): Whether to use only sparse vector search
        use_dense (bool): Whether to use only dense vector search
        filter_params (dict, optional): Additional filtering parameters
        
    Returns:
        dict: Search results with pagination info
    """
    print(f"DEBUG: search_games called with use_hybrid={use_hybrid}, use_sparse={use_sparse}, use_dense={use_dense}")
    try:
        # If query is empty, return random games
        if not query or not query.strip():
            random_games = get_random_games(limit=limit)
            return random_games
        
        # Prepare filter if needed
        query_filter = None
        if filter_params:
            filter_conditions = []
            
            # Add price range filter
            if filter_params.get('price_range'):
                filter_conditions.append(
                    FieldCondition(key="price_range", match=MatchValue(value=filter_params['price_range']))
                )
                
            # Add genre filter
            if filter_params.get('genre'):
                filter_conditions.append(
                    FieldCondition(key="genres", match=MatchValue(value=filter_params['genre']))
                )
            
            # Create filter object if we have conditions
            if filter_conditions:
                query_filter = Filter(must=filter_conditions)
        
        # Determine search method to use
        # Default to hybrid if no specific method is selected
        if not (use_hybrid or use_sparse or use_dense):
            use_hybrid = True
            
        # Set search parameters based on selected method
        search_params = {}
        
        if use_sparse:
            # Sparse vector only search
            search_params = {
                'collection_name': COLLECTION_NAME,
                'query_text': query,
                'query_filter': query_filter,
                'limit': limit,
                'with_payload': True,
                'search_params': {
                    'sparse_vector': {
                        'enabled': True
                    },
                    'vector': {
                        'enabled': False
                    }
                }
            }
        elif use_dense:
            # Dense vector only search
            search_params = {
                'collection_name': COLLECTION_NAME,
                'query_text': query,
                'query_filter': query_filter,
                'limit': limit,
                'with_payload': True,
                'search_params': {
                    'sparse_vector': {
                        'enabled': False
                    },
                    'vector': {
                        'enabled': True
                    }
                }
            }
        else:
            # Hybrid search (default)
            search_params = {
                'collection_name': COLLECTION_NAME,
                'query_text': query,
                'query_filter': query_filter,
                'limit': limit,
                'with_payload': True
            }
            
        # Use the Qdrant query method for search
        results = qdrant.query(**search_params)
        
        # Format results as dictionaries
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": str(result.id),
                "payload": result.metadata,
                "score": result.score
            })
            
        return formatted_results
        
    except Exception as e:
        print(f"Error during search: {e}")
        # Return empty result set on error
        return []

def get_game_recommendations(game_id, limit=6):
    """
    Get game recommendations based on a game ID
    
    Args:
        game_id (str or int): The game ID to get recommendations for
        limit (int): Number of recommendations to return
        
    Returns:
        list: Recommended games
    """
    try:
        # Ensure game_id is the right type
        if isinstance(game_id, str) and game_id.isdigit():
            game_id = int(game_id)
        
        # Get the game by ID first to use its vector for recommendations
        game = qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[game_id],
            with_vectors=True,
            with_payload=True
        )
        
        if not game:
            print(f"Game with ID {game_id} not found")
            return []
        
        # Get the game vectors
        game_point = game[0]
        
        # Get recommendations using vectors
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=(DENSE_VECTOR_NAME, game_point.vector[DENSE_VECTOR_NAME]),
            limit=limit + 1,  # Add 1 to include the game itself
            with_payload=True
        )
        
        # Filter out the game itself and format results
        recommendations = []
        for result in results:
            # Skip the original game
            if str(result.id) == str(game_id):
                continue
                
            recommendations.append({
                "id": str(result.id),
                "payload": result.payload,
                "score": result.score
            })
            
            # Break if we have enough recommendations
            if len(recommendations) >= limit:
                break
                
        return recommendations
    except Exception as e:
        print(f"Recommendation failed: {e}")
        return []

def get_random_games(limit=9, excluded_ids=None):
    """
    Get a selection of truly random games by fetching a larger pool and sampling in memory
    
    Args:
        limit (int): Number of random games to return
        excluded_ids (list): List of game IDs to exclude
        
    Returns:
        list: Random games
    """
    try:
        # Generate a truly unique seed using clock time and system entropy
        unique_seed = int(time.time() * 1000000) ^ int.from_bytes(os.urandom(4), byteorder='little')
        print(f"TRULY UNIQUE SEED: {unique_seed}")
        
        # Use the unique seed
        random.seed(unique_seed)
        
        if not excluded_ids:
            excluded_ids = []
            
        # Convert excluded_ids to strings for consistent comparison
        excluded_ids = [str(id) for id in excluded_ids]
        
        # Get the collection info to know how many points we have
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        total_points = collection_info.points_count
        
        if total_points == 0:
            print("No games in the collection")
            return []
        
        # Fetch a much larger pool of games than needed (up to 200 or half the collection, whichever is smaller)
        fetch_limit = min(200, max(limit * 10, total_points // 2))
        print(f"Fetching {fetch_limit} games for random pool")
        
        # Get a large pool of games without any offset - we'll randomize in memory
        results = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=fetch_limit,
            with_payload=True
        )
        
        pool = results[0]
        print(f"Got {len(pool)} games in random pool")
        
        # Transform to a list for easier manipulation
        all_games = []
        for point in pool:
            # Skip excluded IDs
            if str(point.id) in excluded_ids:
                continue
                
            all_games.append({
                "id": str(point.id),
                "payload": point.payload,
                "score": 1.0  # Default score for random games
            })
        
        print(f"After filtering excluded IDs, pool has {len(all_games)} games")
        
        # Shuffle multiple times for maximum randomness
        for _ in range(3):
            random.shuffle(all_games)
            
        # Take only what we need from the shuffled list
        result_games = all_games[:limit] if len(all_games) >= limit else all_games
        
        # If not enough games, try getting more from a different part of the collection
        if len(result_games) < limit and total_points > fetch_limit:
            print(f"Not enough games in first batch, fetching more...")
            
            # Use a random offset to get a different set of games
            random_offset = random.randint(fetch_limit, total_points - 1)
            more_results = qdrant.scroll(
                collection_name=COLLECTION_NAME,
                limit=fetch_limit,
                with_payload=True,
                offset=random_offset
            )
            
            more_pool = more_results[0]
            print(f"Got {len(more_pool)} additional games")
            
            # Add to our candidates pool, filtering excluded IDs
            for point in more_pool:
                if str(point.id) in excluded_ids:
                    continue
                    
                if not any(game["id"] == str(point.id) for game in result_games):
                    all_games.append({
                        "id": str(point.id),
                        "payload": point.payload,
                        "score": 1.0
                    })
            
            # Shuffle again and take what we need
            random.shuffle(all_games)
            result_games = all_games[:limit] if len(all_games) >= limit else all_games
        
        # Print the IDs we're returning for debugging
        returned_ids = [game["id"] for game in result_games]
        print(f"Returning these random game IDs: {returned_ids}")
        
        # Reset random seed
        random.seed()
        
        return result_games
    except Exception as e:
        print(f"Error getting random games: {e}")
        return []

def get_game_by_id(game_id):
    """
    Get a game by its ID
    
    Args:
        game_id (str or int): The game ID to retrieve
        
    Returns:
        dict or None: The game data or None if not found
    """
    try:
        # Ensure game_id is the right type
        if isinstance(game_id, str) and game_id.isdigit():
            game_id = int(game_id)
            
        # Get the game by ID
        game = qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[game_id],
            with_payload=True
        )
        
        if not game:
            return None
            
        # Format the result
        return {
            "id": str(game[0].id),
            "payload": game[0].payload
        }
    except Exception as e:
        print(f"Error getting game by ID: {e}")
        return None

def test_search():
    """Run a few test searches to verify functionality"""
    test_queries = [
        "open world RPG with dragons",
        "multiplayer shooter with vehicles",
        "relaxing puzzle games"
    ]
    
    for query in test_queries:
        print(f"\nResults for query: '{query}'")
        results = search_games(query, limit=3)
        for i, hit in enumerate(results):
            print(f"{i+1}. {hit.payload.get('name')} (Score: {hit.score:.4f})")
            print(f"   Steam App ID: {hit.id}")
            print(f"   Genres: {hit.payload.get('genres', 'N/A')}")
            print(f"   Price: ${hit.payload.get('price', 'N/A')}")

def initialize_collection(csv_file_path, collection_name=None, force_recreate=False):
    """
    Initialize the Qdrant collection with game data from a CSV file.
    
    Args:
        csv_file_path (str): Path to the CSV file containing game data
        collection_name (str): Name of the collection to create or update
        force_recreate (bool): Whether to force recreation of the collection if it exists
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set the collection name if provided
        global COLLECTION_NAME
        if collection_name:
            COLLECTION_NAME = collection_name
            
        # Set the CSV file path
        global CSV_FILE
        CSV_FILE = csv_file_path
        
        # Check if the collection exists
        try:
            collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
            if collection_info.points_count > 0 and not force_recreate:
                print(f"Collection {COLLECTION_NAME} already has {collection_info.points_count} points.")
                return True
            if force_recreate:
                create_collection()
        except Exception:
            create_collection()
        
        # Upload data
        upload_data_to_qdrant()
        
        return True
    except Exception as e:
        print(f"Error initializing collection: {e}")
        return False

# Add this new function after embedding initialization
def get_dense_embedding(text):
    """Get dense embedding for text using fastembed"""
    try:
        embeddings = list(embedder.embed([text]))
        return embeddings[0].tolist() if embeddings else []
    except Exception as e:
        print(f"Error generating dense embedding: {e}")
        return []

def format_search_results(search_result):
    """Format search results into a consistent dictionary format"""
    results = []
    for point in search_result:
        results.append({
            "id": str(point.id),
            "payload": point.payload if hasattr(point, 'payload') else {},
            "score": point.score
        })
    return results

# Add a helper function to get sparse embeddings
def get_sparse_embedding(text):
    """Get sparse embedding for text using FastEmbed's sparse model integration"""
    try:
        # Use Qdrant client with the specified sparse model
        # This leverages the sparse_model we set earlier with qdrant.set_sparse_model()
        sparse_vector = qdrant.encode_sparse(
            text=text,
            model=SPARSE_MODEL
        )
        
        return sparse_vector.dict
    except Exception as e:
        print(f"Error generating sparse embedding with FastEmbed: {e}")
        # Fallback to simple token frequency approach if the sparse model fails
        tokens = text.lower().split()
        sparse_vector = {}
        for token in tokens:
            if token in sparse_vector:
                sparse_vector[token] += 1.0
            else:
                sparse_vector[token] = 1.0
        return sparse_vector

def get_discovery_games(excluded_ids=None, positive_ids=None, negative_ids=None, limit=9, randomize=None):
    """
    Get games for discovery based on user preferences
    
    Args:
        excluded_ids (list): List of game IDs to exclude (both liked and disliked)
        positive_ids (list): List of game IDs the user liked
        negative_ids (list): List of game IDs the user disliked
        limit (int): Number of games to return
        randomize (int, optional): Random seed to use for consistent randomization
        
    Returns:
        list: Discovered games
    """
    try:
        # Apply random seed if provided
        if randomize is not None:
            # Set a specific seed for reproducible randomness
            old_state = random.getstate()
            random.seed(randomize)
            print(f"Using random seed: {randomize} in get_discovery_games")
            
        if not excluded_ids:
            excluded_ids = []
            
        # If we have positive IDs (liked games), use recommendations
        if positive_ids and len(positive_ids) > 0:
            print(f"Discovery using recommendation with {len(positive_ids)} positive and {len(negative_ids or [])} negative IDs")
            
            # Convert string IDs to integers if needed
            positive_points = [int(id) if isinstance(id, str) and id.isdigit() else id for id in positive_ids]
            
            # Convert negative IDs if provided
            negative_points = []
            if negative_ids and len(negative_ids) > 0:
                negative_points = [int(id) if isinstance(id, str) and id.isdigit() else id for id in negative_ids]
            
            # Use Qdrant's recommend API with the average_vector strategy
            results = qdrant.recommend(
                collection_name=COLLECTION_NAME,
                positive=positive_points,
                negative=negative_points,
                strategy=RecommendStrategy.AVERAGE_VECTOR,
                limit=limit + len(excluded_ids),  # Get extra results to account for excluded IDs
                with_payload=True,
                score_threshold=0.0
            )
            
            # Format and filter results
            formatted_results = []
            for result in results:
                # Skip if in excluded IDs
                if str(result.id) in excluded_ids or result.id in excluded_ids:
                    continue
                    
                formatted_results.append({
                    "id": str(result.id),
                    "payload": result.payload,
                    "score": result.score
                })
                
                # Break if we have enough results
                if len(formatted_results) >= limit:
                    break
                    
            # If we still need more games (not enough recommendations)
            remaining = limit - len(formatted_results)
            if remaining > 0:
                print(f"Not enough recommendations, adding {remaining} random games")
                random_results = get_random_games(limit=remaining * 2, excluded_ids=excluded_ids)
                
                # Add random games up to the limit
                random_count = 0
                for result in random_results:
                    if random_count >= remaining:
                        break
                        
                    # Skip games we already have in recommendations
                    if any(r["id"] == result["id"] for r in formatted_results):
                        continue
                        
                    formatted_results.append(result)
                    random_count += 1
                    
            return formatted_results
            
        # If no positive IDs or negative IDs only, get diverse random games
        print("Discovery using random games (no positive preferences)")
        return get_random_games(limit=limit, excluded_ids=excluded_ids)
            
    except Exception as e:
        print(f"Error in discovery: {e}")
        # Fall back to random games
        return get_random_games(limit=limit, excluded_ids=excluded_ids)
    finally:
        # Reset the random state if we changed it
        if randomize is not None:
            random.setstate(old_state)

def get_discovery_context(game_id, limit=9, excluded_ids=None):
    """
    Get games similar to a specific game (context-based discovery)
    
    Args:
        game_id (str or int): The game ID to get similar games for
        limit (int): Number of similar games to return
        excluded_ids (list): List of game IDs to exclude
        
    Returns:
        list: Similar games
    """
    try:
        if not excluded_ids:
            excluded_ids = []
            
        # Convert excluded IDs to strings
        excluded_ids = [str(id) for id in excluded_ids]
        
        # Convert game_id to the right type
        if isinstance(game_id, str) and game_id.isdigit():
            game_id = int(game_id)
        
        # Get recommendations based on this single game
        recommendations = get_game_recommendations(game_id, limit=limit + len(excluded_ids))
        
        # Filter out excluded IDs
        filtered_recommendations = []
        for game in recommendations:
            if str(game["id"]) not in excluded_ids:
                filtered_recommendations.append(game)
                
            if len(filtered_recommendations) >= limit:
                break
                
        # If we need more games, add random ones
        if len(filtered_recommendations) < limit:
            remaining = limit - len(filtered_recommendations)
            random_games = get_random_games(limit=remaining, excluded_ids=excluded_ids)
            
            # Make sure we don't add duplicates
            existing_ids = [game["id"] for game in filtered_recommendations]
            for game in random_games:
                if game["id"] not in existing_ids:
                    filtered_recommendations.append(game)
                    
                if len(filtered_recommendations) >= limit:
                    break
                    
        return filtered_recommendations
    except Exception as e:
        print(f"Error in context discovery: {e}")
        return get_random_games(limit=limit, excluded_ids=excluded_ids)

# If this file is run directly, perform a test of the discovery API
if __name__ == "__main__":
    # Test the discovery API
    print("Testing Discovery API...")
    
    # Random discovery (no preferences)
    discovery_games = get_discovery_games(limit=3)
    print(f"\nDiscovery (random, no preferences): {len(discovery_games)} games")
    for i, game in enumerate(discovery_games):
        print(f"  {i+1}. {game['payload'].get('name', 'Unknown')}")
    
    # Get the first game ID to use for testing
    if discovery_games:
        test_game_id = discovery_games[0]["id"]
        
        # Test context-based discovery
        context_games = get_discovery_context(test_game_id, limit=3)
        print(f"\nContext discovery based on '{discovery_games[0]['payload'].get('name', 'Unknown')}':")
        for i, game in enumerate(context_games):
            print(f"  {i+1}. {game['payload'].get('name', 'Unknown')}")
        
        # Test recommendation-based discovery
        recommendation_games = get_discovery_games(
            positive_ids=[test_game_id], 
            negative_ids=None, 
            limit=3
        )
        print(f"\nRecommendation-based discovery (positive: {test_game_id}):")
        for i, game in enumerate(recommendation_games):
            print(f"  {i+1}. {game['payload'].get('name', 'Unknown')}") 