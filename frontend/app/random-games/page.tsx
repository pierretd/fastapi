'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';

interface GamePayload {
  name: string;
  price: number;
  short_description: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  steam_appid: string;
}

interface ApiGame {
  id: string;
  score: number;
  payload: GamePayload;
}

interface Game {
  id: string;
  name: string;
  price: number;
  short_description: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  relevance?: number;
  imageUrl: string;
}

interface RandomGamesResponse {
  items: Game[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export default function RandomGames() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [limit, setLimit] = useState(10);

  const fetchRandomGames = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/py/random-games?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      // The API returns an array of games directly, not wrapped in a RandomGamesResponse
      const apiGames: ApiGame[] = await response.json();
      
      // Transform the API response to match our Game interface
      const transformedGames: Game[] = processApiGames(apiGames);
      
      setGames(transformedGames);
    } catch (err) {
      console.error('Error fetching random games:', err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchRandomGames();
  }, [fetchRandomGames]);

  const handleRefresh = () => {
    fetchRandomGames();
  };

  // Helper function to convert comma-separated strings to arrays
  const splitString = (str: string): string[] => {
    return str ? str.split(',').map(item => item.trim()) : [];
  };

  // Format price display
  const formatPrice = (price: number): string => {
    if (price === 0) return 'Free to Play';
    return `$${price.toFixed(2)}`;
  };

  // Process games from API to match the Game interface
  const processApiGames = (apiGames: ApiGame[]): Game[] => {
    return apiGames.map(apiGame => {
      // Use the original description without enhancement
      const description = apiGame.payload.short_description || '';
      
      return {
        id: apiGame.id,
        name: apiGame.payload.name,
        price: apiGame.payload.price,
        short_description: description,
        release_date: apiGame.payload.release_date,
        developers: apiGame.payload.developers,
        genres: apiGame.payload.genres,
        tags: apiGame.payload.tags,
        relevance: apiGame.score,
        // Construct Steam store image URL using the appid
        imageUrl: `https://cdn.cloudflare.steamstatic.com/steam/apps/${apiGame.payload.steam_appid}/header.jpg`
      };
    });
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-4xl">
        <div className="flex flex-col gap-8">
          {/* Navigation */}
          <div className="flex justify-between items-center">
            <Link href="/" className="text-blue-500 hover:underline">
              &larr; Back to Home
            </Link>
            <Link href="/search" className="text-blue-500 hover:underline">
              Search Games
            </Link>
          </div>
          
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">Random Games</h1>
                <div className="flex items-center gap-4">
                  <select 
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="px-3 py-2 border border-gray-300 rounded text-sm"
                  >
                    <option value={5}>5 games</option>
                    <option value={10}>10 games</option>
                    <option value={20}>20 games</option>
                    <option value={30}>30 games</option>
                  </select>
                  <button
                    onClick={handleRefresh}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                  >
                    {loading ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">
              <p className="font-bold">Error</p>
              <p>{error}</p>
            </div>
          )}
          
          {/* Loading State */}
          {loading && (
            <div className="flex justify-center py-10">
              <p className="text-lg">Loading random games...</p>
            </div>
          )}
          
          {/* Results */}
          {!loading && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
              <div className="p-6">
                {games.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {games.map((game) => (
                      <Link 
                        href={`/game/${game.id}`}
                        key={game.id}
                        className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-200"
                      >
                        <div className="relative w-full h-40">
                          <Image 
                            src={game.imageUrl} 
                            alt={`${game.name} cover`}
                            fill
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                            className="object-cover"
                            onError={(e) => {
                              // Fallback for image loading errors
                              const target = e.target as HTMLImageElement;
                              target.src = "https://placehold.co/600x400/222/fff?text=No+Image";
                            }}
                          />
                        </div>
                        <div className="p-3 flex-1 flex flex-col">
                          <Link href={`/game/${game.id}`} className="text-lg font-semibold mb-2 hover:underline">
                            {game.name}
                          </Link>
                          <p className="text-gray-600 dark:text-gray-400 mb-2">
                            {formatPrice(game.price)}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {game.short_description}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                            Released on {game.release_date}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                            Developed by {game.developers}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                            Genres: {game.genres}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                            Tags: {game.tags}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Relevance: {game.relevance}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p>No games found.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
