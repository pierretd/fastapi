#!/usr/bin/env python
"""
Script to examine game data structure in Qdrant
This helps us verify the enhanced data structure
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

# Initialize Qdrant client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def get_game_by_id(game_id):
    """Retrieve a game by its ID and print details"""
    print(f"Retrieving game with ID: {game_id}")
    
    # Get the game from Qdrant
    result = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[game_id],
        with_payload=True,
        with_vectors=True
    )
    
    if not result:
        print(f"Game with ID {game_id} not found.")
        return
    
    # Extract the point data
    point = result[0]
    
    # Print basic info
    print("\n=== Game Basic Info ===")
    print(f"ID: {point.id}")
    print(f"Name: {point.payload.get('name', 'Unknown')}")
    
    # Print all payload fields
    print("\n=== Game Payload Fields ===")
    for key, value in point.payload.items():
        # Truncate long text fields
        if isinstance(value, str) and len(value) > 100:
            print(f"{key}: {value[:100]}...")
        else:
            print(f"{key}: {value}")
    
    # Check for new enriched fields
    print("\n=== New Enriched Fields ===")
    enriched_fields = [
        'short_description', 'detailed_description', 
        'price', 'price_range', 'review_sentiment',
        'image_url', 'file_name', 'total_reviews',
        'release_year'
    ]
    
    for field in enriched_fields:
        value = point.payload.get(field)
        present = "✓ PRESENT" if value else "✗ MISSING"
        print(f"{field}: {present}")
    
    # Vector info
    print("\n=== Vector Info ===")
    vector = point.vector
    print(f"Vector size: {len(vector)}")
    print(f"First 5 dimensions: {vector[:5]}")
    
    # Save a sample of the data structure
    print("\n=== Saving to sample_game.json ===")
    sample_data = {
        "id": point.id,
        "payload": point.payload,
        "vector": vector[:10]  # Just save first 10 dimensions to keep file small
    }
    
    with open("sample_game.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print("Data saved to sample_game.json")

if __name__ == "__main__":
    # Gems of Destiny: Homeless Dwarf
    GAME_ID = 1899290
    get_game_by_id(GAME_ID) 