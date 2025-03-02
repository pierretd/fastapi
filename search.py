import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, PointStruct
from fastembed import TextEmbedding
import os
from dotenv import load_dotenv
import logging
import numpy as np
import asyncio
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
CSV_FILE = os.getenv("CSV_FILE", "games_data.csv")

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
    
    # Combine fields with more weight on name and genres
    text = f"{name} {name} {genres} {genres} {tags} {description}"
    return text

def check_collection_exists():
    """
    Check if the Qdrant collection exists.
    
    Returns:
        bool: True if collection exists, False otherwise
    """
    try:
        collections = qdrant.get_collections().collections
        collection_names = [collection.name for collection in collections]
        return COLLECTION_NAME in collection_names
    except Exception as e:
        logger.error(f"Error checking collection: {str(e)}")
        return False

async def initialize_collection():
    """
    Initialize the Qdrant collection with data if it doesn't exist.
    """
    try:
        logger.info("Checking if collection exists...")
        if not check_collection_exists():
            logger.info(f"Collection {COLLECTION_NAME} doesn't exist. Please upload data.")
        else:
            logger.info(f"Collection {COLLECTION_NAME} exists.")
    except Exception as e:
        logger.error(f"Error initializing collection: {str(e)}")

def get_game_by_id(game_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a game by its ID.
    
    Args:
        game_id: The unique identifier of the game
        
    Returns:
        Dict containing game details or None if not found
    """
    try:
        # Create filter to find the game by ID
        filter_by_id = Filter(
            must=[
                Filter(
                    field="steam_appid",
                    match={"value": game_id}
                )
            ]
        )
        
        # Search for the game
        search_result = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            filter=filter_by_id,
            limit=1
        )
        
        # Get the first (and only) result if any
        if search_result and search_result[0]:
            points = search_result[0]
            if len(points) > 0:
                # Return the game data
                return points[0].payload
                
        return None
    except Exception as e:
        logger.error(f"Error getting game by ID: {str(e)}")
        return None

def get_discovery_games(
    positive_ids: List[str] = [],
    negative_ids: List[str] = [],
    excluded_ids: List[str] = [],
    limit: int = 9
) -> List[Dict[str, Any]]:
    """
    Get personalized game recommendations based on likes/dislikes.
    
    Args:
        positive_ids: List of game IDs the user likes
        negative_ids: List of game IDs the user dislikes
        excluded_ids: List of game IDs to exclude from results
        limit: Maximum number of results to return
        
    Returns:
        List of recommended games
    """
    try:
        # If no positive IDs, return empty list
        if not positive_ids:
            return []
        
        # Get the positive game vectors
        positive_games = []
        for game_id in positive_ids:
            game = get_game_by_id(game_id)
            if game:
                positive_games.append(game)
        
        # Get the negative game vectors
        negative_games = []
        for game_id in negative_ids:
            game = get_game_by_id(game_id)
            if game:
                negative_games.append(game)
        
        # Prepare positive and negative texts for embedding
        positive_texts = []
        for game in positive_games:
            text = f"{game.get('name', '')} {game.get('genres', '')} {game.get('tags', '')} {game.get('short_description', '')}"
            positive_texts.append(text)
        
        negative_texts = []
        for game in negative_games:
            text = f"{game.get('name', '')} {game.get('genres', '')} {game.get('tags', '')} {game.get('short_description', '')}"
            negative_texts.append(text)
        
        # Get embeddings
        positive_embeddings = list(embedder.embed(positive_texts)) if positive_texts else []
        negative_embeddings = list(embedder.embed(negative_texts)) if negative_texts else []
        
        if not positive_embeddings:
            return []
        
        # Combine positive embeddings and subtract negative embeddings
        query_vector = np.zeros_like(positive_embeddings[0])
        for embedding in positive_embeddings:
            query_vector += embedding
        
        for embedding in negative_embeddings:
            query_vector -= embedding
        
        # Normalize the query vector
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # Prepare filter to exclude specific game IDs
        exclude_filter = None
        if excluded_ids:
            exclude_filter = Filter(
                must_not=[
                    Filter(
                        field="steam_appid",
                        match={"value": game_id}
                    )
                    for game_id in excluded_ids + positive_ids + negative_ids
                ]
            )
        
        # Search for similar games
        search_result = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector.tolist(),
            limit=limit,
            filter=exclude_filter
        )
        
        # Extract game data from search results
        games = []
        for point in search_result:
            game_data = point.payload
            game_data["score"] = point.score
            games.append(game_data)
        
        return games
    except Exception as e:
        logger.error(f"Error in discovery games: {str(e)}")
        return []

def get_discovery_context(
    game_id: str,
    limit: int = 9,
    excluded_ids: List[str] = []
) -> List[Dict[str, Any]]:
    """
    Get games similar to a specific game.
    
    Args:
        game_id: ID of the game to find similar games for
        limit: Maximum number of results to return
        excluded_ids: List of game IDs to exclude from results
        
    Returns:
        List of similar games
    """
    try:
        # Get the source game
        source_game = get_game_by_id(game_id)
        if not source_game:
            return []
        
        # Prepare text for embedding
        text = f"{source_game.get('name', '')} {source_game.get('genres', '')} {source_game.get('tags', '')} {source_game.get('short_description', '')}"
        
        # Get embedding for the text
        embeddings = list(embedder.embed([text]))
        if not embeddings:
            return []
        
        query_vector = embeddings[0]
        
        # Prepare filter to exclude specific game IDs
        exclude_filter = None
        if excluded_ids or game_id:
            exclude_filter = Filter(
                must_not=[
                    Filter(
                        field="steam_appid",
                        match={"value": id}
                    )
                    for id in excluded_ids + [game_id]
                ]
            )
        
        # Search for similar games
        search_result = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector.tolist(),
            limit=limit,
            filter=exclude_filter
        )
        
        # Extract game data from search results
        games = []
        for point in search_result:
            game_data = point.payload
            game_data["score"] = point.score
            games.append(game_data)
        
        return games
    except Exception as e:
        logger.error(f"Error in discovery context: {str(e)}")
        return [] 