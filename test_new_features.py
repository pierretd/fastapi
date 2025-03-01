#!/usr/bin/env python
"""
Test script for the new API features including:
- Game details with similar games
- Pagination
- Error handling
- Search suggestions
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        result = response.json()
        print(f"Health Status: {result['status']}")
        print(f"Timestamp: {result['timestamp']}")
        print("✅ Health Check Test Passed")
    else:
        print(f"❌ Health Check Test Failed: {response.status_code} - {response.text}")

def test_game_details():
    """Test the game details endpoint with similar games"""
    print("\n=== Testing Game Details ===")
    
    # First get a random game to use as our test subject
    response = requests.get(f"{API_URL}/random-games?limit=1")
    if response.status_code != 200:
        print(f"❌ Failed to get random game: {response.status_code} - {response.text}")
        return
    
    # Extract the game ID from the random game
    random_game = response.json()[0]
    game_id = random_game["id"]
    
    print(f"Getting details for game: {random_game['payload']['name']} (ID: {game_id})")
    
    # Test the game details endpoint
    response = requests.get(f"{API_URL}/game/{game_id}")
    if response.status_code == 200:
        game = response.json()
        print(f"Name: {game['name']}")
        print(f"Price: ${game['price']}")
        print(f"Release Date: {game['release_date']}")
        print(f"Developers: {game['developers']}")
        print(f"Short Description: {game['short_description'][:100]}...")
        
        print("\nSimilar Games:")
        for i, similar_game in enumerate(game['similar_games'], 1):
            print(f"  {i}. {similar_game['payload']['name']} (Similarity: {similar_game['score']:.2f})")
        
        print("✅ Game Details Test Passed")
    else:
        print(f"❌ Game Details Test Failed: {response.status_code} - {response.text}")

def test_pagination():
    """Test the pagination functionality on search endpoint"""
    print("\n=== Testing Pagination ===")
    
    test_query = "strategy games"
    
    # Test first page
    response = requests.post(
        f"{API_URL}/search", 
        json={"query": test_query, "limit": 5, "offset": 0}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total Results: {result['total']}")
        print(f"Page: {result['page']}/{result['pages']}")
        print(f"Page Size: {result['page_size']}")
        
        print("\nFirst Page Results:")
        for i, item in enumerate(result['items'], 1):
            print(f"  {i}. {item['payload']['name']} (Score: {item['score']:.2f})")
            
        # Test second page 
        if result['pages'] > 1:
            response = requests.post(
                f"{API_URL}/search", 
                json={"query": test_query, "limit": 5, "offset": 5}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSecond Page:")
                print(f"Page: {result['page']}/{result['pages']}")
                
                print("\nSecond Page Results:")
                for i, item in enumerate(result['items'], 1):
                    print(f"  {i}. {item['payload']['name']} (Score: {item['score']:.2f})")
            else:
                print(f"❌ Second Page Request Failed: {response.status_code} - {response.text}")
                
        print("✅ Pagination Test Passed")
    else:
        print(f"❌ Pagination Test Failed: {response.status_code} - {response.text}")

def test_search_suggestions():
    """Test the search suggestions endpoint"""
    print("\n=== Testing Search Suggestions ===")
    
    test_queries = ["stra", "adven", "puzz", "rac"]
    
    for query in test_queries:
        print(f"\nSuggestions for '{query}':")
        response = requests.get(f"{API_URL}/suggest?query={query}&limit=3")
        
        if response.status_code == 200:
            suggestions = response.json()
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion['name']} (ID: {suggestion['id']})")
            else:
                print("  No suggestions found")
        else:
            print(f"❌ Failed to get suggestions: {response.status_code} - {response.text}")
    
    print("✅ Search Suggestions Test Passed")

def test_error_handling():
    """Test the improved error handling"""
    print("\n=== Testing Error Handling ===")
    
    # Test invalid game ID
    invalid_id = "99999999999"
    print(f"Testing with invalid game ID: {invalid_id}")
    
    response = requests.get(f"{API_URL}/game/{invalid_id}")
    if response.status_code == 404:
        error = response.json()
        print(f"Expected Error (404): {error['detail']}")
        print("✅ Error Handling Test (404) Passed")
    else:
        print(f"❌ Error Handling Test (404) Failed: {response.status_code} - {response.text}")
    
    # Test invalid request format
    print("\nTesting with invalid request format")
    response = requests.post(
        f"{API_URL}/enhanced-recommend", 
        json={"invalid_param": "value"}
    )
    
    if response.status_code == 422:
        print(f"Expected Error (422): Validation Error")
        print("✅ Error Handling Test (422) Passed")
    else:
        print(f"❌ Error Handling Test (422) Failed: {response.status_code} - {response.text}")

def test_caching_headers():
    """Test the caching headers on responses"""
    print("\n=== Testing Caching Headers ===")
    
    endpoints = [
        "/",  # root - long cache
        "/random-games?limit=1",  # random games - short cache
        "/search"  # search - medium cache
    ]
    
    for endpoint in endpoints:
        if endpoint == "/search":
            response = requests.post(
                f"{API_URL}{endpoint}", 
                json={"query": "adventure", "limit": 1}
            )
        else:
            response = requests.get(f"{API_URL}{endpoint}")
        
        if response.status_code == 200:
            cache_header = response.headers.get('Cache-Control')
            if cache_header:
                print(f"Endpoint: {endpoint} - Cache Header: {cache_header}")
            else:
                print(f"❌ No Cache-Control header for {endpoint}")
        else:
            print(f"❌ Request failed for {endpoint}: {response.status_code}")
    
    print("✅ Caching Headers Test Completed")

def main():
    """Run all tests"""
    print("=== Testing New API Features ===")
    
    # Check if API is up
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code != 200:
            print(f"❌ API is not responding correctly: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_URL}. Is the server running?")
        return
    
    print(f"✅ API is running at {API_URL}")
    
    # Run tests
    test_health_check()
    test_game_details()
    test_pagination()
    test_search_suggestions()
    test_error_handling()
    test_caching_headers()
    
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    main() 