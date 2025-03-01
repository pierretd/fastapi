"""
Test fixes for the Steam Games Search API.

This script examines Qdrant data structure and implements
a corrected search function that works with the current client version.
"""

import os
from dotenv import load_dotenv
import json
from pprint import pprint
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import requests
from fastembed import TextEmbedding

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

# Initialize TextEmbedding
embedder = TextEmbedding(model_name=EMBEDDING_MODEL, max_length=512, cache_dir="./.embeddings_cache")

def check_collection_structure():
    """Check the collection's structure"""
    print("\n=== Checking Collection Structure ===")
    try:
        # Get collection info
        collection = qdrant.get_collection(collection_name=COLLECTION_NAME)
        print(f"Collection info: {collection}")
        
        # Get a sample record
        scroll_results = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=1,
            with_payload=True,
            with_vectors=True
        )
        
        points = scroll_results[0]
        if points:
            point = points[0]
            print("\nSample record structure:")
            print(f"ID: {point.id}")
            
            print("\nPayload structure:")
            if hasattr(point, 'payload') and point.payload:
                for key, value in point.payload.items():
                    print(f"  {key}: {type(value).__name__} -> {value[:100] if isinstance(value, str) else value}")
            else:
                print("  No payload available")
            
            print("\nVector structure:")
            if hasattr(point, 'vector'):
                if isinstance(point.vector, dict):
                    for name, vector in point.vector.items():
                        print(f"  Vector '{name}': {type(vector).__name__}, length: {len(vector) if hasattr(vector, '__len__') else 'N/A'}")
                else:
                    print(f"  Vector: {type(point.vector).__name__}, length: {len(point.vector) if hasattr(point.vector, '__len__') else 'N/A'}")
            else:
                print("  No vector available")
            
        else:
            print("No records found")
        
    except Exception as e:
        print(f"Error checking collection structure: {e}")

def corrected_search_games(query_text, limit=5):
    """
    Corrected search function that works with the current version of Qdrant client
    
    Args:
        query_text (str): The search query
        limit (int): Number of results to return
        
    Returns:
        list: List of dictionaries with search results
    """
    print(f"\n=== Performing Corrected Search for: '{query_text}' ===")
    try:
        # Generate vector embedding for the query
        vector = embedder.embed(query_text)[0].tolist()  # Get the first embedding and convert to list
        
        # Perform the search
        search_results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
            with_payload=True
        )
        
        # Convert to a format that can be processed by our application
        formatted_results = []
        for hit in search_results:
            result = {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload if hasattr(hit, 'payload') else {}
            }
            formatted_results.append(result)
        
        return formatted_results
    except Exception as e:
        print(f"Error during search: {e}")
        return []

def test_search_by_id():
    """Test retrieving a specific game by ID"""
    print("\n=== Testing Retrieve by ID ===")
    
    # Get a sample ID from the collection
    try:
        scroll_results = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=1,
            with_payload=True
        )
        
        points = scroll_results[0]
        if not points:
            print("No records found")
            return
        
        sample_id = points[0].id
        print(f"Testing retrieval for game ID: {sample_id}")
        
        # Retrieve the specific point
        retrieved = qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[sample_id],
            with_payload=True,
            with_vectors=False
        )
        
        if retrieved:
            print(f"Successfully retrieved game with ID {sample_id}")
            point = retrieved[0]
            print("Point structure:")
            print(f"ID: {point.id}")
            
            if hasattr(point, 'payload') and point.payload:
                print("Game name:", point.payload.get('name', 'Unknown'))
                print("Genres:", point.payload.get('genres', 'Unknown'))
            else:
                print("No payload available")
        else:
            print(f"No game found with ID {sample_id}")
            
    except Exception as e:
        print(f"Error during retrieval: {e}")

def test_corrected_search():
    """Test the corrected search function"""
    print("\n=== Testing Corrected Search Function ===")
    
    test_queries = [
        "open world RPG with dragons",
        "multiplayer shooter with vehicles",
        "relaxing puzzle games"
    ]
    
    for query in test_queries:
        print(f"\nResults for query: '{query}'")
        results = corrected_search_games(query, limit=3)
        
        if results:
            for i, hit in enumerate(results):
                print(f"{i+1}. ID: {hit['id']}, Score: {hit['score']:.4f}")
                if hit['payload']:
                    print(f"   Name: {hit['payload'].get('name', 'N/A')}")
                    print(f"   Genres: {hit['payload'].get('genres', 'N/A')}")
                    print(f"   Price: ${hit['payload'].get('price', 'N/A')}")
                else:
                    print("   No payload data available")
        else:
            print("No results found or error occurred")

def main():
    """Main function"""
    print("Starting test fixes for Steam Games Search API...")
    
    # Check collection structure
    check_collection_structure()
    
    # Test retrieving by ID
    test_search_by_id()
    
    # Test corrected search
    test_corrected_search()
    
    print("\n=== Testing complete! ===")

if __name__ == "__main__":
    main() 