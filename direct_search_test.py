#!/usr/bin/env python
"""
Direct search test without relying on search.py
This bypasses any issues with the search.py implementation
"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

# Load environment variables
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# Initialize clients
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedder = TextEmbedding(EMBEDDING_MODEL)

def direct_search(query, limit=5):
    """Search directly using the Qdrant client without dependencies on search.py"""
    print(f"\n===== SEARCHING: '{query}' =====")

    try:
        # Generate embedding for query
        embeddings = list(embedder.embed([query]))
        
        # If empty query, return
        if not query or not query.strip():
            print("Empty query, skipping search")
            return
        
        # Execute direct vector search
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embeddings[0].tolist(),
            limit=limit,
            with_payload=True
        )
        
        # Print results
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"\n{i+1}. {result.payload.get('name', 'Unknown')} (score: {result.score:.4f})")
            
            # Print description
            desc = result.payload.get('short_description', '')
            if desc:
                print(f"   Description: {desc[:150]}...")
            
            # Print genre and tags
            genres = result.payload.get('genres', '')
            tags = result.payload.get('tags', '')
            if genres:
                print(f"   Genres: {genres}")
            if tags:
                print(f"   Tags: {tags[:100]}...")
    
    except Exception as e:
        print(f"Error during search: {e}")

def main():
    """Test multiple search queries"""
    test_queries = [
        "adventure game with puzzles",
        "match 3 game with story",
        "building simulation",
        "strategy game",
        "action adventure with rpg elements"
    ]
    
    # Print collection info first
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"Collection info: {COLLECTION_NAME}")
        print(f"  Status: {collection_info.status}")
        print(f"  Points count: {collection_info.points_count}")
        print(f"  Vectors configuration: {collection_info.config.params.vectors}")
    except Exception as e:
        print(f"Error fetching collection info: {e}")
    
    # Run each query
    for query in test_queries:
        direct_search(query, limit=3)

if __name__ == "__main__":
    main() 