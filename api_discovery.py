from fastapi import FastAPI, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import sys
import importlib.util
from dotenv import load_dotenv
import random
import time

# Load environment variables
load_dotenv()

# Directly import the search.py file
search_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search.py")
spec = importlib.util.spec_from_file_location("search_module", search_path)
search_module = importlib.util.module_from_spec(spec)
sys.modules["search_module"] = search_module
spec.loader.exec_module(search_module)

# Create FastAPI app
app = FastAPI()

class DiscoveryRequest(BaseModel):
    positive_ids: Optional[List[str]] = []
    negative_ids: Optional[List[str]] = []
    excluded_ids: Optional[List[str]] = []
    limit: int = 9
    randomize: Optional[int] = None
    action: Optional[str] = "refresh"
    game_id: Optional[str] = ""

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/discovery-games")
async def discovery_games(request: DiscoveryRequest):
    """
    Get discovery games based on user preferences
    
    Args:
        request: DiscoveryRequest object with user preferences
        
    Returns:
        List of games based on user preferences
    """
    try:
        # Convert string IDs to integers if needed
        positive_ids = [int(id) if id.isdigit() else id for id in request.positive_ids] if request.positive_ids else None
        negative_ids = [int(id) if id.isdigit() else id for id in request.negative_ids] if request.negative_ids else None
        excluded_ids = [int(id) if id.isdigit() else id for id in request.excluded_ids] if request.excluded_ids else None
        
        # Set random seed if randomize parameter is provided
        randomize = request.randomize
        if randomize is not None:
            random.seed(randomize)
            print(f"Using random seed: {randomize} for discovery games")
        
        # Get discovery games
        games = search_module.get_discovery_games(
            positive_ids=positive_ids,
            negative_ids=negative_ids,
            excluded_ids=excluded_ids,
            limit=request.limit,
            randomize=randomize
        )
        
        # Reset random seed to system time to avoid affecting other requests
        random.seed()
        
        # Format the response
        formatted_games = []
        for game in games:
            formatted_game = {
                "id": game.get("id"),
                "payload": game.get("payload", {}),
                "score": game.get("score", 0)
            }
            formatted_games.append(formatted_game)
            
        return formatted_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting discovery games: {str(e)}")

@app.post("/api/v1/discovery/preferences")
async def discovery_preferences(request: DiscoveryRequest, t: Optional[str] = Query(None)):
    """
    API v1 endpoint for discovery preferences
    This matches the route used by the frontend
    
    Args:
        request: DiscoveryRequest object with user preferences
        t: Optional timestamp for cache busting
        
    Returns:
        List of games based on user preferences
    """
    try:
        # If timestamp provided in URL, log it
        if t:
            print(f"[API v1] Received timestamp in URL: {t}")
            
        # Convert string IDs to integers if needed
        positive_ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in request.positive_ids] if request.positive_ids else None
        negative_ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in request.negative_ids] if request.negative_ids else None
        excluded_ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in request.excluded_ids] if request.excluded_ids else None
        
        # Always use the randomize parameter if provided, or generate a truly unique one
        randomize = request.randomize
        if randomize is None:
            # Create a super-unique timestamp-based random seed
            current_time_ns = int(time.time() * 1000000)
            randomize = current_time_ns ^ random.randint(0, 1000000)
            
        print(f"[API v1] Using random seed: {randomize} for discovery preferences")
        
        # Log additional debugging information
        print(f"[API v1] Request parameters: action={request.action}, game_id={request.game_id}")
        print(f"[API v1] Positive IDs count: {len(positive_ids) if positive_ids else 0}")
        print(f"[API v1] Negative IDs count: {len(negative_ids) if negative_ids else 0}")
        
        # Get discovery games
        games = search_module.get_discovery_games(
            positive_ids=positive_ids,
            negative_ids=negative_ids,
            excluded_ids=excluded_ids,
            limit=request.limit,
            randomize=randomize
        )
        
        # Format the response
        formatted_games = []
        for game in games:
            formatted_game = {
                "id": game.get("id"),
                "payload": game.get("payload", {}),
                "score": game.get("score", 0)
            }
            formatted_games.append(formatted_game)
        
        # Log the first few game IDs that we're returning
        if formatted_games:
            sample_ids = [game["id"] for game in formatted_games[:3]]
            print(f"[API v1] Returning {len(formatted_games)} games. Sample IDs: {sample_ids}")
        
        return formatted_games
    except Exception as e:
        print(f"[API v1] Error in discovery_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting discovery games: {str(e)}")

@app.get("/discovery-context/{game_id}")
async def discovery_context(
    game_id: str,
    limit: int = Query(9, ge=1, le=50),
    excluded_ids: Optional[str] = Query(None)
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
        if game_id.isdigit():
            game_id = int(game_id)
            
        # Get discovery context
        games = search_module.get_discovery_context(
            game_id=game_id,
            limit=limit,
            excluded_ids=excluded_ids_list
        )
        
        # Format the response
        formatted_games = []
        for game in games:
            formatted_game = {
                "id": game.get("id"),
                "payload": game.get("payload", {}),
                "score": game.get("score", 0)
            }
            formatted_games.append(formatted_game)
            
        return formatted_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting discovery context: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 