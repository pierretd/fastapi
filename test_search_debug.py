import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from fastembed import TextEmbedding
import numpy as np

# Load environment variables
load_dotenv()

# Get env vars
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "steam_games_unique_20250302"  # Our new collection

print(f"Connecting to Qdrant at {QDRANT_URL}")
print(f"Using collection: {COLLECTION_NAME}")

# Initialize Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Check if collection exists and get info
try:
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"Collection info: status={collection_info.status} optimizer_status={collection_info.optimizer_status}")
    print(f" vectors_count={collection_info.vectors_count} indexed_vectors_count={collection_info.indexed_vectors_count} points_count={collection_info.points_count} segments_count={collection_info.segments_count} config={collection_info.config} payload_schema={collection_info.payload_schema}")
    
    # Get points count
    points_count = client.count(collection_name=COLLECTION_NAME)
    print(f"Points count: {points_count.count}")
    
    # Get vectors config
    vectors_config = collection_info.config.params.vectors
    print(f"Vectors config: {vectors_config}")
except Exception as e:
    print(f"Error getting collection info: {str(e)}")

# Query text
query_text = "Gems of Destiny"
print(f"Generating embedding for query: '{query_text}'")

# Model for embedding
try:
    # Use fastembed instead of sentence_transformers
    embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    embeddings = list(embedder.embed([query_text]))
    vector = embeddings[0].tolist() if embeddings else []
    
    # Test direct vector search
    print("\n=== Testing Direct Vector Search ===")
    try:
        # Try with named vector
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector={"fast-bge-small-en": vector},
            limit=3,
            with_payload=True
        )
        print(f"Named vector search results: {len(results)} results")
        for r in results:
            print(f"  - {r.id}: {r.payload.get('name', 'Unknown')} (score: {r.score})")
    except Exception as e:
        print(f"Error with named vector search: {str(e)}")
        print(f"Raw response content:\n{getattr(e, 'response', {}).get('content', 'No response content')}")
        
        # Try without named vector as fallback
        try:
            print("\n=== Testing Direct Vector Search (Unnamed) ===")
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=3,
                with_payload=True
            )
            print(f"Direct vector search results: {len(results)} results")
            for r in results:
                print(f"  - {r.id}: {r.payload.get('name', 'Unknown')} (score: {r.score})")
        except Exception as e2:
            print(f"Error with direct vector search: {str(e2)}")
            print(f"Raw response content:\n{getattr(e2, 'response', {}).get('content', 'No response content')}")
except Exception as e:
    print(f"Error with embedding: {str(e)}")

# List all collections
print("\n=== Listing Available Collections ===")
try:
    collections = client.get_collections()
    print(f"Available collections: {collections.collections}")
except Exception as e:
    print(f"Error listing collections: {str(e)}")

# Test get point
print("\n=== Testing Get Point ===")
try:
    print(f"Retrieving with int ID: 1899290")
    result = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[1899290],
        with_payload=True
    )
    print(f"Retrieved game by int ID: {result}")
except Exception as e:
    print(f"Error retrieving point: {str(e)}")
    # Try string ID
    try:
        print(f"Trying with string ID: '1899290'")
        result = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=["1899290"],
            with_payload=True
        )
        print(f"Retrieved game by string ID: {result}")
    except Exception as e2:
        print(f"Error retrieving point with string ID: {str(e2)}") 