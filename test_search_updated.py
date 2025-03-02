#!/usr/bin/env python
"""
Test the updated search.py functionality
This script tests all the search functions to ensure they work correctly with hybrid search
"""
import os
import sys
from dotenv import load_dotenv
import importlib.util

# Load environment variables
load_dotenv()

# Directly import the search.py file
search_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search.py")
spec = importlib.util.spec_from_file_location("search_module", search_path)
search_module = importlib.util.module_from_spec(spec)
sys.modules["search_module"] = search_module
spec.loader.exec_module(search_module)

def test_search():
    """Test the search_games function with various queries"""
    print("\n===== TESTING SEARCH FUNCTIONALITY =====")
    
    # Test basic search
    query = "adventure game with puzzles"
    print(f"\nBasic search: '{query}'")
    try:
        results = search_module.search_games(query=query, page_size=3, use_hybrid=True)
        
        if results:
            print(f"Found {len(results)} results")
            for i, item in enumerate(results):
                # Check if the result is a dictionary or an object
                if isinstance(item, dict):
                    name = item.get('payload', {}).get('name', 'Unknown')
                    score = item.get('score', 0)
                else:
                    # Try to access attributes directly
                    try:
                        name = item.payload.get('name', 'Unknown') if hasattr(item, 'payload') else 'Unknown'
                        score = item.score if hasattr(item, 'score') else 0
                    except:
                        print(f"  {i+1}. Result format not recognized: {type(item)}")
                        continue
                
                print(f"  {i+1}. {name} (score: {score:.4f})")
                # Print description if available
                if isinstance(item, dict):
                    desc = item.get('payload', {}).get('short_description', '')
                else:
                    try:
                        desc = item.payload.get('short_description', '') if hasattr(item, 'payload') else ''
                    except:
                        desc = ''
                
                if desc:
                    print(f"     {desc[:100]}...")
        else:
            print("No results found or invalid response structure")
    except Exception as e:
        print(f"Error in search: {e}")

    # Test empty query (should return random games)
    print("\nEmpty query (random games):")
    try:
        random_results = search_module.search_games(query="", page_size=3, use_hybrid=True)
        
        if random_results:
            print(f"Found {len(random_results)} random games")
            for i, item in enumerate(random_results):
                # Check if the result is a dictionary or an object
                if isinstance(item, dict):
                    name = item.get('payload', {}).get('name', 'Unknown')
                else:
                    # Try to access attributes directly
                    try:
                        name = item.payload.get('name', 'Unknown') if hasattr(item, 'payload') else 'Unknown'
                    except:
                        print(f"  {i+1}. Result format not recognized: {type(item)}")
                        continue
                
                print(f"  {i+1}. {name}")
        else:
            print("No random games found or invalid response structure")
    except Exception as e:
        print(f"Error in random search: {e}")

def test_recommendations():
    """Test the get_game_recommendations function"""
    print("\n===== TESTING RECOMMENDATIONS FUNCTIONALITY =====")
    
    try:
        # Get a random game first to use for recommendations
        random_games = search_module.get_random_games(limit=1)
        
        if not random_games:
            print("Could not get a random game for testing recommendations")
            return
        
        game = random_games[0]
        # Handle different result formats
        if isinstance(game, dict):
            game_id = game.get('id')
            game_name = game.get('payload', {}).get('name', 'Unknown')
        else:
            try:
                game_id = game.id if hasattr(game, 'id') else None
                game_name = game.payload.get('name', 'Unknown') if hasattr(game, 'payload') else 'Unknown'
            except:
                print(f"Result format not recognized: {type(game)}")
                return
        
        print(f"\nGetting recommendations based on: {game_name} (ID: {game_id})")
        recommendations = search_module.get_game_recommendations(game_id, limit=3)
        
        if recommendations:
            print(f"Found {len(recommendations)} recommendations")
            for i, item in enumerate(recommendations):
                # Handle different result formats
                if isinstance(item, dict):
                    name = item.get('payload', {}).get('name', 'Unknown')
                    score = item.get('score', 0)
                else:
                    try:
                        name = item.payload.get('name', 'Unknown') if hasattr(item, 'payload') else 'Unknown'
                        score = item.score if hasattr(item, 'score') else 0
                    except:
                        print(f"  {i+1}. Result format not recognized: {type(item)}")
                        continue
                
                print(f"  {i+1}. {name} (similarity: {score:.4f})")
        else:
            print("No recommendations found or invalid response structure")
    except Exception as e:
        print(f"Error in recommendations: {e}")

def test_random_games():
    """Test the get_random_games function"""
    print("\n===== TESTING RANDOM GAMES FUNCTIONALITY =====")
    
    try:
        random_games = search_module.get_random_games(limit=3)
        
        if random_games:
            print(f"Found {len(random_games)} random games")
            for i, item in enumerate(random_games):
                # Handle different result formats
                if isinstance(item, dict):
                    name = item.get('payload', {}).get('name', 'Unknown')
                else:
                    try:
                        name = item.payload.get('name', 'Unknown') if hasattr(item, 'payload') else 'Unknown'
                    except:
                        print(f"  {i+1}. Result format not recognized: {type(item)}")
                        continue
                
                print(f"  {i+1}. {name}")
        else:
            print("No random games found or invalid response structure")
    except Exception as e:
        print(f"Error in random games: {e}")

def test_game_by_id():
    """Test the get_game_by_id function"""
    print("\n===== TESTING GAME BY ID FUNCTIONALITY =====")
    
    try:
        # Get a random game first to use for ID lookup
        random_games = search_module.get_random_games(limit=1)
        
        if not random_games:
            print("Could not get a random game for testing game by ID")
            return
        
        game = random_games[0]
        # Handle different result formats
        if isinstance(game, dict):
            game_id = game.get('id')
            game_name = game.get('payload', {}).get('name', 'Unknown')
        else:
            try:
                game_id = game.id if hasattr(game, 'id') else None
                game_name = game.payload.get('name', 'Unknown') if hasattr(game, 'payload') else 'Unknown'
            except:
                print(f"Result format not recognized: {type(game)}")
                return
        
        print(f"\nLooking up game by ID: {game_name} (ID: {game_id})")
        game_details = search_module.get_game_by_id(game_id)
        
        if game_details:
            # Handle different result formats
            if isinstance(game_details, dict):
                name = game_details.get('payload', {}).get('name', 'Unknown')
                desc = game_details.get('payload', {}).get('short_description', '')
            else:
                try:
                    name = game_details.payload.get('name', 'Unknown') if hasattr(game_details, 'payload') else 'Unknown'
                    desc = game_details.payload.get('short_description', '') if hasattr(game_details, 'payload') else ''
                except:
                    print(f"Result format not recognized: {type(game_details)}")
                    return
            
            print(f"Successfully retrieved game details:")
            print(f"  Name: {name}")
            if desc:
                print(f"  Description: {desc[:100]}...")
        else:
            print(f"Could not find game with ID: {game_id}")
    except Exception as e:
        print(f"Error in game by ID: {e}")

def test_discovery():
    """Test the discovery functionality"""
    print("\n===== TESTING DISCOVERY FUNCTIONALITY =====")
    
    try:
        # 1. Get initial set of games (no preferences)
        print("\nGetting initial discovery games (no preferences):")
        initial_games = search_module.get_discovery_games(limit=3)
        
        if not initial_games or len(initial_games) == 0:
            print("Could not get initial discovery games")
            return
        
        print(f"Found {len(initial_games)} discovery games")
        for i, game in enumerate(initial_games):
            # Handle different result formats
            if isinstance(game, dict):
                name = game.get('payload', {}).get('name', 'Unknown')
            else:
                try:
                    name = game.payload.get('name', 'Unknown') if hasattr(game, 'payload') else 'Unknown'
                except:
                    print(f"  {i+1}. Result format not recognized: {type(game)}")
                    continue
            
            print(f"  {i+1}. {name}")
        
        # 2. Test with a liked game (positive preference)
        # Handle different result formats
        if isinstance(initial_games[0], dict):
            liked_game_id = initial_games[0].get('id')
            liked_game_name = initial_games[0].get('payload', {}).get('name', 'Unknown')
        else:
            try:
                liked_game_id = initial_games[0].id if hasattr(initial_games[0], 'id') else None
                liked_game_name = initial_games[0].payload.get('name', 'Unknown') if hasattr(initial_games[0], 'payload') else 'Unknown'
            except:
                print(f"Result format not recognized: {type(initial_games[0])}")
                return
        
        print(f"\nGetting discovery games with liked game: {liked_game_name} (ID: {liked_game_id})")
        discovery_with_liked = search_module.get_discovery_games(
            positive_ids=[liked_game_id], 
            excluded_ids=[liked_game_id],  # Exclude the liked game from results
            limit=3
        )
        
        if discovery_with_liked:
            print(f"Found {len(discovery_with_liked)} discovery games based on liked game")
            for i, game in enumerate(discovery_with_liked):
                # Handle different result formats
                if isinstance(game, dict):
                    name = game.get('payload', {}).get('name', 'Unknown')
                    score = game.get('score', 0)
                else:
                    try:
                        name = game.payload.get('name', 'Unknown') if hasattr(game, 'payload') else 'Unknown'
                        score = game.score if hasattr(game, 'score') else 0
                    except:
                        print(f"  {i+1}. Result format not recognized: {type(game)}")
                        continue
                
                print(f"  {i+1}. {name} (score: {score:.4f})")
        else:
            print("No discovery games found based on liked game")
        
        # 3. Test with both liked and disliked games (if we have enough initial games)
        if len(initial_games) >= 2:
            # Handle different result formats
            if isinstance(initial_games[1], dict):
                disliked_game_id = initial_games[1].get('id')
                disliked_game_name = initial_games[1].get('payload', {}).get('name', 'Unknown')
            else:
                try:
                    disliked_game_id = initial_games[1].id if hasattr(initial_games[1], 'id') else None
                    disliked_game_name = initial_games[1].payload.get('name', 'Unknown') if hasattr(initial_games[1], 'payload') else 'Unknown'
                except:
                    print(f"Result format not recognized: {type(initial_games[1])}")
                    return
            
            print(f"\nGetting discovery games with liked game: {liked_game_name} and disliked game: {disliked_game_name}")
            discovery_with_preferences = search_module.get_discovery_games(
                positive_ids=[liked_game_id],
                negative_ids=[disliked_game_id],
                excluded_ids=[liked_game_id, disliked_game_id],
                limit=3
            )
            
            if discovery_with_preferences:
                print(f"Found {len(discovery_with_preferences)} discovery games based on preferences")
                for i, game in enumerate(discovery_with_preferences):
                    # Handle different result formats
                    if isinstance(game, dict):
                        name = game.get('payload', {}).get('name', 'Unknown')
                        score = game.get('score', 0)
                    else:
                        try:
                            name = game.payload.get('name', 'Unknown') if hasattr(game, 'payload') else 'Unknown'
                            score = game.score if hasattr(game, 'score') else 0
                        except:
                            print(f"  {i+1}. Result format not recognized: {type(game)}")
                            continue
                    
                    print(f"  {i+1}. {name} (score: {score:.4f})")
            else:
                print("No discovery games found based on preferences")
    except Exception as e:
        print(f"Error in discovery: {e}")

def main():
    """Main function to run all tests"""
    print("===== TESTING UPDATED SEARCH FUNCTIONALITY =====")
    
    test_search()
    test_recommendations()
    test_random_games()
    test_game_by_id()
    test_discovery()
    
    print("\n===== ALL TESTS COMPLETED =====")

if __name__ == "__main__":
    main() 