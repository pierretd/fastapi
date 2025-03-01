from fastapi import FastAPI, HTTPException, Query, Body
import httpx
import os
from typing import Optional, Dict, Any

BACKEND_URL = os.environ.get("BACKEND_URL", "https://fastapi-5aw3.onrender.com")

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
                # Get the data from the response and return it directly
                data = await response.json()
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
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/game/{game_id}")
            
            if response.status_code == 200:
                # Get the raw game data
                game_data = await response.json()
                
                # Get the current description or empty string if missing
                current_desc = game_data.get('short_description', '')
                
                # Check if description is missing or is a generic one
                if not current_desc or current_desc.startswith(f"A {game_data.get('genres', '')} game"):
                    # Create a better description from the info we have
                    name = game_data.get('name', '')
                    genres = game_data.get('genres', '')
                    
                    # Handle tags safely by converting to list if it's a string
                    tags_raw = game_data.get('tags', '')
                    tags = tags_raw.split(',')[:5] if isinstance(tags_raw, str) else []
                    tags_str = ', '.join(tags) if tags else ''
                    
                    developers = game_data.get('developers', 'an indie studio')
                    
                    # Create an enhanced description
                    game_data['short_description'] = (
                        f"{name} is a {genres} game. "
                        f"It features {tags_str} gameplay elements. "
                        f"Developed by {developers}."
                    )
                
                return game_data
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {response.text}"
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/py/helloFastApi")
async def hello_fast_api():
    return {"message": "Hello from FastAPI"}