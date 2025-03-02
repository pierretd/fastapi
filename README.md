# Game Discovery API

A simplified API for game discovery using dense vector search. This application provides a streamlined experience focused on efficient discovery of games through semantic similarity.

## Features

- **Dense Vector Search**: Find games using semantic search through vector embeddings
- **Discovery**: Get personalized game recommendations based on user preferences
- **Context-based Discovery**: Find similar games based on a specific game

## Architecture

This application uses:

- **FastAPI**: Modern, fast web framework for building APIs
- **Qdrant**: Vector database for storing and searching game embeddings
- **FastEmbed**: Embedding model library for creating dense vector representations

## API Endpoints

### Search

- `GET /search`: Search for games using a text query
  - Parameters: 
    - `query`: Search term or game ID
    - `limit`: Maximum number of results to return

### Game Details

- `GET /game/{game_id}`: Get detailed information about a specific game
  - Parameters:
    - `game_id`: ID of the game to retrieve

### Discovery

- `POST /discovery-games`: Get personalized game recommendations based on likes/dislikes
  - Request body:
    ```json
    {
      "positive_ids": ["12345", "67890"], // Games the user likes
      "negative_ids": ["54321"],          // Games the user dislikes
      "excluded_ids": ["11111"],          // Games to exclude from results
      "limit": 9                          // Number of results to return
    }
    ```

- `GET /discovery-context/{game_id}`: Get games similar to a specific game
  - Parameters:
    - `game_id`: ID of the game to find similar games for
    - `limit`: Maximum number of results to return
    - `excluded_ids`: Comma-separated list of game IDs to exclude

## Setup & Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with the following variables:
   ```
   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key
   COLLECTION_NAME=your_collection_name
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   CSV_FILE=path_to_your_games_data.csv
   PORT=8000
   ```
6. Run the application: `python main.py`

## Data Format

The CSV file should contain the following columns:
- `steam_appid`: Unique identifier for the game
- `name`: Name of the game
- `price`: Price of the game in USD
- `genres`: Comma-separated list of genres
- `tags`: Comma-separated list of tags
- `release_date`: Release date of the game
- `developers`: Game developers
- `platforms`: Supported platforms
- `short_description`: Short description of the game
- `detailed_description`: Detailed description of the game

## Example Usage

### Search for games

```bash
curl -X GET "http://localhost:8000/search?query=open%20world%20RPG&limit=5"
```

### Get game details

```bash
curl -X GET "http://localhost:8000/game/123456"
```

### Get discovery recommendations

```bash
curl -X POST "http://localhost:8000/discovery-games" \
     -H "Content-Type: application/json" \
     -d '{"positive_ids": ["123", "456"], "limit": 5}'
```

### Get similar games

```bash
curl -X GET "http://localhost:8000/discovery-context/123456?limit=5"
```