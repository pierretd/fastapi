#!/usr/bin/env python
"""
Test script for search functionality
This script tests if the search works well with our enhanced data
"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
from fastembed.sparse import SparseTextEmbedding
from qdrant_client.models import SparseVector

# Load environment variables
load_dotenv()

# Initialize clients and models
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")

# Connect to Qdrant
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Initialize embedding models
dense_embedder = TextEmbedding(EMBEDDING_MODEL)
sparse_embedder = SparseTextEmbedding(SPARSE_MODEL)

def hybrid_search(query, limit=5, use_sparse=True):
    """
    Perform a hybrid search using both dense and sparse vectors
    
    Args:
        query (str): Search query text
        limit (int): Maximum number of results to return
        use_sparse (bool): Whether to use sparse vectors for hybrid search
    
    Returns:
        list: Search results
    """
    try:
        print(f"Searching for: '{query}'")
        
        # Generate dense embedding for query
        dense_embedding = list(dense_embedder.embed([query]))[0].tolist()
        
        # If using hybrid search, also generate sparse embedding
        sparse_vec = None
        if use_sparse:
            sparse_embedding = list(sparse_embedder.embed([query]))[0]
            sparse_vec = SparseVector(
                indices=sparse_embedding.indices.tolist(),
                values=sparse_embedding.values.tolist()
            )
        
        # Perform search
        if use_sparse and sparse_vec:
            # Hybrid search with both vectors
            print("Using hybrid search (dense + sparse vectors)")
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=("fast-bge-small-en-v1.5", dense_embedding),
                query_sparse_vector=("fast-sparse-splade_pp_en_v1", sparse_vec),
                limit=limit,
                with_payload=True
            )
        else:
            # Dense-only search
            print("Using dense vector search only")
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=("fast-bge-small-en-v1.5", dense_embedding),
                limit=limit,
                with_payload=True
            )
        
        return results
    except Exception as e:
        print(f"Error during search: {e}")
        return []

def test_search_queries():
    """Test multiple search queries to verify search functionality"""
    test_queries = [
        "adventure game with puzzles",
        "match 3 game with story",
        "building simulation",
        "strategy game",
        "action adventure with rpg elements"
    ]
    
    for query in test_queries:
        print(f"\n===== SEARCHING: '{query}' =====")
        
        # Test hybrid search
        results = hybrid_search(query, limit=3, use_sparse=True)
        
        # Print results
        if results:
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
        else:
            print("No results found or invalid response structure.")
        
        # Add a comparison with dense-only search
        print("\n--- COMPARISON: Dense-only search ---")
        dense_results = hybrid_search(query, limit=3, use_sparse=False)
        if dense_results:
            print(f"Found {len(dense_results)} results:")
            for i, result in enumerate(dense_results):
                print(f"  {i+1}. {result.payload.get('name', 'Unknown')} (score: {result.score:.4f})")
        else:
            print("No results found with dense-only search.")

if __name__ == "__main__":
    # First, check collection info
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        points_count = client.count(collection_name=COLLECTION_NAME)
        print(f"Collection info: {COLLECTION_NAME}")
        print(f"  Status: {collection_info.status}")
        print(f"  Points count: {points_count.count if points_count else 'unknown'}")
        print(f"  Vectors config: {collection_info.config.params.vectors}")
        print(f"  Sparse vectors config: {collection_info.config.params.sparse_vectors}")
    except Exception as e:
        print(f"Error checking collection: {e}")
    
    # Run search tests
    test_search_queries() 