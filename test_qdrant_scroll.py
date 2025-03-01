import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import json

# Load environment variables
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "steam_games_with_sparse_dense")

def test_qdrant_scroll():
    """Test the Qdrant scroll API to understand its response structure"""
    print(f"Connecting to Qdrant at {QDRANT_URL}")
    print(f"Using collection: {COLLECTION_NAME}")
    
    # Initialize Qdrant client
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Check if collection exists
    collections = qdrant.get_collections()
    print(f"Available collections: {[c.name for c in collections.collections]}")
    
    if COLLECTION_NAME not in [c.name for c in collections.collections]:
        print(f"Collection {COLLECTION_NAME} not found!")
        return
    
    # Get collection info
    collection_info = qdrant.get_collection(COLLECTION_NAME)
    print(f"Collection info: {collection_info}")
    print(f"Points count: {collection_info.points_count}")
    
    # Test scroll API
    print("\nTesting scroll API...")
    try:
        scroll_response = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        print(f"Scroll response type: {type(scroll_response)}")
        print(f"Scroll response length: {len(scroll_response)}")
        
        # Print each element in the tuple
        for i, element in enumerate(scroll_response):
            print(f"\nTuple element {i}:")
            print(f"Type: {type(element)}")
            
            if isinstance(element, list):
                print(f"List length: {len(element)}")
                if element and len(element) > 0:
                    print(f"First item type: {type(element[0])}")
                    print(f"First item: {element[0]}")
            else:
                print(f"Value: {element}")
        
        # Try to unpack the tuple
        if len(scroll_response) >= 2:
            points, next_page_offset = scroll_response
            print("\nUnpacked tuple:")
            print(f"Points type: {type(points)}")
            print(f"Points length: {len(points)}")
            print(f"Next page offset: {next_page_offset}")
            
            if points and len(points) > 0:
                print("\nFirst point details:")
                first_point = points[0]
                print(f"Point type: {type(first_point)}")
                print(f"Point attributes: {dir(first_point)}")
                
                # Check for id
                if hasattr(first_point, 'id'):
                    print(f"ID: {first_point.id}")
                
                # Check for payload
                if hasattr(first_point, 'payload'):
                    print(f"Payload type: {type(first_point.payload)}")
                    print(f"Payload keys: {first_point.payload.keys() if first_point.payload else 'Empty payload'}")
                    print(f"Payload sample: {json.dumps(dict(list(first_point.payload.items())[:3])) if first_point.payload else 'Empty payload'}")
                
                # Check for vector
                if hasattr(first_point, 'vector'):
                    print(f"Vector available: {first_point.vector is not None}")
                
        # Format results like in the search_games function
        if len(scroll_response) >= 1:
            points = scroll_response[0]
            print("\nFormatted results:")
            results = []
            for point in points:
                result = {
                    "id": str(point.id) if hasattr(point, 'id') else "unknown",
                    "payload": point.payload if hasattr(point, 'payload') else {},
                    "score": 1.0  # Default score for random games
                }
                results.append(result)
                
            print(f"Number of formatted results: {len(results)}")
            if results:
                print(f"First result: {json.dumps(results[0], default=str)}")
            
    except Exception as e:
        print(f"Error testing scroll API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qdrant_scroll() 