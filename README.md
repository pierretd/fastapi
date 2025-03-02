# Simplified Game Discovery

A streamlined game discovery application focused on finding new games based on your preferences. This application provides a simple interface for discovering games through personalized recommendations.

## Features

- **Discovery Interface**: Get game recommendations based on your likes and dislikes
- **Game Details**: View detailed information about any game
- **Similar Games**: Find games similar to ones you're interested in

## Architecture

This application uses:

- **Backend**: 
  - FastAPI for the API server
  - Qdrant for vector search
  - FastEmbed for semantic embeddings

- **Frontend**:
  - Next.js for the user interface
  - React for component-based UI
  - TailwindCSS for styling

## Setup & Installation

### Backend

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
   COLLECTION_NAME=steam_games_unique
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   CSV_FILE=path_to_your_games_data.csv
   PORT=8000
   ```
6. Upload data: `python upload_data.py`
7. Run the backend: `python main.py`

### Frontend

1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Run the frontend: `npm run dev`
5. Access the application at `http://localhost:3000`

## Usage

1. **Game Discovery**:
   - Like/dislike games to personalize recommendations
   - View recommended games based on your preferences

2. **Game Details**:
   - Click on a game to view detailed information
   - See similar games at the bottom of the details page

## Data Format

The CSV file should contain the following columns:
- `steam_appid`: Unique identifier for the game
- `name`: Name of the game
- `price`: Price of the game in USD
- `genres`: Comma-separated list of genres
- `tags`: Comma-separated list of tags
- `release_date`: Release date of the game
- `developers`: Game developers
- `publishers`: Game publishers 
- `platforms`: Supported platforms
- `short_description`: Short description of the game
- `detailed_description`: Detailed description of the game
- `header_image`: URL to the game's header image

## Deployment

### Backend

The backend can be deployed to any platform that supports Python, such as:
- Render
- Heroku
- DigitalOcean

### Frontend

The Next.js frontend can be deployed to:
- Vercel (recommended)
- Netlify
- GitHub Pages