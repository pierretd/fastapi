"""
Test fix for the Steam Games Search API.

This script directly accesses the Qdrant client to test search functionality
and diagnose issues with the search results structure.
"""

import os
from dotenv import load_dotenv
import json
from pprint import pprint
from qdrant_client import QdrantClient
import requests

# Load environment variables
load_dotenv()

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_with_sparse_dense")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")

# Connect to Qdrant
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def check_collection_status():
    """Check if the collection exists and has data"""
    print("\n=== Checking Collection Status ===")
    try:
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        points_count = collection_info.points_count
        print(f"Collection '{COLLECTION_NAME}' exists with {points_count} points.")
        
        if points_count == 0:
            print("Collection is empty.")
            return False
        return True
    except Exception as e:
        print(f"Error: Collection '{COLLECTION_NAME}' does not exist or cannot be accessed.")
        print(f"Error details: {e}")
        return False

def test_raw_search():
    """Test search using raw Qdrant API calls"""
    print("\n=== Testing Raw Search ===")
    
    query = "open world RPG with dragons"
    print(f"Query: '{query}'")
    
    try:
        # First check client capabilities
        print("\nChecking client methods:")
        print("dir(qdrant):", [m for m in dir(qdrant) if not m.startswith('_')])
        
        # Try direct search if possible
        if hasattr(qdrant, 'search'):
            print("\nTrying direct search:")
            # Create embeddings using API if needed
            if hasattr(qdrant, 'encode'):
                vector = qdrant.encode(query)
                search_results = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=vector,
                    limit=3
                )
            else:
                # Try direct search with text
                search_results = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_text=query,
                    limit=3
                )
            
            print(f"Search returned {len(search_results)} results")
            print("Type of first result:", type(search_results[0]).__name__ if search_results else "N/A")
            print("Dir of first result:", dir(search_results[0]) if search_results else "N/A")
            
            for i, hit in enumerate(search_results):
                print(f"\nResult {i+1}:")
                print(f"ID: {hit.id}")
                print(f"Score: {hit.score}")
                if hasattr(hit, 'payload'):
                    print(f"Has payload: {True}")
                    print(f"Payload keys: {hit.payload.keys() if hit.payload else 'Empty'}")
                else:
                    print(f"Has payload: {False}")
                
                # Print all attributes
                for attr in dir(hit):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(hit, attr)
                            if not callable(value):
                                print(f"Attribute '{attr}': {type(value)}")
                        except Exception as e:
                            print(f"Error accessing attribute '{attr}': {e}")
        
        # Try scroll API to see record structure
        print("\nTrying scroll API:")
        scroll_results = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        print("Scroll results type:", type(scroll_results))
        if scroll_results:
            points = scroll_results[0]
            print(f"Retrieved {len(points)} points")
            if points:
                point = points[0]
                print("Point type:", type(point).__name__)
                print("Point dir:", dir(point))
                if hasattr(point, 'payload'):
                    print("Payload keys:", point.payload.keys() if point.payload else "Empty")
                    print("Payload sample:", dict(list(point.payload.items())[:3]) if point.payload else "Empty")
        
    except Exception as e:
        print(f"Error during search: {e}")

def test_api_search():
    """Test search using the FastAPI endpoint"""
    print("\n=== Testing API Search ===")
    
    query = "open world RPG with dragons"
    print(f"Query: '{query}'")
    
    try:
        response = requests.get(
            f"http://localhost:8000/search", 
            params={"query": query, "limit": 3}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results:")
            for i, game in enumerate(results):
                print(f"{i+1}. Game info:")
                pprint(game)
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error during API search: {e}")

def main():
    """Main function"""
    print("Starting test fix for Steam Games Search API...")
    
    # Check collection status
    if not check_collection_status():
        print("Collection issue detected. Please make sure data is uploaded.")
        return
    
    # Test raw search functionality
    test_raw_search()
    
    # Test API search
    test_api_search()
    
    print("\n=== Testing complete! ===")

if __name__ == "__main__":
    main() 