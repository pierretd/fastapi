# New Features for Next.js Frontend Integration

This document outlines the new features added to the Steam Games Search API to better support the Next.js frontend application.

## Table of Contents
- [Game Details Endpoint](#game-details-endpoint)
- [Pagination Support](#pagination-support)
- [Health Check Endpoint](#health-check-endpoint)
- [Error Handling Improvements](#error-handling-improvements)
- [Search Suggestions](#search-suggestions)
- [Caching Headers](#caching-headers)
- [Rate Limiting](#rate-limiting)

## Game Details Endpoint

A new endpoint has been added to fetch comprehensive details about a specific game, including similar games recommendations.

### Endpoint

```
GET /game/{game_id}
```

### Parameters

- `game_id` (path parameter) - The Steam App ID of the game
- `similar_limit` (query parameter, optional) - Number of similar games to include (default: 5)

### Response Format

```json
{
  "id": "123456",
  "name": "Game Title",
  "price": 19.99,
  "genres": "Action,Adventure",
  "tags": "Multiplayer,Open World",
  "release_date": "2023-01-15",
  "developers": "Developer Name",
  "platforms": "windows,mac",
  "short_description": "Short game description",
  "detailed_description": "Detailed game description...",
  "similar_games": [
    {
      "id": "654321",
      "score": 0.95,
      "payload": {
        "name": "Similar Game 1",
        "price": 29.99,
        "genres": "Action,RPG",
        ...
      }
    },
    ...
  ]
}
```

## Pagination Support

All list-returning endpoints now support pagination for more efficient data retrieval, including:

- `/search`
- `/recommend/{game_id}`
- `/enhanced-recommend`
- `/discover`
- `/diverse-recommend`

### Common Parameters

- `limit` - Number of results per page
- `offset` - Number of results to skip (for manual pagination)

### Response Format

```json
{
  "items": [
    {
      "id": "123456",
      "score": 0.92,
      "payload": {
        "name": "Game Title",
        ...
      }
    },
    ...
  ],
  "total": 50,
  "page": 1,
  "page_size": 10,
  "pages": 5
}
```

## Health Check Endpoint

A new endpoint has been added to monitor the health status of the API.

### Endpoint

```
GET /health
```

### Response Format

```json
{
  "status": "healthy",
  "timestamp": 1698765432.123
}
```

## Error Handling Improvements

Error handling has been standardized across all endpoints, with consistent error formats and more detailed error messages.

### Error Response Format

```json
{
  "detail": "Detailed error message",
  "code": "error_code",
  "status_code": 404,
  "path": "/endpoint/path"
}
```

## Search Suggestions

A new endpoint has been added to provide quick search suggestions based on partial input.

### Endpoint

```
GET /suggest?query={partial_query}&limit={limit}
```

### Parameters

- `query` - Partial search text
- `limit` (optional) - Maximum number of suggestions to return (default: 5)

### Response Format

```json
[
  {
    "id": "123456",
    "name": "Game Title",
    "score": 0.92
  },
  ...
]
```

## Caching Headers

Proper caching headers have been added to all responses to improve performance and reduce server load.

- Root endpoint: 1 hour cache
- Game details: 24 hours cache
- Search results: 5 minutes cache
- Recommendations: 30 minutes cache
- Random games: 1 minute cache
- Suggestions: 1 minute cache

```
Cache-Control: public, max-age=3600
```

## Rate Limiting

Optional rate limiting has been added to protect the API from abuse. This can be enabled through environment variables.

### Environment Variables

- `ENABLE_RATE_LIMITING` - Set to "true" to enable rate limiting (default: "false")
- `API_VERSION` - API version string (default: "1.0.0")
- `DEFAULT_CACHE_DURATION` - Default cache duration in seconds (default: 3600)

When enabled, rate limiting restricts clients to 60 requests per minute by default.

## Cross-Origin Resource Sharing (CORS)

CORS is configured to allow requests from any origin. For production environments, it's recommended to restrict this to your specific frontend domain.

## Using These Features with Next.js

### Example: Fetching Game Details with Similar Games

```javascript
// pages/game/[id].js
import { useRouter } from 'next/router'
import { useState, useEffect } from 'react'

export default function GameDetailsPage() {
  const router = useRouter()
  const { id } = router.query
  const [game, setGame] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return

    async function fetchGameDetails() {
      try {
        const response = await fetch(`https://your-api-url/game/${id}`)
        if (!response.ok) throw new Error('Failed to fetch game details')
        const data = await response.json()
        setGame(data)
      } catch (error) {
        console.error('Error fetching game details:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGameDetails()
  }, [id])

  if (loading) return <div>Loading...</div>
  if (!game) return <div>Game not found</div>

  return (
    <div>
      <h1>{game.name}</h1>
      <p>Price: ${game.price}</p>
      <p>Released: {game.release_date}</p>
      <p>{game.short_description}</p>
      
      <h2>Similar Games</h2>
      <div className="similar-games-grid">
        {game.similar_games.map(similarGame => (
          <div key={similarGame.id} className="game-card">
            <h3>{similarGame.payload.name}</h3>
            <p>Similarity: {(similarGame.score * 100).toFixed(0)}%</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

### Example: Paginated Search

```javascript
// components/GameSearch.js
import { useState } from 'react'

export default function GameSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 10

  async function searchGames(page = 1) {
    setLoading(true)
    
    try {
      const offset = (page - 1) * pageSize
      const response = await fetch('https://your-api-url/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          limit: pageSize,
          offset,
          use_hybrid: true
        }),
      })
      
      if (!response.ok) throw new Error('Search failed')
      
      const data = await response.json()
      setResults(data)
      setCurrentPage(page)
    } catch (error) {
      console.error('Error searching games:', error)
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim()) {
      searchGames(1) // Reset to first page on new search
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for games..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results && (
        <>
          <p>
            Showing {results.items.length} of {results.total} results
            (Page {results.page} of {results.pages})
          </p>
          
          <div className="search-results">
            {results.items.map(game => (
              <div key={game.id} className="game-card">
                <h3>{game.payload.name}</h3>
                <p>${game.payload.price}</p>
                <p>{game.payload.short_description}</p>
              </div>
            ))}
          </div>
          
          <div className="pagination">
            <button 
              onClick={() => searchGames(currentPage - 1)}
              disabled={currentPage === 1 || loading}
            >
              Previous
            </button>
            
            <span>Page {currentPage} of {results.pages}</span>
            
            <button
              onClick={() => searchGames(currentPage + 1)}
              disabled={currentPage === results.pages || loading}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
``` 