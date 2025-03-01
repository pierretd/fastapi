import sys
import os
# Get the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import directly from the search.py file
from .search import (
    initialize_collection,
    search_games,
    get_game_recommendations,
    get_enhanced_recommendations,
    get_discovery_recommendations,
    get_diverse_recommendations,
    get_random_games,
    get_game_by_id,
    get_steam_game_description,
    clean_html_description
)

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
    "clean_html_description"
] 