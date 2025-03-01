# Steam Games Search API

An advanced search and recommendation API for Steam games, powered by FastAPI and vector search.

## Features

- **Search**: Find games using semantic search powered by vector embeddings
- **Recommendations**: Get similar games based on various criteria
- **Discovery**: Interactive exploration of the games catalog
- **Game Details**: Get detailed information about specific games with similar recommendations
- **Pagination**: All list-returning endpoints support pagination
- **Suggestions**: Quick search suggestions based on partial input

## API Endpoints

### Core Endpoints

- `POST /search` - Search for games by text query
- `GET /recommend/{game_id}` - Get recommendations based on a specific game
- `POST /enhanced-recommend` - Get recommendations based on multiple criteria
- `POST /discover` - Interactive discovery with feedback
- `POST /diverse-recommend` - Get diverse recommendations
- `GET /random-games` - Get random games from the collection
- `GET /game/{game_id}` - Get detailed information about a specific game

### Utility Endpoints

- `GET /suggest` - Get search suggestions based on partial input
- `GET /health` - Health check endpoint
- `GET /` - API information and endpoint listing
- `POST /admin/upload` - Administrative endpoint for data uploads

## Setup and Installation

### Prerequisites

- Python 3.8+
- Qdrant vector database
- FastAPI

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/steam-games-search-api.git
   cd steam-games-search-api
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   QDRANT_URL=http://localhost:6333
   COLLECTION_NAME=steam_games
   API_VERSION=1.0.0
   ENABLE_RATE_LIMITING=false
   DEFAULT_CACHE_DURATION=3600
   ```

### Running the API

Start the API server:
```
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the auto-generated interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Search Features

### Text Search

```
POST /search
{
  "query": "open world RPG",
  "limit": 10,
  "offset": 0,
  "use_hybrid": true
}
```

### Game Recommendations

```
GET /recommend/123456?limit=10&offset=0
```

### Enhanced Recommendations

```
POST /enhanced-recommend
{
  "positive_ids": ["123456", "789012"],
  "negative_ids": ["345678"],
  "query": "with good story",
  "limit": 10,
  "offset": 0
}
```

### Interactive Discovery

```
POST /discover
{
  "liked_ids": ["123456", "789012"],
  "disliked_ids": ["345678"],
  "limit": 9,
  "offset": 0
}
```

### Diverse Recommendations

```
POST /diverse-recommend
{
  "seed_id": "123456",
  "diversity_factor": 0.5,
  "limit": 10,
  "offset": 0
}
```

### Game Details with Similar Games

```
GET /game/123456?similar_limit=5
```

### Search Suggestions

```
GET /suggest?query=stra&limit=5
```

## Pagination

All list-returning endpoints support pagination through `limit` and `offset` parameters. The response includes pagination metadata:

```json
{
  "items": [...],
  "total": 50,
  "page": 1,
  "page_size": 10,
  "pages": 5
}
```

## Caching

The API implements caching headers to improve performance:

```
Cache-Control: public, max-age=3600
```

Different endpoints have different cache durations based on their content volatility.

## Rate Limiting

Optional rate limiting can be enabled through the `ENABLE_RATE_LIMITING` environment variable.

## Error Handling

Standardized error responses:

```json
{
  "detail": "Detailed error message",
  "code": "error_code",
  "status_code": 404,
  "path": "/endpoint/path"
}
```

## Front-end Integration

See [NEW_FEATURES.md](NEW_FEATURES.md) for detailed examples and guidance on integrating with a Next.js frontend.

## Testing

Run the tests to verify API functionality:

```
python test_recommendation_discovery.py
python test_new_features.py
```

## License

MIT