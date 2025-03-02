import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const body = await request.json();
    
    // Use the production URL directly
    const backendUrl = 'https://fastapi-5aw3.onrender.com';
    
    // Forward the request to the backend
    const response = await fetch(`${backendUrl}/discover`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store', // Don't cache the response
    });
    
    // Check if the response is OK
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }
    
    // Get the data from the response
    const data = await response.json();
    
    // Return the data
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching game recommendations:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 