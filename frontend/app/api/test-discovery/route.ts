import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Get the backend URL from environment variables or default to the production URL
    const backendUrl = process.env.BACKEND_URL || 'https://fastapi-5aw3.onrender.com';
    
    // Test the random-games endpoint
    const randomGamesResponse = await fetch(`${backendUrl}/random-games?limit=3`);
    const randomGames = await randomGamesResponse.json();
    
    // Test the discover endpoint with sample liked/disliked IDs
    const discoverResponse = await fetch(`${backendUrl}/discover`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        liked: [730, 570], // Sample game IDs (CS:GO and Dota 2)
        disliked: [440],   // Sample game ID (Team Fortress 2)
        limit: 3
      })
    });
    const discoverGames = await discoverResponse.json();
    
    return NextResponse.json({
      success: true,
      randomGamesStatus: randomGamesResponse.status,
      randomGames: randomGames,
      discoverStatus: discoverResponse.status,
      discoverGames: discoverGames
    });
  } catch (error) {
    console.error('API test error:', error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 