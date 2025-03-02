import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Try to import required functions, with clear error handling
try:
    from .search import (
        initialize_collection,
        search_games,
        get_game_recommendations,
        get_enhanced_recommendations,
        get_discovery_recommendations,
        get_diverse_recommendations,
        get_random_games,
        get_game_by_id,
        get_discovery_context
    )
    
    # Optional imports that might be used in search.py
    try:
        from .search import (
            get_steam_game_description,
            clean_html_description
        )
    except ImportError:
        logger.warning("Some optional search functions couldn't be imported")
        
except ImportError as e:
    logger.error(f"Error importing search functionality: {e}")
    
    # Define fallback functions
    def initialize_collection():
        logger.error("Search functionality not available - initialize_collection is a placeholder")
        return
    
    def search_games(query, limit=10, offset=0):
        logger.error("Search functionality not available - search_games is a placeholder")
        return []
    
    def get_game_by_id(game_id):
        logger.error("Search functionality not available - get_game_by_id is a placeholder")
        return None
    
    def get_discovery_context(game_id, limit=9, excluded_ids=None):
        logger.error("Search functionality not available - get_discovery_context is a placeholder")
        return []
        
    def get_steam_game_description(app_id):
        logger.error("Search functionality not available - get_steam_game_description is a placeholder")
        return ""
    
    def clean_html_description(html_text):
        logger.error("Search functionality not available - clean_html_description is a placeholder")
        return ""

# Also expose these directly
__all__ = [
    "initialize_collection",
    "search_games",
    "get_game_recommendations",
    "get_enhanced_recommendations",
    "get_discovery_recommendations",
    "get_diverse_recommendations",
    "get_random_games",
    "get_game_by_id",
    "get_steam_game_description",
    "clean_html_description",
    "get_discovery_context"
] 