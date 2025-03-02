from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Depends, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import BaseModel, Field
import os
import uvicorn
from dotenv import load_dotenv
import time
import logging
from contextlib import asynccontextmanager

# Import from the search package
try:
    from search import (
        initialize_collection, 
        search_games, 
        get_game_by_id,
        get_discovery_context
    )
except ImportError as e:
    logging.error(f"Error importing from search package: {e}")
    # Define placeholder functions to allow the app to start even if imports fail
    def initialize_collection():
        logging.error("Search functionality not available - initialize_collection is a placeholder")
        return
    
    def search_games(query, limit=10, offset=0):
        logging.error("Search functionality not available - search_games is a placeholder")
        return []
    
    def get_game_by_id(game_id):
        logging.error("Search functionality not available - get_game_by_id is a placeholder")
        return None
    
    def get_discovery_context(game_id, limit=9, excluded_ids=None):
        logging.error("Search functionality not available - get_discovery_context is a placeholder")
        return []

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API configuration
API_VERSION = os.getenv("API_VERSION", "1.0.0")
DEFAULT_CACHE_DURATION = int(os.getenv("DEFAULT_CACHE_DURATION", "3600"))  # 1 hour in seconds
IS_RENDER = os.getenv("RENDER", "false").lower() == "true"

# Define our startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the vector search collection
    logger.info("Starting up Steam Games Search API...")
    try:
        initialize_collection()
        logger.info("Collection initialized and ready")
    except Exception as e:
        logger.error(f"Failed to initialize collection: {e}")
        logger.info("Continuing startup despite initialization error")
    yield
    # Shutdown: Any cleanup code would go here
    logger.info("Shutting down Steam Games Search API...")

# Initialize FastAPI app
app = FastAPI(
    title="Steam Games Search API",
    description="API for searching and discovering Steam games using vector search",
    version=API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in this simplified version
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom response headers middleware
@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    
    # Add cache control headers (except for admin endpoints)
    if not request.url.path.startswith("/admin"):
        response.headers["Cache-Control"] = f"public, max-age={DEFAULT_CACHE_DURATION}"
    
    return response

# Define request/response models
class SearchRequest(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

class GameSearchResponse(BaseModel):
    id: str
    score: float
    payload: Dict[str, Any]

# Exception handler for all exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Steam Games Search API",
        "version": API_VERSION,
        "environment": "Render" if IS_RENDER else "Development",
        "endpoints": [
            "/search - Search for games",
            "/game/{game_id} - Get game details",
            "/discovery-context/{game_id} - Get similar games"
        ]
    }

# Health check endpoint (important for Render)
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}

# Search endpoint
@app.post("/search", response_model=List[GameSearchResponse])
async def search(request: SearchRequest):
    """
    Search for games using a text query.
    Returns a list of games matching the search criteria.
    """
    try:
        results = search_games(request.query, limit=request.limit, offset=request.offset)
        if not results and isinstance(results, list):
            return []
        return results
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# Game details endpoint
@app.get("/game/{game_id}", response_model=Dict[str, Any])
async def get_game(game_id: str):
    """
    Get detailed information about a specific game by ID.
    """
    try:
        game = get_game_by_id(game_id)
        if not game:
            raise HTTPException(status_code=404, detail=f"Game with ID {game_id} not found")
        return game
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game details: {str(e)}")

# Similar games endpoint (for game detail page)
@app.get("/discovery-context/{game_id}", response_model=List[GameSearchResponse])
async def get_similar_games(
    game_id: str,
    limit: int = Query(9, ge=1, le=100),
    excluded_ids: str = Query("", description="Comma-separated list of IDs to exclude")
):
    """
    Get games similar to a specific game.
    """
    try:
        excluded = excluded_ids.split(",") if excluded_ids else []
        results = get_discovery_context(game_id, limit=limit, excluded_ids=excluded)
        if not results and isinstance(results, list):
            return []
        return results
    except Exception as e:
        logger.error(f"Error getting similar games: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving similar games: {str(e)}")

# Run the application (only in development)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)