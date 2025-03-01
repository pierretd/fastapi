"""
Fixed test script for the Steam Games Search API.

This script correctly handles embedding generation and search operations.
"""

import os
from dotenv import load_dotenv
import json
from pprint import pprint
from qdrant_client import QdrantClient
import requests
from fastembed import TextEmbedding
import numpy as np

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

def fixed_search_games(query_text, limit=5):
    """
    Fixed search function for games using proper embedding approach
    
    Args:
        query_text (str): The search query
        limit (int): Number of results to return
        
    Returns:
        list: List of dictionaries with search results
    """
    print(f"\n=== Performing Fixed Search for: '{query_text}' ===")
    try:
        # Generate vector embedding for the query
        # Note: embed() returns a generator, convert to list, take first item, convert to a regular Python list
        embeddings = list(embedder.embed([query_text]))
        vector = embeddings[0].tolist() if embeddings else []
        
        if not vector:
            print("Failed to generate embedding vector")
            return []
        
        print(f"Generated embedding vector of length: {len(vector)}")
        
        # Perform the search
        search_results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=("fast-bge-small-en-v1.5", vector),  # Specify which vector to use
            limit=limit,
            with_payload=True
        )
        
        print(f"Search returned {len(search_results)} results")
        
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

def test_fixed_search():
    """Test the fixed search function"""
    print("\n=== Testing Fixed Search Function ===")
    
    test_queries = [
        "open world RPG with dragons",
        "multiplayer shooter with vehicles",
        "relaxing puzzle games"
    ]
    
    for query in test_queries:
        print(f"\nResults for query: '{query}'")
        results = fixed_search_games(query, limit=3)
        
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

def test_api_search():
    """
    Test search through API to see error
    This shows the actual API error for diagnosis
    """
    query = "open world RPG with dragons"
    
    try:
        response = requests.get(
            f"http://localhost:8000/search", 
            params={"query": query, "limit": 3}
        )
        
        print(f"\n=== API Search for '{query}' ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error during API search: {e}")

def create_patch_instructions():
    """Create instructions for patching the main search.py file"""
    print("\n=== Patch Instructions for search.py ===")
    print("""
To fix the search function in search.py, make these changes:

1. Update the search_games function to handle embeddings correctly:

```python
def search_games(query_text, limit=5, use_hybrid=True):
    \"\"\"
    Search for games using sparse, dense, or hybrid approaches.
    
    Args:
        query_text (str): The search query
        limit (int): Number of results to return
        use_hybrid (bool): Whether to use hybrid search
        
    Returns:
        list: Search results
    \"\"\"
    try:
        if use_hybrid:
            # Generate embedding
            embeddings = list(embedder.embed([query_text]))
            vector = embeddings[0].tolist() if embeddings else []
            
            # Search with proper vector field name
            results = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=("fast-bge-small-en-v1.5", vector),
                limit=limit,
                with_payload=True
            )
        else:
            # For non-hybrid, similar approach but with explicit field
            embeddings = list(embedder.embed([query_text]))
            vector = embeddings[0].tolist() if embeddings else []
            
            results = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=("fast-bge-small-en-v1.5", vector),
                limit=limit,
                with_payload=True
            )
        
        return results
    except Exception as e:
        print(f"Error during search: {e}")
        return []
```

2. Update get_game_recommendations function to use proper vector field name:

```python
def get_game_recommendations(game_id, limit=5):
    \"\"\"
    Get game recommendations based on a given game ID.
    
    Args:
        game_id (int): The Steam App ID of the game
        limit (int): Number of recommendations to return
        
    Returns:
        list: Recommended games
    \"\"\"
    try:
        recommendations = qdrant.recommend(
            collection_name=COLLECTION_NAME,
            positive=[game_id],
            using="fast-bge-small-en-v1.5",  # Specify which vector to use
            limit=limit,
            with_payload=True
        )
        return recommendations
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []
```
""")

def main():
    """Main function"""
    print("Starting fixed test script for Steam Games Search API...")
    
    # Test fixed search
    test_fixed_search()
    
    # Test API search to see error
    test_api_search()
    
    # Output patch instructions
    create_patch_instructions()
    
    print("\n=== Testing complete! ===")

if __name__ == "__main__":
    main() 