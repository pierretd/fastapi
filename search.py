import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter
from fastembed import TextEmbedding
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional, Any
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables and suppress warnings
load_dotenv()

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))

# Connect to Qdrant
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Initialize embedder for dense vector search
embedder = TextEmbedding(EMBEDDING_MODEL)

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

def initialize_collection():
    """
    Initialize the vector search collection.
    Check if the collection exists, and if not, create it.
    
    This doesn't upload any data - that's handled by the upload_data.py script.
    """
    # Check if collection exists
    collections = qdrant.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if COLLECTION_NAME in collection_names:
        logger.info(f"Collection {COLLECTION_NAME} already exists")
        return
    
    # Collection doesn't exist, create it
    logger.info(f"Creating collection {COLLECTION_NAME}")
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    logger.info(f"Collection {COLLECTION_NAME} created successfully")

def search_games(query: str, limit: int = 10, offset: int = 0):
    """
    Search for games using a text query.
    
    Args:
        query: Search query text
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        List of game objects with their scores and payloads
    """
    # Generate embedding for the query
    query_embedding = list(embedder.embed(query))[0]
    
    # Perform vector search
    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=limit + offset
    )
    
    # Apply offset
    if offset > 0:
        search_result = search_result[offset:]
    
    # Format results
    formatted_results = []
    for result in search_result:
        formatted_results.append({
            "id": result.id,
            "score": result.score,
            "payload": result.payload
        })
    
    return formatted_results

def get_game_by_id(game_id: str):
    """
    Get a game by its ID.
    
    Args:
        game_id: The game ID to look up
        
    Returns:
        Game payload or None if not found
    """
    try:
        # Try to retrieve the point by ID
        points = qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[game_id]
        )
        
        if points and len(points) > 0:
            return points[0].payload
        return None
    except Exception as e:
        logger.error(f"Error retrieving game by ID: {e}")
        return None

def get_discovery_context(game_id: str, limit: int = 9, excluded_ids: List[str] = None):
    """
    Get games similar to a specific game.
    
    Args:
        game_id: ID of the game to find similar games for
        limit: Maximum number of results to return
        excluded_ids: List of game IDs to exclude from results
        
    Returns:
        List of similar games
    """
    if excluded_ids is None:
        excluded_ids = []
    
    # Always exclude the source game from results
    if game_id not in excluded_ids:
        excluded_ids.append(game_id)
    
    try:
        # Get the source game's vector
        points = qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[game_id],
            with_vectors=True
        )
        
        if not points:
            logger.error(f"Game with ID {game_id} not found")
            return []
        
        # Use the vector to find similar games
        source_vector = points[0].vector
        
        # Prepare filter to exclude specified IDs
        must_not = [{"id": {"in": excluded_ids}}] if excluded_ids else []
        search_filter = Filter(must_not=must_not) if must_not else None
        
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=source_vector,
            limit=limit,
            filter=search_filter
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error in get_discovery_context: {e}")
        return [] 