#!/usr/bin/env python
"""
Simplified hybrid search using Qdrant's recommended approach
Based on official documentation: https://qdrant.tech/documentation/beginner-tutorials/hybrid-search-fastembed/
"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import json

# Load environment variables
load_dotenv()

# Get environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_unique_20250302")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "prithivida/Splade_PP_en_v1")

class HybridSearcher:
    """Game search class using hybrid search with dense and sparse vectors"""
    
    def __init__(self, collection_name):
        # Initialize Qdrant client
        self.collection_name = collection_name
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Set models for encoding (this registers them with the client)
        self.client.set_model(EMBEDDING_MODEL)
        self.client.set_sparse_model(SPARSE_MODEL)
        
        # Get vector names from client
        self.dense_vector_name = self.client.get_vector_field_name()  # Should return "fast-bge-small-en-v1.5"
        self.sparse_vector_name = self.client.get_sparse_vector_field_name()  # Should return "fast-sparse-splade_pp_en_v1"
        
        print(f"Initialized hybrid searcher with:")
        print(f"  Dense vector: {self.dense_vector_name}")
        print(f"  Sparse vector: {self.sparse_vector_name}")
        
    def collection_info(self):
        """Get information about the collection"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            points_count = self.client.count(collection_name=self.collection_name)
            
            print(f"Collection info: {self.collection_name}")
            print(f"  Status: {collection_info.status}")
            print(f"  Points count: {points_count.count if points_count else 'unknown'}")
            print(f"  Vectors config: {json.dumps(collection_info.config.params.vectors, default=str)}")
            print(f"  Sparse vectors config: {json.dumps(collection_info.config.params.sparse_vectors, default=str)}")
            
            return collection_info
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None
    
    def search(self, query_text, limit=5, filter_condition=None):
        """
        Search for games using hybrid approach (dense + sparse vectors)
        
        Args:
            query_text (str): The search query
            limit (int): Number of results to return
            filter_condition (dict, optional): Filter condition for search
            
        Returns:
            list: Search results
        """
        try:
            print(f"Searching for: '{query_text}'")
            
            # Using the built-in query method which handles hybrid search automatically
            # This method automatically:
            # 1. Encodes the query using both dense and sparse models
            # 2. Performs search with both vectors
            # 3. Combines results using reciprocal rank fusion
            results = self.client.query(
                collection_name=self.collection_name,
                query_text=query_text,
                query_filter=filter_condition,
                limit=limit
            )
            
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []
            
    def search_with_filter(self, query_text, genre=None, price_range=None, limit=5):
        """
        Search with additional filters for genre and price range
        
        Args:
            query_text (str): The search query
            genre (str, optional): Filter by specific genre
            price_range (str, optional): Filter by price range (free, low_range, mid_range, high_range)
            limit (int): Number of results to return
            
        Returns:
            list: Search results
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Build the filter
        filter_conditions = []
        
        if genre:
            filter_conditions.append(
                FieldCondition(key="genres", match=MatchValue(value=genre))
            )
            
        if price_range:
            filter_conditions.append(
                FieldCondition(key="price_range", match=MatchValue(value=price_range))
            )
        
        # Create the final filter
        filter_obj = None
        if filter_conditions:
            filter_obj = Filter(must=filter_conditions)
            
        # Perform the search
        return self.search(query_text, limit=limit, filter_condition=filter_obj)


def test_search_queries():
    """Test multiple search queries to verify hybrid search functionality"""
    # Create a searcher instance
    searcher = HybridSearcher(COLLECTION_NAME)
    
    # Display collection info
    searcher.collection_info()
    
    # Test search queries
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
        results = searcher.search(query, limit=3)
        
        # Print results
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results):
                print(f"\n{i+1}. {result.metadata.get('name', 'Unknown')} (score: {result.score:.4f})")
                
                # Print description
                desc = result.metadata.get('short_description', '')
                if desc:
                    print(f"   Description: {desc[:150]}...")
                
                # Print genre and tags
                genres = result.metadata.get('genres', '')
                tags = result.metadata.get('tags', '')
                if genres:
                    print(f"   Genres: {genres}")
                if tags:
                    print(f"   Tags: {tags[:100]}...")
        else:
            print("No results found or invalid response structure.")
        
        # Try with a filter if the collection supports it
        if query == "strategy game":
            print("\n--- FILTERED SEARCH: Free strategy games ---")
            filtered_results = searcher.search_with_filter(query, price_range="free", limit=3)
            if filtered_results:
                print(f"Found {len(filtered_results)} free strategy games:")
                for i, result in enumerate(filtered_results):
                    print(f"  {i+1}. {result.metadata.get('name', 'Unknown')} (score: {result.score:.4f})")
            else:
                print("No free strategy games found.")


if __name__ == "__main__":
    test_search_queries() 