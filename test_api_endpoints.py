"""
Test file for the Steam Games Search API endpoints.

This script tests the FastAPI endpoints directly by making HTTP requests to them.
It verifies that the API is properly configured and that all endpoints return expected results.
"""

import requests
import json
import os
from dotenv import load_dotenv
import time
from pprint import pprint

# Load environment variables
load_dotenv()

# Set the base URL for API calls
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            pprint(data)
            return True
        else:
            print(f"Error: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error accessing root endpoint: {e}")
        return False

def test_search_endpoint():
    """Test the search endpoint with various queries"""
    print("\n=== Testing Search Endpoint ===")
    test_queries = [
        "open world RPG with dragons",
        "multiplayer shooter with vehicles",
        "relaxing puzzle games"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        try:
            # Test hybrid search
            response = requests.get(
                f"{BASE_URL}/search", 
                params={"query": query, "limit": 3, "use_hybrid": True}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"Found {len(results)} results:")
                for i, game in enumerate(results):
                    print(f"{i+1}. {game.get('payload', {}).get('name')} (Score: {game.get('score'):.4f})")
                    print(f"   Steam App ID: {game.get('id')}")
                    print(f"   Genres: {game.get('payload', {}).get('genres', 'N/A')}")
            else:
                print(f"Error: Unexpected status code {response.status_code}")
                print(f"Response: {response.text}")
                
            # Test non-hybrid search for comparison
            print("\nTesting non-hybrid search:")
            response = requests.get(
                f"{BASE_URL}/search", 
                params={"query": query, "limit": 3, "use_hybrid": False}
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"Found {len(results)} results:")
                for i, game in enumerate(results):
                    print(f"{i+1}. {game.get('payload', {}).get('name')} (Score: {game.get('score'):.4f})")
            else:
                print(f"Error: Unexpected status code {response.status_code}")
        except Exception as e:
            print(f"Error during search: {e}")
    
    return True

def test_recommendations_endpoint():
    """Test the recommendations endpoint"""
    print("\n=== Testing Recommendations Endpoint ===")
    
    # First, get some game IDs from search results
    try:
        response = requests.get(
            f"{BASE_URL}/search", 
            params={"query": "popular games", "limit": 1}
        )
        
        if response.status_code != 200 or not response.json():
            print("Couldn't find games to test recommendations.")
            return False
            
        game = response.json()[0]
        game_id = game.get('id')
        game_name = game.get('payload', {}).get('name', 'Unknown Game')
        
        print(f"\nTesting recommendations for: {game_name} (ID: {game_id})")
        
        # Get recommendations for this game
        response = requests.get(f"{BASE_URL}/recommend/{game_id}", params={"limit": 3})
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} recommendations:")
            for i, game in enumerate(results):
                print(f"{i+1}. {game.get('payload', {}).get('name')} (Score: {game.get('score'):.4f})")
                print(f"   Steam App ID: {game.get('id')}")
                print(f"   Genres: {game.get('payload', {}).get('genres', 'N/A')}")
            return True
        else:
            print(f"Error: Unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing recommendations: {e}")
        return False

def test_invalid_requests():
    """Test how the API handles invalid requests"""
    print("\n=== Testing Invalid Requests ===")
    
    # Test search with missing query
    print("\nTesting search with missing query:")
    try:
        response = requests.get(f"{BASE_URL}/search")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test recommendations with invalid game ID
    print("\nTesting recommendations with invalid game ID:")
    try:
        response = requests.get(f"{BASE_URL}/recommend/99999999999")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    return True

def main():
    """Main function to run all tests"""
    print("Starting API endpoint tests for Steam Games Search API...")
    
    # Test basic connectivity
    if not test_root_endpoint():
        print(f"\nError connecting to the API at {BASE_URL}")
        print("Please make sure the API is running and the BASE_URL is correct.")
        return
    
    # Run the endpoint tests
    test_search_endpoint()
    test_recommendations_endpoint()
    test_invalid_requests()
    
    print("\n=== API Endpoint Testing complete! ===")

if __name__ == "__main__":
    main() 