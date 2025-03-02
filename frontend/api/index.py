from fastapi import FastAPI, HTTPException, Query, Body
import httpx
import os
from typing import Optional, Dict, Any, List

BACKEND_URL = "https://fastapi-5aw3.onrender.com"

### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

@app.get("/api/py/health")
async def health():
    """Check if the API is running and connected to the backend"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                return {"status": "ok", "backend_status": response.json()}
            else:
                return {"status": "error", "message": f"Backend returned status {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/py/search")
async def search(query: str = Body(...), limit: int = Body(10)):
    """Search for games using the vector search API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/search",
                json={"query": query, "limit": limit}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Keep the GET endpoint for backward compatibility
@app.get("/api/py/search")
async def search_get(query: str, limit: int = Query(10, ge=1, le=50)):
    """Search for games using the vector search API (GET method)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/search",
                json={"query": query, "limit": limit}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/py/recommend/{game_id}")
async def recommend(game_id: int, limit: int = Query(10, ge=1, le=50)):
    """Get game recommendations based on a game ID"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/recommend/{game_id}",
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/py/random-games")
async def random_games(limit: int = Query(10, ge=1, le=50)):
    """Get random games from the collection"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/random-games",
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                # Get the data from the response
                data = await response.json()
                
                # Process each game to ensure proper descriptions
                for game in data:
                    if "payload" in game and "short_description" in game["payload"]:
                        current_desc = game["payload"]["short_description"]
                        genres = game["payload"].get("genres", "")
                        
                        # Check if the description is the generic format we want to avoid
                        if current_desc.startswith(f"A {genres} game with") or current_desc.startswith(f"{genres} game with"):
                            print(f"Found generic description for game {game['id']}, fetching better one")
                            try:
                                # Get the original game data from the backend
                                game_id = game["id"]
                                game_response = await client.get(f"{BACKEND_URL}/games/{game_id}")
                                
                                if game_response.status_code == 200:
                                    game_data = await game_response.json()
                                    if game_data.get("short_description"):
                                        # Replace with the original description
                                        game["payload"]["short_description"] = game_data["short_description"]
                                        print(f"Successfully replaced description for game {game_id}")
                            except Exception as e:
                                print(f"Error fetching better description: {e}")
                
                return data
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/py/game/{game_id}")
async def get_game(game_id: str):
    """Get detailed information about a specific game"""
    # Ensure logging for tracking
    print(f"get_game called with ID: {game_id}")
    
    # Extract both ID and any embedded description
    embedded_description = None
    if ":" in game_id:
        parts = game_id.split(":", 1)
        base_game_id = parts[0]
        if len(parts) > 1 and len(parts[1]) > 20:
            embedded_description = parts[1]
            print(f"Found embedded description in game ID: {embedded_description[:30]}...")
    else:
        base_game_id = game_id
    
    # Set timeout for HTTP client to prevent long waits
    timeout = httpx.Timeout(5.0, connect=3.0)
    
    try:
        # Attempt to get game data from the backend
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{BACKEND_URL}/games/{base_game_id}")
            response.raise_for_status()
            game_data = response.json()
            
            # If we have an embedded description from the ID, use it
            if embedded_description:
                # Store the embedded description in a special field
                game_data["embedded_description"] = embedded_description
                
                # Only use it as the main description if the current ones are generic/missing
                if not game_data.get("short_description") or len(game_data.get("short_description", "")) < 20:
                    game_data["short_description"] = embedded_description
            
            # Only add a fallback description if we don't have any good description
            elif (not game_data.get("short_description") or len(game_data.get("short_description", "")) < 20) and \
                 (not game_data.get("detailed_description") or len(game_data.get("detailed_description", "")) < 20):
                # Create a minimal description that doesn't follow the problematic pattern
                game_name = game_data.get("name", "This game")
                dev_info = f" by {game_data.get('developers', 'indie developers')}" if game_data.get("developers") else ""
                
                if game_data.get("genres") and game_data.get("tags"):
                    # Select at most 2 genres and tags for a cleaner description
                    genres = game_data.get("genres", "").split(',')[:2]
                    tags = game_data.get("tags", "").split(',')[:2]
                    
                    genre_text = " and ".join(genres) if len(genres) <= 2 else f"{genres[0]} and more"
                    tag_text = " and ".join(tags) if len(tags) <= 2 else f"{tags[0]} and more"
                    
                    game_data["short_description"] = f"{game_name}{dev_info} offers {genre_text} gameplay with {tag_text} elements."
                else:
                    game_data["short_description"] = f"{game_name}{dev_info}. More information coming soon."
        
        return game_data
    
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        # If we fail to get the game, return a fallback response
        print(f"Error fetching game {game_id}: {str(e)}")
        
        # If we have an embedded description, use it in the fallback
        fallback_response = {
            "id": game_id,
            "name": "Game Information Unavailable",
            "header_image": "/placeholder.jpg",
            "screenshots": [],
            "developers": "",
            "publishers": "",
            "genres": "",
            "tags": ""
        }
        
        if embedded_description:
            fallback_response["short_description"] = embedded_description
            fallback_response["embedded_description"] = embedded_description
        else:
            fallback_response["short_description"] = "We're having trouble loading this game's information. Please try again later."
            
        return fallback_response

@app.get("/api/py/helloFastApi")
async def hello_fast_api():
    return {"message": "Hello from FastAPI"}

@app.post("/api/py/discovery-preferences")
async def discovery_preferences(
    liked_ids: Optional[List[str]] = Body(None), 
    disliked_ids: Optional[List[str]] = Body(None),
    action: str = Body(...),
    game_id: Optional[str] = Body(None),
    limit: int = Body(9)
):
    """
    Handle user preferences for game discovery.
    
    This endpoint allows users to:
    - Like or dislike games
    - Remove likes or dislikes
    - Refresh the discovery feed
    - Reset all preferences
    
    Args:
        liked_ids: List of game IDs the user has liked
        disliked_ids: List of game IDs the user has disliked
        action: Action to perform (like, dislike, unlike, undislike, refresh, reset)
        game_id: Game ID for the action (required for like, dislike, unlike, undislike)
        limit: Number of games to return in the response
    
    Returns:
        A fresh set of games based on updated preferences
    """
    try:
        # Validate the action
        valid_actions = ["like", "dislike", "unlike", "undislike", "refresh", "reset"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid action: {action}. Must be one of: {', '.join(valid_actions)}"
            )
        
        # Validate game_id is provided when needed
        if action in ["like", "dislike", "unlike", "undislike"] and not game_id:
            raise HTTPException(
                status_code=400,
                detail=f"Game ID is required for action: {action}"
            )
        
        # Prepare the request payload
        payload = {
            "liked_ids": liked_ids or [],
            "disliked_ids": disliked_ids or [],
            "action": action,
            "game_id": game_id,
            "limit": limit
        }
        
        # Make the request to the backend
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/discovery-preferences",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/py/discovery-games")
async def discovery_games(
    positive_ids: Optional[List[str]] = Body(None),
    negative_ids: Optional[List[str]] = Body(None),
    excluded_ids: Optional[List[str]] = Body(None),
    limit: int = Body(9)
):
    """
    Get discovery games based on user preferences
    
    Args:
        positive_ids: List of game IDs the user has liked
        negative_ids: List of game IDs the user has disliked
        excluded_ids: List of game IDs to exclude from results
        limit: Number of games to return
        
    Returns:
        List of games based on user preferences
    """
    try:
        # Prepare the request payload
        payload = {
            "positive_ids": positive_ids or [],
            "negative_ids": negative_ids or [],
            "excluded_ids": excluded_ids or [],
            "limit": limit
        }
        
        # Make the request to the backend
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/discovery-games",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/py/discovery-context/{game_id}")
async def discovery_context(
    game_id: str,
    limit: int = Query(9, ge=1, le=50),
    excluded_ids: Optional[List[str]] = Query(None)
):
    """
    Get discovery games based on a specific game context
    
    Args:
        game_id: ID of the game to use as context
        limit: Number of games to return
        excluded_ids: List of game IDs to exclude from results
        
    Returns:
        List of games similar to the specified game
    """
    try:
        # Prepare the query parameters
        params = {
            "limit": limit
        }
        
        if excluded_ids:
            params["excluded_ids"] = ",".join(excluded_ids)
        
        # Make the request to the backend
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/discovery-context/{game_id}",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")