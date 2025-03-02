# Game Discovery API

A simplified API for game discovery using dense vector search. This application provides a streamlined experience focused on efficient discovery of games through semantic similarity.

## Features

- **Dense Vector Search**: Find games using semantic search through vector embeddings
- **Game Details**: Get detailed information about specific games
- **Similar Games**: Find games similar to ones you already enjoy

## Deploying on Render

### Quick Deploy

The easiest way to deploy is using Render's Blueprint feature:

1. Fork this repository to your GitHub/GitLab account
2. In your Render dashboard, click "New" → "Blueprint"
3. Connect your repository
4. Set the required environment variables:
   - `QDRANT_URL`: Your Qdrant service URL
   - `QDRANT_API_KEY`: Your Qdrant API key

### Manual Setup

If you prefer to set up services manually:

#### Backend API Service

1. Create a new Web Service on Render
2. Configure:
   - **Name**: `game-discovery-api`
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
   - **Environment Variables**: See `.env.example` for required variables

#### Frontend Service

1. Create another Web Service
2. Configure:
   - **Name**: `game-discovery-frontend`
   - **Environment**: Node
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `cd frontend && npm start`
   - **Environment Variables**:
     - `NEXT_PUBLIC_API_URL`: URL of your backend API service
     - `NODE_ENV`: `production`

## Local Development

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies:
   ```
   pip install -r requirements.txt
   cd frontend && npm install
   ```
4. Run the application:
   ```
   ./run-app.sh
   ```

## API Endpoints

- `POST /search`: Search for games using a text query
- `GET /game/{game_id}`: Get detailed information about a specific game
- `GET /discovery-context/{game_id}`: Get games similar to a specific game

## Data Requirements

This application requires:
1. A Qdrant vector database instance (cloud or self-hosted)
2. Game data uploaded to a Qdrant collection

See `upload_data.py` for details on how to upload game data.