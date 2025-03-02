import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import json

# Load environment variables
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

def test_collections():
    """Test accessing data from different collections"""
    print(f"Connecting to Qdrant at {QDRANT_URL}")
    
    # Initialize Qdrant client
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Check available collections
    collections = qdrant.get_collections()
    collection_names = [c.name for c in collections.collections]
    print(f"Available collections: {collection_names}")
    
    # Look for steam_games collections
    steam_collections = [name for name in collection_names if name.startswith("steam_games")]
    print(f"\nSteam collections: {steam_collections}")
    
    # Check if our target collection exists
    if "steam_games_with_sparse_dense" in collection_names:
        print("\nTarget collection 'steam_games_with_sparse_dense' exists")
    else:
        print("\nTarget collection 'steam_games_with_sparse_dense' does NOT exist")
    
    # Test each steam collection
    game_id = 1899290  # The ID we know exists
    for collection_name in steam_collections:
        print(f"\nTesting collection: {collection_name}")
        try:
            # Get collection info
            collection_info = qdrant.get_collection(collection_name)
            print(f"Collection info: {collection_info}")
            print(f"Points count: {collection_info.points_count}")
            
            # Try to retrieve the specific point (game)
            points = qdrant.retrieve(
                collection_name=collection_name,
                ids=[game_id],
                with_payload=True
            )
            
            if points:
                print(f"Found game {game_id} in collection {collection_name}!")
                print(f"Game info: {points[0].payload.get('name', 'Unknown name')}")
                
                # Test scroll on this collection
                print(f"\nTesting scroll for collection {collection_name}...")
                scroll_response = qdrant.scroll(
                    collection_name=collection_name,
                    limit=2,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, next_page_offset = scroll_response
                if points:
                    print(f"Scroll returned {len(points)} points")
                    for i, point in enumerate(points):
                        print(f"Point {i+1}: ID {point.id}, Name: {point.payload.get('name', 'Unknown')}")
                else:
                    print("Scroll returned no points")
            else:
                print(f"Game {game_id} not found in collection {collection_name}")
                
        except Exception as e:
            print(f"Error with collection {collection_name}: {e}")

if __name__ == "__main__":
    test_collections() 