'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';

interface Game {
  id: string;
  name: string;
  price: number;
  short_description: string;
  detailed_description?: string;
  release_date: string;
  developers: string;
  platforms: string;
  genres: string;
  tags: string;
  similar_games?: any[];
  relevance?: number;
}

interface SearchResponse {
  items: Game[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface RecommendationResponse {
  items: Game[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export default function GameDetails() {
  const params = useParams();
  const router = useRouter();
  const gameId = params.id as string;
  
  const [game, setGame] = useState<Game | null>(null);
  const [recommendations, setRecommendations] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Helper function to convert comma-separated strings to arrays
  const splitString = (str: string): string[] => {
    return str ? str.split(',').map(item => item.trim()) : [];
  };

  useEffect(() => {
    const fetchGameDetails = async () => {
      if (!gameId) return;
      
      setLoading(true);
      setError('');
      
      try {
        // Try first to fetch the game directly from the game endpoint
        const gameResponse = await fetch(`/api/py/game/${gameId}`);
        
        if (gameResponse.ok) {
          const gameData = await gameResponse.json();
          
          // Enhance description if needed
          enhanceGameDescription(gameData);
          
          setGame(gameData);
        } else {
          // Fall back to search if direct game fetch fails
          const response = await fetch('/api/py/search', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: gameId,
              limit: 50
            })
          });
          
          if (!response.ok) {
            throw new Error(`Error fetching game details: ${response.statusText}`);
          }
          
          const data: SearchResponse = await response.json();
          const foundGame = data.items?.find((g: Game) => g.id.toString() === gameId);
          
          if (!foundGame) {
            throw new Error('Game not found');
          }
          
          // Enhance description if needed
          enhanceGameDescription(foundGame);
          
          setGame(foundGame);
        }
        
        // Now fetch recommendations
        const recResponse = await fetch(`/api/py/recommend/${gameId}?limit=6`);
        
        if (!recResponse.ok) {
          throw new Error(`Error fetching recommendations: ${recResponse.statusText}`);
        }
        
        const recData: RecommendationResponse = await recResponse.json();
        
        // Enhance descriptions for recommendations
        if (recData.items) {
          recData.items.forEach(game => enhanceGameDescription(game));
        }
        
        setRecommendations(recData.items || []);
      } catch (err) {
        console.error('Error fetching game data:', err);
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    };

    fetchGameDetails();
  }, [gameId]);

  // Helper function to enhance game descriptions
  const enhanceGameDescription = (game: any) => {
    if (!game) return;
    
    // Get the current description or empty string if missing
    const currentDesc = game.short_description || '';
    
    // Create an enhanced description if it's generic or missing
    if (!currentDesc || currentDesc.startsWith(`A ${game.genres} game`)) {
      // Create a better description from the info we have
      const name = game.name;
      const genres = game.genres;
      
      // Handle tags safely
      const tagsArray = game.tags ? game.tags.split(',').map((tag: string) => tag.trim()).slice(0, 5) : [];
      const tagsStr = tagsArray.join(', ');
      
      const developers = game.developers || 'an indie studio';
      
      game.short_description = `${name} is a ${genres} game. ` + 
                               `It features ${tagsStr} gameplay elements. ` +
                               `Developed by ${developers}.`;
                               
      console.log("Enhanced description for game:", game.id);
    }
  };

  const formatPrice = (price: number) => {
    if (price === 0) return 'Free to Play';
    return `$${price.toFixed(2)}`;
  };

  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center p-8">
        <div className="w-full max-w-4xl">
          <Link href="/" className="text-blue-500 hover:underline mb-6 inline-block">
            &larr; Back to Home
          </Link>
          <div className="flex justify-center items-center min-h-[60vh]">
            <p className="text-lg">Loading game details...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center p-8">
        <div className="w-full max-w-4xl">
          <Link href="/" className="text-blue-500 hover:underline mb-6 inline-block">
            &larr; Back to Home
          </Link>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h1 className="text-xl text-red-600 mb-2">Error</h1>
            <p>{error}</p>
            <button 
              onClick={() => router.back()} 
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Go Back
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (!game) {
    return (
      <main className="flex min-h-screen flex-col items-center p-8">
        <div className="w-full max-w-4xl">
          <Link href="/" className="text-blue-500 hover:underline mb-6 inline-block">
            &larr; Back to Home
          </Link>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <h1 className="text-xl text-yellow-600 mb-2">Game Not Found</h1>
            <p>We couldn&apos;t find the game you&apos;re looking for.</p>
            <button 
              onClick={() => router.back()} 
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Go Back
            </button>
          </div>
        </div>
      </main>
    );
  }

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
          
          {/* Game Details */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">{game.name}</h1>
              
              <div className="flex flex-wrap gap-2 mb-4">
                {splitString(game.genres).map((genre, index) => (
                  <span 
                    key={index}
                    className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded dark:bg-blue-900 dark:text-blue-300"
                  >
                    {genre}
                  </span>
                ))}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-gray-700 dark:text-gray-300 mb-4">{game.short_description}</p>
                  
                  <div className="mb-4">
                    <p className="text-green-600 dark:text-green-400 font-bold text-xl">{formatPrice(game.price)}</p>
                  </div>
                </div>
                
                <div className="border-t pt-4 md:border-t-0 md:pt-0 md:border-l md:pl-6">
                  <h2 className="font-semibold mb-2">Details</h2>
                  <dl className="grid grid-cols-[120px_1fr] gap-y-2">
                    <dt className="text-gray-600 dark:text-gray-400">Developer:</dt>
                    <dd>{game.developers}</dd>
                    
                    <dt className="text-gray-600 dark:text-gray-400">Platforms:</dt>
                    <dd>{splitString(game.platforms).join(', ')}</dd>
                    
                    <dt className="text-gray-600 dark:text-gray-400">Release Date:</dt>
                    <dd>{game.release_date}</dd>
                    
                    {splitString(game.tags).length > 0 && (
                      <>
                        <dt className="text-gray-600 dark:text-gray-400">Tags:</dt>
                        <dd className="flex flex-wrap gap-1">
                          {splitString(game.tags).slice(0, 5).map((tag, index) => (
                            <span 
                              key={index} 
                              className="bg-gray-100 text-gray-800 text-xs px-2 py-0.5 rounded dark:bg-gray-700 dark:text-gray-300"
                            >
                              {tag}
                            </span>
                          ))}
                          {splitString(game.tags).length > 5 && (
                            <span className="text-xs text-gray-500">+{splitString(game.tags).length - 5} more</span>
                          )}
                        </dd>
                      </>
                    )}
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          {game.detailed_description && (
            <div className="mt-6">
              <h2 className="text-xl font-semibold mb-2">About this game</h2>
              <div 
                className="prose prose-blue max-w-none dark:prose-invert prose-h3:text-lg prose-h3:font-semibold"
                dangerouslySetInnerHTML={{ __html: game.detailed_description }}
              />
            </div>
          )}
          
          {/* Recommendations */}
          <div className="mt-8">
            <h2 className="text-xl font-bold mb-4">Similar Games You Might Enjoy</h2>
            {recommendations.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {recommendations.map((rec) => (
                  <Link 
                    href={`/game/${rec.id}`} 
                    key={rec.id}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200"
                  >
                    <div className="p-4">
                      <h3 className="font-semibold text-lg mb-1 line-clamp-1">{rec.name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{formatPrice(rec.price)}</p>
                      <p className="text-sm line-clamp-2">{rec.short_description}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {splitString(rec.genres).slice(0, 2).map((genre, idx) => (
                          <span 
                            key={idx}
                            className="bg-blue-50 text-blue-700 text-xs px-1.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300"
                          >
                            {genre}
                          </span>
                        ))}
                        {splitString(rec.genres).length > 2 && (
                          <span className="text-xs text-gray-500">+{splitString(rec.genres).length - 2} more</span>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No recommendations available for this game.</p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
} 