import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVectorParams, SparseIndexParams, SparseVector
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
from typing import List, Dict, Optional
import math

load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_with_sparse_dense")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
CSV_FILE = os.getenv("CSV_FILE", "jan-25-released-games copy.csv")

# Define methods to monkey-patch onto QdrantClient
def set_model(self, model_name):
    """Set the dense embedding model"""
    self._model_name = model_name
    
def set_sparse_model(self, model_name):
    """Set the sparse embedding model"""
    self._sparse_model_name = model_name

def get_fastembed_vector_params(self):
    """Return named VectorParams for fastembed"""
    return {
        "fast-bge-small-en": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    }

def get_fastembed_sparse_vector_params(self):
    """Return named SparseVectorParams for fastembed"""
    return {
        "fast-sparse-splade_pp_en_v1": SparseVectorParams(index=SparseIndexParams())
    }

# Monkey-patch methods onto the QdrantClient class
QdrantClient.set_model = set_model
QdrantClient.set_sparse_model = set_sparse_model
QdrantClient.get_fastembed_vector_params = get_fastembed_vector_params
QdrantClient.get_fastembed_sparse_vector_params = get_fastembed_sparse_vector_params

# Connect to Qdrant
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Set the models for dense and sparse embeddings
qdrant.set_model(EMBEDDING_MODEL)
qdrant.set_sparse_model(SPARSE_MODEL)

# We'll still use TextEmbedding for flexibility in generating dense vectors directly
embedder = TextEmbedding(model_name=EMBEDDING_MODEL, max_length=512, cache_dir="./.embeddings_cache")

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

def search_games(
    query_text: str, 
    offset: int = 0, 
    limit: int = 10, 
    use_hybrid: bool = True,
    query_filter: Optional[Dict] = None,
    with_payload: bool = True,
) -> Dict:
    """
    Searches for games based on a text query.
    
    Parameters:
    - query_text: Text query to search for
    - offset: Number of items to skip
    - limit: Maximum number of items to return
    - use_hybrid: Whether to use hybrid search (both dense and sparse vectors)
    - query_filter: Filter to apply to the search
    - with_payload: Whether to return the payload
    
    Returns:
    - Dictionary with search results
    """
    try:
        # Get the embedding for the query text
        print(f"Generating embeddings for query: '{query_text}'")
        vector = get_dense_embedding(query_text)
        print(f"Generated dense vector with {len(vector)} dimensions")
        
        # Default to using only dense vectors
        search_result = None
        
        try:
            if use_hybrid:
                # Try hybrid search first (combining dense and sparse vectors)
                print(f"Attempting hybrid search with query: '{query_text}'")
                
                # Get sparse vector using FastEmbed integration
                sparse_vector = get_sparse_embedding(query_text)
                sparse_keys = list(sparse_vector.keys())
                print(f"Generated sparse vector with {len(sparse_keys)} tokens. Sample tokens: {sparse_keys[:5] if len(sparse_keys) > 5 else sparse_keys}")
                
                # For hybrid search, we need to use the correct vector names from our collection
                print(f"Using collection: {COLLECTION_NAME}")
                print(f"Vector names: dense='fast-bge-small-en', sparse='fast-sparse-splade_pp_en_v1'")
                
                # Log the API request we're about to make for debugging
                search_result = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_vector={
                        "fast-bge-small-en": vector,  # Dense vector with the correct name
                    },
                    query_sparse_vector={
                        "fast-sparse-splade_pp_en_v1": sparse_vector  # Sparse vector with correct name
                    },
                    limit=limit,
                    offset=offset,
                    with_payload=with_payload,
                )
                print(f"Hybrid search returned {len(search_result)} results")
            else:
                # If hybrid is not requested, use just the dense vector
                print(f"Using dense vector search with query: '{query_text}'")
                search_result = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=("fast-bge-small-en", vector),  # Named dense vector
                    limit=limit,
                    offset=offset,
                    with_payload=with_payload,
                )
                print(f"Dense search returned {len(search_result)} results")
            
            # Format the results
            items = format_search_results(search_result)
            
            # Return the formatted results
            return {
                "items": items,
                "total": len(items),
                "page": offset // limit + 1 if limit > 0 else 1,
                "page_size": limit,
                "pages": math.ceil(len(items) / limit) if limit > 0 else 0,
            }
        except Exception as e:
            print(f"Named vector search failed: {e}")
            try:
                # Fall back to direct vector search as last resort
                print(f"Falling back to direct vector search")
                search_result = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=vector,  # Direct vector fallback
                    limit=limit,
                    offset=offset,
                    with_payload=with_payload,
                )
                print(f"Direct vector search returned {len(search_result)} results")
                
                items = format_search_results(search_result)
                
                return {
                    "items": items,
                    "total": len(items),
                    "page": offset // limit + 1 if limit > 0 else 1,
                    "page_size": limit,
                    "pages": math.ceil(len(items) / limit) if limit > 0 else 0,
                }
            except Exception as e2:
                print(f"Direct vector search failed too: {e2}")
                # If all search methods fail, try getting random games as fallback
                print(f"Search failed, falling back to random games")
                random_results = get_random_games(limit=limit)
                print(f"Returning {len(random_results)} random games as fallback")
                
                return {
                    "items": random_results,
                    "total": len(random_results),
                    "page": 1,
                    "page_size": limit,
                    "pages": 1,
                }
            
    except Exception as e:
        print(f"Error in search_games: {e}")
        return {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": limit,
            "pages": 0,
        }

def get_game_recommendations(game_id, limit=5):
    """
    Get game recommendations based on a given game ID.
    
    Args:
        game_id (int): The Steam App ID of the game
        limit (int): Number of recommendations to return
        
    Returns:
        list: Recommended games as dictionaries with id, payload, and score
    """
    try:
        # Try with named vector (matching collection config)
        recommend_results = qdrant.recommend(
            collection_name=COLLECTION_NAME,
            positive=[game_id],
            using="fast-bge-small-en",  # Specify which vector to use for recommendations
            limit=limit,
            with_payload=True
        )
        
        # Convert to dictionaries for consistent format
        results = []
        for point in recommend_results:
            results.append({
                "id": str(point.id),
                "payload": point.payload if hasattr(point, 'payload') else {},
                "score": point.score
            })
        
        return results
    except Exception as e:
        print(f"Named vector recommendation failed: {e}")
        try:
            # Fallback to direct vector recommendation
            recommend_results = qdrant.recommend(
                collection_name=COLLECTION_NAME,
                positive=[game_id],
                limit=limit,
                with_payload=True
            )
            
            results = []
            for point in recommend_results:
                results.append({
                    "id": str(point.id),
                    "payload": point.payload if hasattr(point, 'payload') else {},
                    "score": point.score
                })
            
            return results
        except Exception as e2:
            print(f"Direct recommendation failed too: {e2}")
            # Fallback to random games if all recommendation methods fail
            try:
                return get_random_games(limit)
            except:
                return []

def get_enhanced_recommendations(positive_ids=None, negative_ids=None, query=None, limit=5):
    """
    Get enhanced recommendations based on combinations of:
    - games the user likes (positive_ids)
    - games the user dislikes (negative_ids)
    - a text query for additional context
    
    Args:
        positive_ids (list): List of game IDs that the user likes
        negative_ids (list): List of game IDs that the user dislikes
        query (str): Optional text query for additional context
        limit (int): Maximum number of recommendations to return
        
    Returns:
        list: List of recommended games
    """
    if not positive_ids and not negative_ids and not query:
        return get_random_games(limit)
    
    # Initialize weights for combining the recommendations
    positive_weight = 1.0
    negative_weight = -1.0
    query_weight = 0.5
    total_weight = 0.0
    
    # Combine all recommendations
    combined_results = {}
    
    # Process positive IDs (games the user likes)
    if positive_ids and len(positive_ids) > 0:
        total_weight += positive_weight
        for game_id in positive_ids:
            try:
                similar_games = search_games(game_id, limit=limit*3)
                for game in similar_games:
                    game_id = game["id"]
                    if game_id in positive_ids or game_id in (negative_ids or []):
                        continue  # Skip games that are in the input lists
                        
                    if game_id not in combined_results:
                        combined_results[game_id] = {
                            "id": game_id,
                            "payload": game.get("payload", {}),
                            "score": 0
                        }
                    combined_results[game_id]["score"] += (game.get("score", 0) * positive_weight)
            except Exception as e:
                print(f"Error getting recommendations for positive ID {game_id}: {e}")
    
    # Process negative IDs (games the user dislikes)
    if negative_ids and len(negative_ids) > 0:
        total_weight += abs(negative_weight)
        for game_id in negative_ids:
            try:
                similar_games = search_games(game_id, limit=limit*3)
                for game in similar_games:
                    game_id = game["id"]
                    if game_id in positive_ids or game_id in (negative_ids or []):
                        continue  # Skip games that are in the input lists
                        
                    if game_id not in combined_results:
                        combined_results[game_id] = {
                            "id": game_id,
                            "payload": game.get("payload", {}),
                            "score": 0
                        }
                    combined_results[game_id]["score"] += (game.get("score", 0) * negative_weight)
            except Exception as e:
                print(f"Error getting recommendations for negative ID {game_id}: {e}")
    
    # Process text query
    if query:
        total_weight += query_weight
        try:
            query_results = search_games(query, limit=limit*3)
            for game in query_results:
                game_id = game["id"]
                if game_id in positive_ids or game_id in (negative_ids or []):
                    continue  # Skip games that are in the input lists
                    
                if game_id not in combined_results:
                    combined_results[game_id] = {
                        "id": game_id,
                        "payload": game.get("payload", {}),
                        "score": 0
                    }
                combined_results[game_id]["score"] += (game.get("score", 0) * query_weight)
        except Exception as e:
            print(f"Error searching for query '{query}': {e}")
    
    # Normalize scores
    if total_weight > 0:
        for game_id in combined_results:
            combined_results[game_id]["score"] /= total_weight
    
    # Sort by score and limit results
    results = list(combined_results.values())
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def get_discovery_recommendations(liked_ids=None, disliked_ids=None, limit=5):
    """
    Get discovery recommendations based on user feedback.
    
    If no feedback (liked_ids, disliked_ids) is provided, returns random games.
    If feedback is provided, returns recommendations based on the feedback.
    
    Args:
        liked_ids (list): List of game IDs that the user likes
        disliked_ids (list): List of game IDs that the user dislikes
        limit (int): Maximum number of recommendations to return
        
    Returns:
        list: List of recommended games
    """
    if not liked_ids and not disliked_ids:
        return get_random_games(limit)
    
    # Use the enhanced recommendations system with only positive and negative IDs
    return get_enhanced_recommendations(
        positive_ids=liked_ids,
        negative_ids=disliked_ids,
        limit=limit
    )

def get_diverse_recommendations(seed_id, diversity_factor=0.5, limit=5):
    """
    Get diverse recommendations based on a seed game ID.
    
    Args:
        seed_id (str): The game ID to base recommendations on
        diversity_factor (float): A value between 0 and 1 that determines how diverse the results should be.
                                 0 means similar to seed, 1 means maximally diverse.
        limit (int): Maximum number of recommendations to return
        
    Returns:
        list: List of recommended games
    """
    if diversity_factor < 0:
        diversity_factor = 0
    elif diversity_factor > 1:
        diversity_factor = 1
    
    # First, get similar games to the seed
    similar_games = search_games(seed_id, limit=limit*3)
    
    if not similar_games or len(similar_games) == 0:
        return []
    
    # If diversity factor is 0, just return the similar games
    if diversity_factor == 0:
        return similar_games[:limit]
    
    # If diversity factor is 1, return random games
    if diversity_factor == 1:
        return get_random_games(limit)
    
    # Create a set of game IDs to track what we've selected
    selected_ids = set([seed_id])
    results = []
    
    # Add the most similar game first
    if similar_games:
        first_game = similar_games[0]
        results.append(first_game)
        selected_ids.add(first_game["id"])
    
    # Select remaining games by balancing similarity and diversity
    remaining_candidates = [g for g in similar_games if g["id"] not in selected_ids]
    
    while len(results) < limit and remaining_candidates:
        best_game = None
        best_score = -float("inf")
        
        for game in remaining_candidates:
            # Calculate base similarity score (higher is better)
            similarity_score = game.get("score", 0)
            
            # Calculate diversity score (higher means more diverse)
            diversity_score = 0
            for selected_game in results:
                # A simple diversity measure - the more different from existing selections, the better
                # This is a placeholder - in a real system, you might use vector distance or genre difference
                if game["id"] != selected_game["id"]:
                    # Ensure we don't get KeyError if score isn't present
                    diversity_score += 1 - (selected_game.get("score", 0) * similarity_score)
            
            # Normalize diversity score
            if len(results) > 0:
                diversity_score /= len(results)
            
            # Combine scores based on diversity_factor
            combined_score = (1 - diversity_factor) * similarity_score + diversity_factor * diversity_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_game = game
        
        if best_game:
            results.append(best_game)
            selected_ids.add(best_game["id"])
            remaining_candidates = [g for g in remaining_candidates if g["id"] not in selected_ids]
        else:
            break
    
    return results

def get_random_games(limit: int = 10) -> List[Dict]:
    """
    Get a list of random games from the collection.
    
    Parameters:
        limit (int): Number of games to return.
        
    Returns:
        List[Dict]: List of dictionaries with game information in the format {id, score, payload}.
    """
    try:
        # Use Qdrant's scroll method to get random games
        results = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        # The scroll method returns a tuple of (points, next_page_offset)
        points, _ = results
        
        # Format the results to match our standard return format
        formatted_results = []
        for point in points:
            formatted_results.append({
                "id": str(point.id),
                "score": 1.0,  # Assign a score of 1.0 for random retrieval
                "payload": point.payload
            })
        
        return formatted_results
    except Exception as e:
        print(f"Error getting random games: {e}")
        return []

def get_game_by_id(game_id: str) -> Optional[Dict]:
    """
    Get detailed information about a specific game by ID.
    
    Parameters:
        game_id (str): The Steam App ID of the game to retrieve.
        
    Returns:
        Optional[Dict]: Dictionary with game information or None if not found.
    """
    try:
        # Convert to string to ensure proper ID format
        str_id = str(game_id)
        
        # First try direct retrieval by ID
        result = qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[str_id],
            with_payload=True,
            with_vectors=False
        )
        
        # Check if we got a result
        if result and len(result) > 0:
            point = result[0]
            return {
                "id": str(point.id),
                "score": 1.0,
                "payload": point.payload
            }
        
        # If direct retrieval failed, try searching by filter
        results = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            filter={
                "must": [
                    {"key": "id", "match": {"value": str_id}}
                ]
            },
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        # Check if we got a result from filter search
        points, _ = results
        if points and len(points) > 0:
            point = points[0]
            return {
                "id": str(point.id),
                "score": 1.0,
                "payload": point.payload
            }
        
        return None
    except Exception as e:
        print(f"Error getting game by ID {game_id}: {e}")
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

if __name__ == "__main__":
    # Check if collection exists and create/upload if needed
    try:
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        print(f"Collection {COLLECTION_NAME} exists with {collection_info.points_count} points.")
        if collection_info.points_count == 0:
            upload_data_to_qdrant()
    except Exception:
        print(f"Collection {COLLECTION_NAME} doesn't exist yet. Creating and uploading data...")
        create_collection()
        upload_data_to_qdrant()
    
    # Run a test search
    test_search() 