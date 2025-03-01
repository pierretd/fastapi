"""
Test file for the Steam Games Search API.

This script tests the search functionality against the Qdrant collection.
It verifies that the collection is properly set up and that search operations work as expected.
"""

import sys
import os
from dotenv import load_dotenv
import time
from pprint import pprint
import pandas as pd

# Import search functions
from search import (
    qdrant,
    COLLECTION_NAME,
    search_games,
    get_game_recommendations,
    create_collection,
    upload_data_to_qdrant
)

# Load environment variables
load_dotenv()

def test_collection_status():
    """Test if the collection exists and has data"""
    print("\n=== Testing Collection Status ===")
    try:
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        points_count = collection_info.points_count
        print(f"Collection '{COLLECTION_NAME}' exists with {points_count} points.")
        
        if points_count == 0:
            print("Collection is empty. Consider uploading data.")
            return False
        return True
    except Exception as e:
        print(f"Error: Collection '{COLLECTION_NAME}' does not exist or cannot be accessed.")
        print(f"Error details: {e}")
        return False

def test_search_functionality():
    """Test the search functionality with various queries"""
    print("\n=== Testing Search Functionality ===")
    test_queries = [
        "open world RPG with dragons",
        "multiplayer shooter with vehicles",
        "relaxing puzzle games",
        "strategy games with base building",
        "horror games with zombies"
    ]
    
    for query in test_queries:
        print(f"\nResults for query: '{query}'")
        try:
            # Test hybrid search (default)
            results = search_games(query, limit=3, use_hybrid=True)
            print(f"Hybrid search returned {len(results)} results:")
            for i, hit in enumerate(results):
                print(f"{i+1}. {hit.payload.get('name')} (Score: {hit.score:.4f})")
                print(f"   Steam App ID: {hit.id}")
                print(f"   Genres: {hit.payload.get('genres', 'N/A')}")
                print(f"   Price: ${hit.payload.get('price', 'N/A')}")
            
            # Test non-hybrid search for comparison
            if len(results) > 0:
                print("\nNon-hybrid search for the same query:")
                non_hybrid_results = search_games(query, limit=3, use_hybrid=False)
                for i, hit in enumerate(non_hybrid_results):
                    print(f"{i+1}. {hit.payload.get('name')} (Score: {hit.score:.4f})")
        except Exception as e:
            print(f"Error during search: {e}")
    
    return True

def test_recommendations():
    """Test the recommendations functionality"""
    print("\n=== Testing Recommendations ===")
    
    # Try to get a few game IDs from the collection
    try:
        print("Fetching sample game IDs from collection...")
        sample_points = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=5,
            with_payload=True
        )[0]
        
        if not sample_points:
            print("No games found in the collection.")
            return False
        
        for point in sample_points:
            game_id = point.id
            game_name = point.payload.get('name', 'Unknown Game')
            
            print(f"\nRecommendations for: {game_name} (ID: {game_id})")
            try:
                recommendations = get_game_recommendations(game_id, limit=3)
                print(f"Found {len(recommendations)} recommendations:")
                
                for i, hit in enumerate(recommendations):
                    print(f"{i+1}. {hit.payload.get('name')} (Score: {hit.score:.4f})")
                    print(f"   Steam App ID: {hit.id}")
                    print(f"   Genres: {hit.payload.get('genres', 'N/A')}")
            except Exception as e:
                print(f"Error getting recommendations: {e}")
        
        return True
    except Exception as e:
        print(f"Error fetching sample games: {e}")
        return False

def test_sparse_vector_generation():
    """Test sparse vector generation"""
    print("\n=== Testing Sparse Vector Generation ===")
    test_text = "open world RPG with dragons and magic spells"
    
    try:
        sparse_vector = qdrant.generate_sparse_vector(test_text)
        print(f"Sparse vector generated successfully")
        print(f"Indices count: {len(sparse_vector.indices)}")
        print(f"Values count: {len(sparse_vector.values)}")
        print("Sample indices (first 5):", sparse_vector.indices[:5] if len(sparse_vector.indices) > 5 else sparse_vector.indices)
        print("Sample values (first 5):", sparse_vector.values[:5] if len(sparse_vector.values) > 5 else sparse_vector.values)
        return True
    except Exception as e:
        print(f"Error generating sparse vector: {e}")
        return False

def test_dense_vector_generation():
    """Test dense vector generation"""
    print("\n=== Testing Dense Vector Generation ===")
    test_text = "open world RPG with dragons and magic spells"
    
    try:
        dense_vector = qdrant.generate_vector(test_text)
        print(f"Dense vector generated successfully")
        print(f"Vector size: {len(dense_vector)}")
        print("Sample values (first 5):", dense_vector[:5])
        return True
    except Exception as e:
        print(f"Error generating dense vector: {e}")
        return False

def run_upload_if_needed():
    """Run the upload_data_to_qdrant function if collection doesn't exist or is empty"""
    try:
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        if collection_info.points_count == 0:
            print("\n=== Collection is empty, uploading data... ===")
            upload_data_to_qdrant()
            return True
    except Exception:
        print("\n=== Collection doesn't exist, creating and uploading data... ===")
        create_collection()
        upload_data_to_qdrant()
        return True
    
    return False

def main():
    """Main function to run all tests"""
    print("Starting tests for Steam Games Search API...")
    
    # Test collection status
    collection_exists = test_collection_status()
    
    # If collection doesn't exist or is empty, offer to upload data
    if not collection_exists:
        should_upload = input("Do you want to create/upload data to the collection? (y/n): ")
        if should_upload.lower() == 'y':
            run_upload_if_needed()
    
    # Run the search tests
    test_search_functionality()
    
    # Run the recommendations tests
    test_recommendations()
    
    # Test vector generation
    test_sparse_vector_generation()
    test_dense_vector_generation()
    
    print("\n=== Testing complete! ===")

if __name__ == "__main__":
    main() 