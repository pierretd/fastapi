import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get the URL parameters
    const url = new URL(request.url);
    const gameId = url.searchParams.get('gameId');
    const limit = url.searchParams.get('limit') || '9';
    const excludedIds = url.searchParams.get('excludedIds') || '';
    const nocache = url.searchParams.get('nocache') || Date.now().toString(); // Get nocache param or create one
    
    // Validate the game ID
    if (!gameId) {
      return NextResponse.json(
        { error: 'Game ID is required' },
        { status: 400 }
      );
    }
    
    console.log(`Context API: Processing request for game ${gameId} with cache buster ${nocache}`);
    
    // Get environment variables for the backend URL (default to localhost for development)
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    // Generate a timestamp for the backend request
    const timestamp = Date.now();
    
    // Build the URL with query parameters
    let apiUrl = `${backendUrl}/discovery-context/${gameId}?limit=${limit}&t=${timestamp}`;
    if (excludedIds) {
      apiUrl += `&excluded_ids=${excludedIds}`;
    }
    
    console.log(`Context API: Forwarding to backend URL: ${apiUrl}`);
    
    // Forward the request to the backend
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      cache: 'no-store', // Don't cache the response
      next: { revalidate: 0 } // Tell Next.js not to cache this request
    });
    
    // Check if the response is OK
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }
    
    // Get the data from the response
    const data = await response.json();
    console.log(`Context API: Received ${data.length} games from backend`);
    
    // Post-process the data to add header_image field based on steam_appid
    const processedData = data.map((game: any) => {
      // Update header_image URL to point to Steam CDN
      if (game.payload && game.payload.steam_appid) {
        game.payload.header_image = `https://cdn.cloudflare.steamstatic.com/steam/apps/${game.payload.steam_appid}/header.jpg`;
      }
      return game;
    });
    
    // Return the data
    return NextResponse.json(processedData);
  } catch (error) {
    console.error('Error fetching discovery context:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 