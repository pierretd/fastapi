# Steam Games Search API Documentation

This API provides search and recommendation functionality for Steam games, including enhanced recommendation features, interactive discovery, and diverse recommendations.

## Base URL

```
http://localhost:8000
```

## API Endpoints

### 1. Root Endpoint

- **URL:** `/`
- **Method:** `GET`
- **Description:** Shows API information and available endpoints
- **Response:**
  ```json
  {
    "message": "Steam Games Search API is running",
    "endpoints": [
      "/search",
      "/recommend/{game_id}",
      "/enhanced-recommend",
      "/discover",
      "/diverse-recommend",
      "/random-games",
      "/admin/upload"
    ]
  }
  ```

### 2. Search for Games

- **URL:** `/search`
- **Method:** `POST`
- **Description:** Search for games using a text query
- **Request Body:**
  ```json
  {
    "query": "open world RPG with dragons",
    "limit": 10,
    "use_hybrid": true
  }
  ```
  - `query` (string, required): The search query text
  - `limit` (integer, optional): Maximum number of results to return (default: 10)
  - `use_hybrid` (boolean, optional): Whether to use hybrid search combining sparse and dense vectors (default: true)

- **Response:** List of game objects:
  ```json
  [
    {
      "id": "1234567",
      "score": 0.85,
      "payload": {
        "name": "Game Title",
        "genres": ["RPG", "Open World"],
        "price": 29.99,
        "release_date": "2023-01-15",
        "short_description": "An epic open world RPG...",
        "detailed_description": "Full description of the game..."
      }
    },
    ...
  ]
  ```

### 3. Game Recommendations

- **URL:** `/recommend/{game_id}`
- **Method:** `GET`
- **Description:** Get recommendations based on a specific game
- **URL Parameters:**
  - `game_id` (string, required): The Steam App ID of the game
  - `limit` (integer, optional): Maximum number of recommendations to return (default: 10)

- **Response:** List of game objects (same format as search results)

### 4. Enhanced Recommendations

- **URL:** `/enhanced-recommend`
- **Method:** `POST`
- **Description:** Get personalized recommendations based on liked games, disliked games, and an optional query
- **Request Body:**
  ```json
  {
    "positive_ids": ["1234567", "2345678"],
    "negative_ids": ["3456789"],
    "query": "strategy games with building",
    "limit": 10
  }
  ```
  - `positive_ids` (array of strings, optional): List of game IDs the user likes
  - `negative_ids` (array of strings, optional): List of game IDs the user dislikes
  - `query` (string, optional): Additional search query to guide recommendations
  - `limit` (integer, optional): Maximum number of recommendations to return (default: 10)

- **Response:** List of game objects (same format as search results)

### 5. Interactive Discovery

- **URL:** `/discover`
- **Method:** `POST`
- **Description:** Get game recommendations for interactive discovery, with feedback from user preferences
- **Request Body:**
  ```json
  {
    "liked_ids": ["1234567", "2345678"],
    "disliked_ids": ["3456789"],
    "limit": 9
  }
  ```
  - `liked_ids` (array of strings, optional): List of game IDs the user has liked
  - `disliked_ids` (array of strings, optional): List of game IDs the user has disliked
  - `limit` (integer, optional): Maximum number of games to return (default: 9)

- **Response:** List of game objects (same format as search results)

### 6. Diverse Recommendations

- **URL:** `/diverse-recommend`
- **Method:** `POST`
- **Description:** Get diverse recommendations based on a seed game, with adjustable diversity
- **Request Body:**
  ```json
  {
    "seed_id": "1234567",
    "diversity_factor": 0.5,
    "limit": 10
  }
  ```
  - `seed_id` (string, required): The game ID to base recommendations on
  - `diversity_factor` (float, optional): Value between 0 and 1 that controls diversity (0 = similar to seed, 1 = maximally diverse, default: 0.5)
  - `limit` (integer, optional): Maximum number of recommendations to return (default: 10)

- **Response:** List of game objects (same format as search results)

### 7. Random Games

- **URL:** `/random-games`
- **Method:** `GET`
- **Description:** Get random games from the collection
- **Query Parameters:**
  - `limit` (integer, optional): Number of random games to return (default: 9)

- **Response:** List of game objects (same format as search results)

### 8. Upload Data (Admin)

- **URL:** `/admin/upload`
- **Method:** `POST`
- **Description:** Upload game data to initialize or update the collection (admin only)
- **Form Data:**
  - `file` (file, required): CSV file containing game data
  - `collection_name` (string, required): Name of the collection to create or update
  - `force_recreate` (boolean, optional): Whether to force recreation of the collection if it exists (default: false)

- **Response:**
  ```json
  {
    "message": "Collection {collection_name} initialized successfully"
  }
  ```

## Usage Examples

### Search for Games

```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "open world RPG with dragons",
        "limit": 10
    }
)

results = response.json()
print(f"Found {len(results)} games matching your query:")
for i, game in enumerate(results):
    print(f"{i+1}. {game['payload']['name']} (Score: {game['score']:.4f})")
```

### Get Enhanced Recommendations

```python
import requests

response = requests.post(
    "http://localhost:8000/enhanced-recommend",
    json={
        "positive_ids": ["1234567", "2345678"],  # Games the user likes
        "negative_ids": ["3456789"],            # Games the user dislikes
        "query": "strategy games with building", # Additional context
        "limit": 10
    }
)

results = response.json()
print(f"Found {len(results)} personalized recommendations:")
for i, game in enumerate(results):
    print(f"{i+1}. {game['payload']['name']} (Score: {game['score']:.4f})")
```

### Interactive Discovery Example

```python
import requests

# Initial discovery (no feedback yet)
response = requests.post(
    "http://localhost:8000/discover",
    json={"limit": 9}
)

games = response.json()
print("Here are some games to explore:")
for i, game in enumerate(games):
    print(f"{i+1}. {game['payload']['name']}")

# User provides feedback
liked_ids = [games[0]["id"], games[2]["id"]]  # User liked first and third game
disliked_ids = [games[1]["id"]]              # User disliked second game

# Get updated recommendations based on feedback
response = requests.post(
    "http://localhost:8000/discover",
    json={
        "liked_ids": liked_ids,
        "disliked_ids": disliked_ids,
        "limit": 9
    }
)

updated_games = response.json()
print("\nBased on your feedback, you might like these games:")
for i, game in enumerate(updated_games):
    print(f"{i+1}. {game['payload']['name']}")
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

Error responses include a detail message explaining the error:

```json
{
  "detail": "Error message explaining what went wrong"
}
``` 