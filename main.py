from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
import uvicorn
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager

from search import (
    initialize_collection,
    get_game_by_id,
    get_discovery_games,
    get_discovery_context
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the collection
    await initialize_collection()
    yield
    # Shutdown: No special cleanup needed

# Initialize FastAPI app
app = FastAPI(
    title="Simplified Game Discovery API",
    description="A minimal API for game discovery and details",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class DiscoveryRequest(BaseModel):
    positive_ids: Optional[List[str]] = Field(default=[], description="List of game IDs the user likes")
    negative_ids: Optional[List[str]] = Field(default=[], description="List of game IDs the user dislikes")
    excluded_ids: Optional[List[str]] = Field(default=[], description="List of game IDs to exclude from results")
    limit: Optional[int] = Field(default=9, description="Maximum number of results to return")

# Routes
@app.get("/")
async def root():
    """Root endpoint providing basic API information."""
    return {
        "message": "Simplified Game Discovery API",
        "endpoints": [
            "/game/{game_id}",
            "/discovery-games",
            "/discovery-context/{game_id}"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}

@app.get("/game/{game_id}")
async def get_game(game_id: str):
    """
    Get detailed information about a specific game by ID.
    
    Args:
        game_id: The unique identifier of the game
        
    Returns:
        Game details or 404 if not found
    """
    game = get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game with ID {game_id} not found")
    return game

@app.post("/discovery-games")
async def discovery_games(request: DiscoveryRequest):
    """
    Get personalized game recommendations based on likes/dislikes.
    
    Args:
        request: The discovery request containing positive and negative IDs
        
    Returns:
        List of recommended games
    """
    try:
        games = get_discovery_games(
            positive_ids=request.positive_ids,
            negative_ids=request.negative_ids,
            excluded_ids=request.excluded_ids,
            limit=request.limit
        )
        return games
    except Exception as e:
        logger.error(f"Error in discovery games: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/discovery-context/{game_id}")
async def discovery_context(
    game_id: str,
    limit: int = 9,
    excluded_ids: str = ""
):
    """
    Get games similar to a specific game.
    
    Args:
        game_id: ID of the game to find similar games for
        limit: Maximum number of results to return
        excluded_ids: Comma-separated list of game IDs to exclude
        
    Returns:
        List of similar games
    """
    excluded = excluded_ids.split(",") if excluded_ids else []
    try:
        games = get_discovery_context(
            game_id=game_id,
            limit=limit,
            excluded_ids=excluded
        )
        return games
    except Exception as e:
        logger.error(f"Error in discovery context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)