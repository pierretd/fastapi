from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Depends, UploadFile, File, Form, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import BaseModel, Field
import os
import uvicorn
from dotenv import load_dotenv
import time
from datetime import timedelta
import asyncio
import logging
from contextlib import asynccontextmanager
import httpx

# Import the ENHANCED search module with aliasing for backward compatibility
# This imports search_enhanced.py but allows it to be used as 'search'
import search_enhanced 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API configuration
API_VERSION = os.getenv("API_VERSION", "1.0.0")
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
DEFAULT_CACHE_DURATION = int(os.getenv("DEFAULT_CACHE_DURATION", "3600"))  # 1 hour in seconds
KEEPALIVE_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL", "240"))  # 4 minutes in seconds (less than 5 min timeout)

# Background task for keep-alive
async def keepalive_task():
    """Background task that pings the health endpoint to keep the server alive."""
    # Get the API host from environment or default to localhost
    is_render = os.getenv("RENDER", "false").lower() == "true"
    port = os.getenv("PORT", "8000")
    
    # If running on Render, use localhost with the correct port
    if is_render:
        # On Render, services are available internally at localhost with the assigned PORT
        api_host = f"http://localhost:{port}"
    else:
        # For local development or other environments
        api_host = os.getenv("API_HOST", f"http://localhost:{port}")
    
    # URL to ping (health endpoint)
    health_url = f"{api_host}/health"
    
    while True:
        try:
            logger.info(f"Running keep-alive task, pinging {health_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url)
                logger.info(f"Keep-alive ping status: {response.status_code}")
        except Exception as e:
            logger.error(f"Keep-alive task failed: {str(e)}")
        
        # Sleep for the specified interval
        await asyncio.sleep(KEEPALIVE_INTERVAL)

# Data initialization task
async def initialize_data():
    """Initialize the Qdrant collection with data if it doesn't exist"""
    try:
        logger.info("Checking if data initialization is needed...")
        
        # Import functions from our upload script
        from upload_data import check_collection_exists, create_collection, upload_data
        
        # Check if collection exists and has data
        if not check_collection_exists():
            logger.info("Collection doesn't exist or is empty. Creating and uploading data...")
            
            # Create collection
            if create_collection():
                logger.info("Collection created successfully.")
                
                # Upload data
                if upload_data():
                    logger.info("Data uploaded successfully.")
                else:
                    logger.error("Failed to upload data.")
            else:
                logger.error("Failed to create collection.")
        else:
            logger.info("Collection already exists with data. No initialization needed.")
            
    except Exception as e:
        logger.error(f"Data initialization failed: {str(e)}")

# LifeSpan context to start background tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize data when the app starts
    await initialize_data()
    logger.info("Data initialization completed")
    
    # Start the keepalive task when the app starts
    keepalive_task_obj = asyncio.create_task(keepalive_task())
    logger.info("Started keep-alive background task")
    
    yield  # This is where the app runs
    
    # Cancel the task when the app is shutting down
    keepalive_task_obj.cancel()
    try:
        await keepalive_task_obj
    except asyncio.CancelledError:
        logger.info("Keep-alive task cancelled")

# Initialize FastAPI with lifespan
app = FastAPI(
    title="Steam Games Search API",
    description="API for searching and recommending Steam games using vector embeddings",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom rate limiter (simple implementation)
if ENABLE_RATE_LIMITING:
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class RateLimitMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, rate_limit_per_minute=60):
            super().__init__(app)
            self.rate_limit = rate_limit_per_minute
            self.requests = {}
            
        async def dispatch(self, request, call_next):
            client_ip = request.client.host
            current_time = time.time()
            
            # Clean up old entries
            self.requests = {ip: times for ip, times in self.requests.items() 
                            if any(t > current_time - 60 for t in times)}
            
            # Check if client has exceeded rate limit
            if client_ip in self.requests:
                times = self.requests[client_ip]
                times = [t for t in times if t > current_time - 60]
                
                if len(times) >= self.rate_limit:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Please try again later."}
                    )
                
                self.requests[client_ip] = times + [current_time]
            else:
                self.requests[client_ip] = [current_time]
            
            return await call_next(request)
    
    app.add_middleware(RateLimitMiddleware)

# Models for request/response
class SearchResponse(BaseModel):
    id: str = Field(..., description="Steam App ID of the game")
    score: float = Field(..., description="Relevance score from 0 to 1")
    payload: Dict[str, Any] = Field(..., description="Game metadata")

class RecommendationResponse(BaseModel):
    id: str = Field(..., description="Steam App ID of the game")
    score: float = Field(..., description="Similarity score from 0 to 1")
    payload: Dict[str, Any] = Field(..., description="Game metadata")

class GameDetail(BaseModel):
    id: str = Field(..., description="Steam App ID of the game")
    name: str = Field(..., description="Name of the game")
    price: float = Field(..., description="Price of the game in USD")
    genres: str = Field(..., description="Comma-separated list of genres")
    tags: Optional[str] = Field(None, description="Comma-separated list of tags")
    release_date: str = Field(..., description="Release date of the game")
    developers: str = Field(..., description="Game developers")
    platforms: str = Field(..., description="Supported platforms")
    short_description: str = Field(..., description="Short description of the game")
    detailed_description: str = Field(..., description="Detailed description of the game")
    similar_games: List[RecommendationResponse] = Field([], description="Similar games recommendations")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code for programmatic handling")
    status_code: int = Field(..., description="HTTP status code")
    path: str = Field(..., description="Request path that caused the error")

class PaginatedResponse(BaseModel):
    items: List[Any] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

# Additional models for new endpoints
class SearchRequest(BaseModel):
    query: str
    limit: int = 12
    offset: int = 0
    use_hybrid: bool = True
    use_sparse: bool = False
    use_dense: bool = False

class RecommendationRequest(BaseModel):
    game_id: str = Field(..., description="Steam App ID of the game")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip (for pagination)")

class EnhancedRecommendationRequest(BaseModel):
    positive_ids: Optional[List[str]] = Field(None, description="List of game IDs the user likes")
    negative_ids: Optional[List[str]] = Field(None, description="List of game IDs the user dislikes")
    query: Optional[str] = Field(None, description="Optional text query for additional context")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip (for pagination)")

class DiscoveryRequest(BaseModel):
    liked_ids: Optional[List[str]] = Field(None, description="List of game IDs the user likes")
    disliked_ids: Optional[List[str]] = Field(None, description="List of game IDs the user dislikes")
    limit: int = Field(9, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip (for pagination)")

class DiscoveryPreferencesRequest(BaseModel):
    liked_ids: Optional[List[str]] = Field(None, description="List of game IDs the user likes")
    disliked_ids: Optional[List[str]] = Field(None, description="List of game IDs the user dislikes")
    action: str = Field(..., description="Action to perform: 'like', 'dislike', 'unlike', 'undislike', 'refresh', 'reset'")
    game_id: Optional[str] = Field(None, description="Game ID for the action (required for like, dislike, unlike, undislike)")
    limit: int = Field(9, description="Number of games to return in the response")

class DiverseRecommendationRequest(BaseModel):
    seed_id: str = Field(..., description="Steam App ID of the seed game")
    diversity_factor: float = Field(0.5, description="Factor controlling diversity (0=similar, 1=diverse)")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip (for pagination)")

class SuggestionRequest(BaseModel):
    query: str = Field(..., description="Partial query text to get suggestions for")
    limit: int = Field(5, description="Maximum number of suggestions to return")

class DiscoveryGamesRequest(BaseModel):
    positive_ids: Optional[List[str]] = Field(None, description="List of game IDs the user likes")
    negative_ids: Optional[List[str]] = Field(None, description="List of game IDs the user dislikes")
    excluded_ids: Optional[List[str]] = Field(None, description="List of game IDs to exclude from results")
    limit: int = Field(9, description="Maximum number of games to return")

# Custom exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail=str(exc),
            code="internal_server_error",
            status_code=500,
            path=request.url.path
        ).dict()
    )

# Helper for adding cache headers
def add_cache_headers(response: Response, duration_seconds: int = DEFAULT_CACHE_DURATION):
    response.headers["Cache-Control"] = f"public, max-age={duration_seconds}"
    return response

@app.get("/", tags=["General"])
async def root(response: Response):
    """API root endpoint that provides information about available endpoints."""
    result = {
        "message": "Steam Games Search API is running",
        "version": API_VERSION,
        "endpoints": [
            {"path": "/search", "description": "Search for games using text query"},
            {"path": "/recommend/{game_id}", "description": "Get game recommendations based on a specific game"},
            {"path": "/enhanced-recommend", "description": "Get enhanced recommendations with likes, dislikes, and queries"},
            {"path": "/discover", "description": "Interactive discovery with feedback"},
            {"path": "/diverse-recommend", "description": "Get diverse recommendations balancing similarity and variety"},
            {"path": "/random-games", "description": "Get random games from the collection"},
            {"path": "/game/{game_id}", "description": "Get detailed information about a specific game"},
            {"path": "/suggest", "description": "Get search suggestions based on partial input"},
            {"path": "/health", "description": "Health check endpoint"},
            {"path": "/admin/upload", "description": "Admin endpoint to trigger data upload"},
        ]
    }
    return add_cache_headers(response, 3600), result

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/search", response_model=PaginatedResponse, tags=["Search"])
async def search(request: SearchRequest, response: Response):
    """
    Search for games using text query.
    
    This endpoint uses vector search to find games matching the query.
    Multiple search methods are supported:
    - Hybrid search (default): Combines dense and sparse vectors
    - Dense vector search: Uses embeddings for semantic search
    - Sparse vector search: Uses keyword-based search
    
    Results are paginated for easier frontend integration.
    """
    try:
        # Determine which search method to use
        use_hybrid = request.use_hybrid
        use_sparse = request.use_sparse
        use_dense = request.use_dense
        
        # Default to hybrid search if no specific method is selected
        if not (use_hybrid or use_sparse or use_dense):
            use_hybrid = True
        
        # Call the search_games function from the search module
        results = search_enhanced.search_games(
            request.query, 
            request.limit + request.offset, 
            use_hybrid=use_hybrid,
            use_sparse=use_sparse,
            use_dense=use_dense
        )
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[request.offset:request.offset + request.limit]
        
        # Convert to response model
        response_items = []
        for hit in paginated_results:
            response_items.append(
                SearchResponse(
                    id=hit["id"],
                    score=hit["score"],
                    payload=hit["payload"]
                )
            )
        
        # Calculate pagination info
        page_size = request.limit
        current_page = (request.offset // page_size) + 1 if page_size > 0 else 1
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 1
        
        # Create response object
        result = PaginatedResponse(
            items=response_items,
            total=total_results,
            page=current_page,
            page_size=page_size,
            pages=total_pages
        )
        
        # Add cache headers (short duration for search results)
        add_cache_headers(response, 300)
        
        # Just return the result object
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/recommend/{game_id}", response_model=PaginatedResponse, tags=["Recommendations"])
async def recommend(
    game_id: str, 
    limit: int = 10, 
    offset: int = 0,
    response: Response = None
):
    """
    Get game recommendations based on a specific game ID.
    
    This endpoint uses vector similarity to find games similar to the provided game.
    Results are paginated for easier frontend integration.
    """
    try:
        results = search_enhanced.get_game_recommendations(game_id, limit + offset)
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[offset:offset + limit]
        
        # Convert to response model
        response_items = []
        for hit in paginated_results:
            response_items.append(
                RecommendationResponse(
                    id=hit["id"],
                    score=hit["score"],
                    payload=hit["payload"]
                )
            )
        
        # Calculate pagination info
        page_size = limit
        current_page = (offset // page_size) + 1 if page_size > 0 else 1
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 1
        
        result = PaginatedResponse(
            items=response_items,
            total=total_results,
            page=current_page,
            page_size=page_size,
            pages=total_pages
        )
        
        # Add cache headers (1 hour for recommendations)
        add_cache_headers(response, 3600)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/admin/upload", tags=["Admin"])
async def upload_data(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    force_recreate: bool = Form(False)
):
    """
    Administrative endpoint to trigger data upload to Qdrant.
    
    This will create the collection if it doesn't exist and upload all game data.
    """
    try:
        # Save uploaded file temporarily
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Initialize collection
        search_enhanced.initialize_collection(file_path, collection_name, force_recreate)
        
        # Remove temporary file
        os.remove(file_path)
        
        return {"message": f"Collection {collection_name} initialized successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing collection: {str(e)}"
        )

@app.post("/enhanced-recommend", response_model=PaginatedResponse, tags=["Recommendations"])
async def enhanced_recommend(request: EnhancedRecommendationRequest, response: Response):
    """
    Get enhanced game recommendations based on multiple inputs.
    
    This endpoint allows specifying both liked and disliked games, as well as an optional text query.
    Results are paginated for easier frontend integration.
    """
    try:
        results = search_enhanced.get_enhanced_recommendations(
            positive_ids=request.positive_ids,
            negative_ids=request.negative_ids,
            query=request.query,
            limit=request.limit + request.offset
        )
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[request.offset:request.offset + request.limit]
        
        # Convert to response model
        response_items = []
        for hit in paginated_results:
            response_items.append(
                RecommendationResponse(
                    id=hit["id"],
                    score=hit["score"],
                    payload=hit["payload"]
                )
            )
        
        # Calculate pagination info
        page_size = request.limit
        current_page = (request.offset // page_size) + 1 if page_size > 0 else 1
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 1
        
        result = PaginatedResponse(
            items=response_items,
            total=total_results,
            page=current_page,
            page_size=page_size,
            pages=total_pages
        )
        
        # Add cache headers (short duration for enhanced recommendations)
        add_cache_headers(response, 300)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/discover", response_model=PaginatedResponse, tags=["Discovery"])
async def discover(request: DiscoveryRequest, response: Response):
    """
    Get interactive discovery recommendations based on user feedback.
    
    This endpoint presents games and updates recommendations as users provide feedback.
    Results are paginated for easier frontend integration.
    """
    try:
        results = search_enhanced.get_discovery_recommendations(
            liked_ids=request.liked_ids,
            disliked_ids=request.disliked_ids,
            limit=request.limit + request.offset
        )
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[request.offset:request.offset + request.limit]
        
        # Convert to response model
        response_items = []
        for hit in paginated_results:
            response_items.append(
                RecommendationResponse(
                    id=hit["id"],
                    score=hit["score"],
                    payload=hit["payload"]
                )
            )
        
        # Calculate pagination info
        page_size = request.limit
        current_page = (request.offset // page_size) + 1 if page_size > 0 else 1
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 1
        
        result = PaginatedResponse(
            items=response_items,
            total=total_results,
            page=current_page,
            page_size=page_size,
            pages=total_pages
        )
        
        # Add cache headers (short duration for discovery results)
        add_cache_headers(response, 300)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/diverse-recommend", response_model=PaginatedResponse, tags=["Recommendations"])
async def diverse_recommend(request: DiverseRecommendationRequest, response: Response):
    """
    Get diverse game recommendations that balance similarity with diversity.
    
    This endpoint provides recommendations with controlled diversity based on a seed game.
    Results are paginated for easier frontend integration.
    """
    try:
        results = search_enhanced.get_diverse_recommendations(
            seed_id=request.seed_id,
            diversity_factor=request.diversity_factor,
            limit=request.limit + request.offset
        )
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[request.offset:request.offset + request.limit]
        
        # Convert to response model
        response_items = []
        for hit in paginated_results:
            response_items.append(
                RecommendationResponse(
                    id=hit["id"],
                    score=hit["score"],
                    payload=hit["payload"]
                )
            )
        
        # Calculate pagination info
        page_size = request.limit
        current_page = (request.offset // page_size) + 1 if page_size > 0 else 1
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 1
        
        result = PaginatedResponse(
            items=response_items,
            total=total_results,
            page=current_page,
            page_size=page_size,
            pages=total_pages
        )
        
        # Add cache headers (medium duration for diverse recommendations)
        add_cache_headers(response, 1800)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/random-games", response_model=List[RecommendationResponse], tags=["Discovery"])
async def random_games(limit: int = 9, response: Response = None):
    """
    Get random games from the collection.
    
    This endpoint is useful for starting the discovery process or exploring the catalog.
    """
    try:
        results = search_enhanced.get_random_games(limit)
        
        # Convert to response model
        response_items = []
        for point in results:
            response_items.append(
                RecommendationResponse(
                    id=point["id"],
                    score=point["score"],
                    payload=point["payload"]
                )
            )
        
        # Add cache headers (short duration for random games)
        add_cache_headers(response, 60)
        return response_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting random games: {str(e)}"
        )

@app.get("/game/{game_id}", response_model=GameDetail, tags=["Games"])
async def get_game_details(game_id: str, similar_limit: int = 5, response: Response = None):
    """
    Get detailed information about a specific game.
    
    This endpoint retrieves all available details about a game and includes similar game recommendations.
    """
    try:
        # Get the game details
        game = search_enhanced.get_game_by_id(game_id)
        if not game:
            # Try to fetch directly from Steam API if not in database
            try:
                steam_data = search_enhanced.get_steam_game_description(game_id)
                if steam_data and (steam_data['short_description'] or steam_data['detailed_description']):
                    # Create a minimal game object with Steam data
                    game = {
                        "id": game_id,
                        "score": 1.0,
                        "payload": {
                            "name": f"Game {game_id}",  # We don't have the name
                            "steam_appid": int(game_id),
                            "price": 0.0,  # We don't have the price
                            "genres": "",  # We don't have genres
                            "tags": "",    # We don't have tags
                            "release_date": "",  # We don't have release date
                            "developers": "",    # We don't have developers
                            "platforms": "",     # We don't have platforms
                            "short_description": steam_data['short_description'],
                            "detailed_description": steam_data['detailed_description']
                        }
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Game with ID {game_id} not found"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Game with ID {game_id} not found: {str(e)}"
                )
        
        # Get similar games
        similar_games = search_enhanced.get_game_recommendations(game_id, similar_limit)
        
        # Convert similar games to response model
        similar_games_response = []
        for game_result in similar_games:
            similar_games_response.append(
                RecommendationResponse(
                    id=game_result["id"],
                    score=game_result["score"],
                    payload=game_result["payload"]
                )
            )
        
        # Create the response
        result = GameDetail(
            id=game["id"] if isinstance(game["id"], str) else str(game["id"]),
            name=game["payload"].get("name", "Unknown"),
            price=game["payload"].get("price", 0.0),
            genres=game["payload"].get("genres", ""),
            tags=game["payload"].get("tags", ""),
            release_date=game["payload"].get("release_date", "Unknown"),
            developers=game["payload"].get("developers", "Unknown"),
            platforms=game["payload"].get("platforms", ""),
            short_description=game["payload"].get("short_description", ""),
            detailed_description=game["payload"].get("detailed_description", ""),
            similar_games=similar_games_response
        )
        
        # Add cache headers (day-long for game details)
        add_cache_headers(response, 86400)  # 24 hours
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting game details: {str(e)}"
        )

@app.get("/suggest", tags=["Search"])
async def suggest(query: str, limit: int = 5, response: Response = None):
    """
    Return quick search suggestions based on partial input.
    
    This endpoint provides lightweight search suggestions as users type.
    """
    try:
        if not query or len(query) < 2:
            return []
            
        # Use search_games with a lower limit for quick suggestions
        results = search_enhanced.search_games(query, limit=limit, use_hybrid=True)
        
        # Extract just the names and ids for suggestions
        suggestions = []
        for result in results:
            suggestions.append({
                "id": result["id"],
                "name": result["payload"].get("name", "Unknown"),
                "score": result["score"]
            })
            
        # Add cache headers (short duration for suggestions)
        add_cache_headers(response, 60)
        return suggestions
    except Exception as e:
        # For suggestions, we just return empty list on error
        return []

@app.post("/discovery-preferences", response_model=List[RecommendationResponse], tags=["Discovery"])
async def discovery_preferences(request: DiscoveryPreferencesRequest, response: Response = None):
    """
    Handle user preferences for game discovery.
    This endpoint allows users to like, dislike, unlike, or undislike games,
    refresh the discovery feed, or reset all preferences.
    
    The response always includes a fresh set of games based on updated preferences.
    """
    try:
        # Initialize lists if None
        liked_ids = request.liked_ids or []
        disliked_ids = request.disliked_ids or []
        
        # Create a list of all IDs to exclude from results (both liked and disliked)
        excluded_ids = liked_ids + disliked_ids
        
        # Handle the requested action
        if request.action == "like" and request.game_id:
            # Add to liked list if not already there
            if request.game_id not in liked_ids:
                liked_ids.append(request.game_id)
            # Remove from disliked list if it was there
            if request.game_id in disliked_ids:
                disliked_ids.remove(request.game_id)
                
        elif request.action == "dislike" and request.game_id:
            # Add to disliked list if not already there
            if request.game_id not in disliked_ids:
                disliked_ids.append(request.game_id)
            # Remove from liked list if it was there
            if request.game_id in liked_ids:
                liked_ids.remove(request.game_id)
                
        elif request.action == "unlike" and request.game_id:
            # Remove from liked list
            if request.game_id in liked_ids:
                liked_ids.remove(request.game_id)
                
        elif request.action == "undislike" and request.game_id:
            # Remove from disliked list
            if request.game_id in disliked_ids:
                disliked_ids.remove(request.game_id)
                
        elif request.action == "reset":
            # Clear all preferences
            liked_ids = []
            disliked_ids = []
            excluded_ids = []
        
        # If action is refresh, we just use the current liked/disliked lists
        
        # Get new games based on current preferences
        if len(liked_ids) > 0:
            # If we have likes, use them to recommend more games
            results = search_enhanced.get_discovery_games(
                excluded_ids=excluded_ids,
                positive_ids=liked_ids,
                negative_ids=disliked_ids,
                limit=request.limit
            )
        else:
            # If no likes yet, just get random games excluding any disliked ones
            results = search_enhanced.get_random_games(limit=request.limit, excluded_ids=excluded_ids)
        
        # Add cache headers if response is provided
        if response:
            add_cache_headers(response, duration_seconds=60)  # Short cache for discovery
        
        # Return the results (this will be the new discovery feed)
        return results
        
    except Exception as e:
        logger.error(f"Error in discovery preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing discovery preferences: {str(e)}")

@app.post("/discovery-games", response_model=List[RecommendationResponse], tags=["Discovery"])
async def discovery_games(request: DiscoveryGamesRequest, response: Response = None):
    """
    Get discovery games based on user preferences
    
    Args:
        request: DiscoveryGamesRequest object with user preferences
        
    Returns:
        List of games based on user preferences
    """
    try:
        # Convert string IDs to integers if needed
        positive_ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in request.positive_ids] if request.positive_ids else None
        negative_ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in request.negative_ids] if request.negative_ids else None
        excluded_ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in request.excluded_ids] if request.excluded_ids else None
        
        # Get discovery games
        results = search_enhanced.get_discovery_games(
            positive_ids=positive_ids,
            negative_ids=negative_ids,
            excluded_ids=excluded_ids,
            limit=request.limit
        )
        
        # Add cache headers if response is provided
        if response:
            add_cache_headers(response, duration_seconds=60)  # Short cache for discovery
            
        return results
    except Exception as e:
        logger.error(f"Error in discovery games: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting discovery games: {str(e)}")

@app.get("/discovery-context/{game_id}", response_model=List[RecommendationResponse], tags=["Discovery"])
async def discovery_context(
    game_id: str,
    limit: int = Query(9, ge=1, le=50),
    excluded_ids: Optional[str] = Query(None),
    response: Response = None
):
    """
    Get discovery games based on a specific game context
    
    Args:
        game_id: ID of the game to use as context
        limit: Number of games to return
        excluded_ids: Comma-separated list of game IDs to exclude
        
    Returns:
        List of games similar to the specified game
    """
    try:
        # Parse excluded IDs
        excluded_ids_list = None
        if excluded_ids:
            excluded_ids_list = [int(id) if id.isdigit() else id for id in excluded_ids.split(",")]
        
        # Convert game_id to integer if it's a digit
        if isinstance(game_id, str) and game_id.isdigit():
            game_id = int(game_id)
            
        # Get discovery context
        results = search_enhanced.get_discovery_context(
            game_id=game_id,
            limit=limit,
            excluded_ids=excluded_ids_list
        )
        
        # Add cache headers if response is provided
        if response:
            add_cache_headers(response, duration_seconds=300)  # 5 minute cache for context
            
        return results
    except Exception as e:
        logger.error(f"Error in discovery context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting discovery context: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)