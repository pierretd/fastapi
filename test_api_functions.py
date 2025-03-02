#!/usr/bin/env python
"""
Test script for API functions
This script tests the main functions used by the API to ensure they work correctly.
"""
import os
from dotenv import load_dotenv
from search import (
    search_games,
    get_game_recommendations,
    get_random_games,
    get_game_by_id
)

# Load environment variables
load_dotenv()

def test_search():
    """Test the search_games function"""
    print("\n=== Testing Search Function ===")
    
    # Test with a query
    query = "adventure game with magic"
    print(f"Searching for: '{query}'")
    results = search_games(query, page=1, page_size=5)
    
    if results["items"]:
        print(f"Found {len(results['items'])} results:")
        for i, item in enumerate(results["items"]):
            print(f"  {i+1}. {item['payload'].get('name', 'Unknown')} (score: {item['score']:.4f})")
    else:
        print("No results found.")
        
    # Test with an empty query (should return random games)
    print("\nTesting empty query (should return random games):")
    results = search_games("", page=1, page_size=5)
    
    if results["items"]:
        print(f"Found {len(results['items'])} random games:")
        for i, item in enumerate(results["items"]):
            print(f"  {i+1}. {item['payload'].get('name', 'Unknown')}")
    else:
        print("No random games found.")

def test_recommendations():
    """Test the game recommendations function"""
    print("\n=== Testing Recommendations Function ===")
    
    # First, let's get a game ID from random games
    random_games = get_random_games(limit=1)
    if not random_games:
        print("No games available for testing recommendations.")
        return
        
    game_id = random_games[0]["id"]
    game_name = random_games[0]["payload"].get("name", "Unknown Game")
    
    print(f"Getting recommendations for game: {game_name} (ID: {game_id})")
    recommendations = get_game_recommendations(game_id, limit=5)
    
    if recommendations:
        print(f"Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations):
            print(f"  {i+1}. {rec['payload'].get('name', 'Unknown')} (score: {rec['score']:.4f})")
    else:
        print(f"No recommendations found for {game_name}.")

def test_random_games():
    """Test the random games function"""
    print("\n=== Testing Random Games Function ===")
    
    random_games = get_random_games(limit=5)
    
    if random_games:
        print(f"Found {len(random_games)} random games:")
        for i, game in enumerate(random_games):
            print(f"  {i+1}. {game['payload'].get('name', 'Unknown')}")
    else:
        print("No random games found.")

def test_game_by_id():
    """Test the get_game_by_id function"""
    print("\n=== Testing Get Game By ID Function ===")
    
    # First, let's get a game ID from random games
    random_games = get_random_games(limit=1)
    if not random_games:
        print("No games available for testing get_game_by_id.")
        return
        
    game_id = random_games[0]["id"]
    
    print(f"Getting game with ID: {game_id}")
    game = get_game_by_id(game_id)
    
    if game:
        print(f"Found game: {game['payload'].get('name', 'Unknown')}")
        print(f"Description: {game['payload'].get('short_description', 'No description available')[:100]}...")
    else:
        print(f"No game found with ID {game_id}.")

def main():
    """Run all tests"""
    print("=== Testing API Functions ===")
    
    # Test all functions
    test_search()
    test_recommendations()
    test_random_games()
    test_game_by_id()
    
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    main() 