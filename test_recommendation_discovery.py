"""
Test script for recommendation and discovery features of the Steam Games Search API.

This script tests the enhanced recommendation and discovery capabilities.
"""

import os
import json
import requests
from pprint import pprint

# API base URL
BASE_URL = "http://localhost:8000"

def test_enhanced_recommendations():
    """Test the enhanced recommendation endpoint with various combinations"""
    print("\n=== Testing Enhanced Recommendations ===")
    
    # First get some sample game IDs to work with
    print("Fetching random games to use as test data...")
    response = requests.get(f"{BASE_URL}/random-games?limit=5")
    
    if response.status_code != 200:
        print(f"Error fetching random games: {response.text}")
        return
    
    games = response.json()
    if not games:
        print("No games returned")
        return
    
    # Ensure all IDs are strings
    game_ids = [str(game["id"]) for game in games]
    print(f"Using game IDs: {game_ids}")
    
    # Test case 1: Recommendation with positive IDs only
    print("\nTest 1: Recommendation with positive IDs only")
    payload = {
        "positive_ids": game_ids[:2],
        "limit": 3
    }
    
    response = requests.post(f"{BASE_URL}/enhanced-recommend", json=payload)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} recommendations:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')} (Score: {game['score']:.4f})")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    # Test case 2: Recommendation with positive and negative IDs
    print("\nTest 2: Recommendation with positive and negative IDs")
    payload = {
        "positive_ids": game_ids[:1],
        "negative_ids": game_ids[3:4],
        "limit": 3
    }
    
    response = requests.post(f"{BASE_URL}/enhanced-recommend", json=payload)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} recommendations:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')} (Score: {game['score']:.4f})")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    # Test case 3: Recommendation with query only
    print("\nTest 3: Recommendation with query only")
    payload = {
        "query": "strategy games with building",
        "limit": 3
    }
    
    response = requests.post(f"{BASE_URL}/enhanced-recommend", json=payload)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} recommendations:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')} (Score: {game['score']:.4f})")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    # Test case 4: Recommendation with everything
    print("\nTest 4: Recommendation with positive IDs, negative IDs, and query")
    payload = {
        "positive_ids": game_ids[:1],
        "negative_ids": game_ids[3:4],
        "query": "strategy games",
        "limit": 3
    }
    
    response = requests.post(f"{BASE_URL}/enhanced-recommend", json=payload)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} recommendations:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')} (Score: {game['score']:.4f})")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")

def test_discovery_recommendations():
    """Test the discovery recommendation endpoint"""
    print("\n=== Testing Discovery Recommendations ===")
    
    # Test case 1: Initial discovery (no feedback)
    print("\nTest 1: Initial discovery (no feedback)")
    response = requests.post(f"{BASE_URL}/discover", json={"limit": 5})
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} random games:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')}")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    # Test case 2: Discovery with feedback
    print("\nTest 2: Discovery with feedback")
    
    # Get some random games to use as feedback
    response = requests.get(f"{BASE_URL}/random-games?limit=5")
    
    if response.status_code != 200:
        print(f"Error fetching random games: {response.text}")
        return
    
    games = response.json()
    if not games:
        print("No games returned")
        return
    
    # Ensure all IDs are strings
    liked_ids = [str(games[0]["id"]), str(games[1]["id"])]
    disliked_ids = [str(games[2]["id"])]
    
    payload = {
        "liked_ids": liked_ids,
        "disliked_ids": disliked_ids,
        "limit": 5
    }
    
    response = requests.post(f"{BASE_URL}/discover", json=payload)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} recommendations based on feedback:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')}")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")

def test_diverse_recommendations():
    """Test the diverse recommendation endpoint"""
    print("\n=== Testing Diverse Recommendations ===")
    
    # Get a random game to use as seed
    print("Fetching a random game to use as seed...")
    response = requests.get(f"{BASE_URL}/random-games?limit=1")
    
    if response.status_code != 200:
        print(f"Error fetching random game: {response.text}")
        return
    
    games = response.json()
    if not games:
        print("No games returned")
        return
    
    seed_game = games[0]
    # Ensure ID is a string
    seed_id = str(seed_game["id"])
    print(f"Using seed game: {seed_game['payload'].get('name', 'Unknown')} (ID: {seed_id})")
    
    # Test with different diversity factors
    diversity_factors = [0.0, 0.5, 1.0]
    
    for factor in diversity_factors:
        print(f"\nTest: Diverse recommendations with diversity_factor = {factor}")
        payload = {
            "seed_id": seed_id,
            "limit": 5,
            "diversity_factor": factor
        }
        
        response = requests.post(f"{BASE_URL}/diverse-recommend", json=payload)
        
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} diverse recommendations:")
            for i, game in enumerate(results):
                print(f"{i+1}. {game['payload'].get('name', 'Unknown')} (Score: {game['score']:.4f})")
                print(f"   Steam App ID: {game['id']}")
                print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
        else:
            print(f"Error: {response.text}")

def test_random_games():
    """Test the random games endpoint"""
    print("\n=== Testing Random Games ===")
    
    response = requests.get(f"{BASE_URL}/random-games?limit=3")
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} random games:")
        for i, game in enumerate(results):
            print(f"{i+1}. {game['payload'].get('name', 'Unknown')}")
            print(f"   Steam App ID: {game['id']}")
            print(f"   Genres: {game['payload'].get('genres', 'N/A')}")
    else:
        print(f"Error: {response.text}")

def main():
    """Main function to run all tests"""
    print("Starting tests for Recommendation and Discovery features...")
    
    # Test all features
    test_random_games()
    test_enhanced_recommendations()
    test_discovery_recommendations()
    test_diverse_recommendations()
    
    print("\n=== Testing complete! ===")

if __name__ == "__main__":
    main() 