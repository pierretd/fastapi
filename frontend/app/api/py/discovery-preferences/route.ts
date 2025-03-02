import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const body = await request.json();
    
    // Get environment variables for the backend URL (default to localhost for development)
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8001';
    
    // Extract data from the request
    const { liked_ids = [], disliked_ids = [], limit = 9, randomize, action = 'refresh', game_id = '', _cache_buster = '' } = body;
    
    console.log('API PROXY DEBUG - Request received with params:', { 
      liked_count: liked_ids.length, 
      disliked_count: disliked_ids.length, 
      limit, 
      randomize,
      action,
      game_id,
      _cache_buster,
      request_time: new Date().toISOString()
    });
    
    // Generate a new timestamp for caching control
    const timestamp = Date.now();
    
    // IMPORTANT: Preserve the randomize parameter exactly as sent from the client
    // Do NOT override it with anything else
    console.log(`API PROXY DEBUG - Using randomize value: ${randomize}`);
    
    // Format the request for the discovery-games endpoint
    const apiRequest = {
      positive_ids: liked_ids,
      negative_ids: disliked_ids,
      excluded_ids: [...liked_ids, ...disliked_ids], // Exclude games the user has already rated
      limit,
      randomize: randomize,  // Preserve the exact randomize value
      action,
      game_id,
      _cache_buster: `${_cache_buster || timestamp}-${Math.random()}`
    };
    
    console.log(`API PROXY DEBUG - Sending to backend with randomize=${randomize}`);
    
    // Forward the request to the backend
    const response = await fetch(`${backendUrl}/api/v1/discovery/preferences?t=${timestamp}-${Math.random()}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      body: JSON.stringify(apiRequest),
      cache: 'no-store', // Don't cache the response
      next: { revalidate: 0 } // Tell Next.js to never cache this request
    });
    
    // Check if the response is OK
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }
    
    // Get the data from the response
    const data = await response.json();
    
    console.log(`API PROXY DEBUG - Received ${data.length} games from backend`);
    if (data.length > 0) {
      console.log(`API PROXY DEBUG - First 3 game IDs: ${data.slice(0, 3).map(g => g.id).join(', ')}`);
    }
    
    // Post-process the data to add header_image field based on steam_appid
    const processedData = data.map((game: any) => {
      // Update header_image URL to point to Steam CDN
      if (game.payload && game.payload.steam_appid) {
        game.payload.header_image = `https://cdn.cloudflare.steamstatic.com/steam/apps/${game.payload.steam_appid}/header.jpg`;
      }
      return game;
    });
    
    // Return the data with no-cache headers
    const apiResponse = NextResponse.json(processedData);
    apiResponse.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0');
    apiResponse.headers.set('Pragma', 'no-cache');
    apiResponse.headers.set('Expires', '0');
    return apiResponse;
  } catch (error) {
    console.error('Error fetching discovery games:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 