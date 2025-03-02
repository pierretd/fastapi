import { NextRequest, NextResponse } from 'next/server';

// Define the API endpoint for search
export async function POST(request: NextRequest) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  try {
    // Parse the JSON request body
    const requestData = await request.json();
    
    // Extract search method parameters
    const { use_hybrid, use_sparse, use_dense, ...otherParams } = requestData;
    
    // Determine which search method to use
    let searchParams = { ...otherParams };
    
    // Only include search method parameters if explicitly set
    if (use_hybrid !== undefined) {
      searchParams.use_hybrid = use_hybrid;
    }
    
    if (use_sparse !== undefined) {
      searchParams.use_sparse = use_sparse;
    }
    
    if (use_dense !== undefined) {
      searchParams.use_dense = use_dense;
    }
    
    // Forward the request to the FastAPI backend
    const response = await fetch(`${baseUrl}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchParams),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Search API error:', errorText);
      return NextResponse.json(
        { error: 'Failed to fetch search results', details: errorText },
        { status: response.status }
      );
    }
    
    // Get the response data
    const data = await response.json();
    
    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('Search API route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 