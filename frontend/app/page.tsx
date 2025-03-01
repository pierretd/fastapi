'use client';

import { useState, useEffect } from 'react';
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

export default function Home() {
  const [games, setGames] = useState<Game[]>([]);
  const [likedGames, setLikedGames] = useState<Game[]>([]);
  const [dislikedGames, setDislikedGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<{ [key: string]: boolean }>({});
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');

  // Load liked and disliked games from local storage
  useEffect(() => {
    const loadSavedGames = () => {
      try {
        const savedLikedGames = localStorage.getItem('likedGames');
        const savedDislikedGames = localStorage.getItem('dislikedGames');
        
        if (savedLikedGames) {
          setLikedGames(JSON.parse(savedLikedGames));
        }
        
        if (savedDislikedGames) {
          setDislikedGames(JSON.parse(savedDislikedGames));
        }
      } catch (err) {
        console.error('Error loading saved games:', err);
        // Continue without saved games if there's an error
      }
    };
    
    loadSavedGames();
    fetchRandomGames();
  }, []);

  // Save liked games to local storage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('likedGames', JSON.stringify(likedGames));
    } catch (err) {
      console.error('Error saving liked games:', err);
    }
  }, [likedGames]);

  // Save disliked games to local storage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('dislikedGames', JSON.stringify(dislikedGames));
    } catch (err) {
      console.error('Error saving disliked games:', err);
    }
  }, [dislikedGames]);

  // Fetch random games from the API
  const fetchRandomGames = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/py/random-games?limit=9`);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      const apiGames: ApiGame[] = await response.json();
      console.log("API Games response:", apiGames);
      
      // Transform the API response to match our Game interface
      const transformedGames: Game[] = processApiGames(apiGames);
      console.log("Transformed games:", transformedGames);
      
      setGames(transformedGames);
    } catch (err) {
      console.error('Error fetching random games:', err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  // Fetch recommendations based on liked/disliked games
  const fetchRecommendations = async (liked: string[], disliked: string[]) => {
    setLoading(true);
    setError('');
    setActionError('');
    
    try {
      const response = await fetch('/api/py/discover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          liked: liked,
          disliked: disliked,
          limit: 9
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      const apiGames: ApiGame[] = await response.json();
      
      // Transform the API response
      const transformedGames: Game[] = processApiGames(apiGames);
      
      setGames(transformedGames);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setActionError(err instanceof Error ? err.message : String(err));
      // If recommendations fail, fall back to random games
      fetchRandomGames();
    } finally {
      setLoading(false);
    }
  };

  // Handle liking a game
  const handleLike = async (game: Game) => {
    // Set loading state for this specific game
    setActionLoading(prev => ({ ...prev, [game.id]: true }));
    setActionError('');
    
    try {
      // Add to liked games
      setLikedGames(prev => {
        const newLikedGames = [...prev, game];
        // Update recommendations based on new likes/dislikes
        fetchRecommendations(
          newLikedGames.map(g => g.id), 
          dislikedGames.map(g => g.id)
        );
        return newLikedGames;
      });
      
      // Remove from current games display
      setGames(prev => prev.filter(g => g.id !== game.id));
    } catch (err) {
      console.error('Error liking game:', err);
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      // Clear loading state for this game
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[game.id];
        return newState;
      });
    }
  };

  // Handle disliking a game
  const handleDislike = async (game: Game) => {
    // Set loading state for this specific game
    setActionLoading(prev => ({ ...prev, [game.id]: true }));
    setActionError('');
    
    try {
      // Add to disliked games
      setDislikedGames(prev => {
        const newDislikedGames = [...prev, game];
        // Update recommendations based on new likes/dislikes
        fetchRecommendations(
          likedGames.map(g => g.id), 
          newDislikedGames.map(g => g.id)
        );
        return newDislikedGames;
      });
      
      // Remove from current games display
      setGames(prev => prev.filter(g => g.id !== game.id));
    } catch (err) {
      console.error('Error disliking game:', err);
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      // Clear loading state for this game
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[game.id];
        return newState;
      });
    }
  };

  // Reset all history and start fresh
  const handleResetHistory = () => {
    setLikedGames([]);
    setDislikedGames([]);
    localStorage.removeItem('likedGames');
    localStorage.removeItem('dislikedGames');
    fetchRandomGames();
  };

  // Helper function to convert comma-separated strings to arrays
  const splitString = (str: string): string[] => {
    return str ? str.split(',').map(item => item.trim()) : [];
  };
  
  // Format price
  const formatPrice = (price: number): string => {
    if (price === 0) return 'Free to Play';
    return `$${price.toFixed(2)}`;
  };

  // Process games from API to match the Game interface
  const processApiGames = (apiGames: ApiGame[]): Game[] => {
    return apiGames.map(apiGame => {
      // Log each item to see the structure
      console.log("Processing game:", apiGame);
      console.log("Short description:", apiGame.payload.short_description);
      
      // Get the current description or empty string if missing
      const currentDesc = apiGame.payload.short_description || '';
      
      // Create an enhanced description if it's generic or missing
      let enhancedDesc = currentDesc;
      if (!currentDesc || currentDesc.startsWith(`A ${apiGame.payload.genres} game`)) {
        // Create a better description from the info we have
        const name = apiGame.payload.name;
        const genres = apiGame.payload.genres;
        
        // Handle tags safely
        const tagsArray = apiGame.payload.tags ? apiGame.payload.tags.split(',').map(tag => tag.trim()).slice(0, 5) : [];
        const tagsStr = tagsArray.join(', ');
        
        const developers = apiGame.payload.developers || 'an indie studio';
        
        enhancedDesc = `${name} is a ${genres} game. ` + 
                       `It features ${tagsStr} gameplay elements. ` +
                       `Developed by ${developers}.`;
                       
        console.log("Enhanced description:", enhancedDesc);
      }
      
      return {
        id: apiGame.id,
        name: apiGame.payload.name,
        price: apiGame.payload.price,
        short_description: enhancedDesc,
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
    <main className="flex min-h-screen flex-col items-center p-2 max-h-screen overflow-hidden">
      <div className="w-full max-w-7xl h-full flex flex-col">
        {/* Header - made more compact */}
        <div className="mb-2">
          <h1 className="text-2xl font-bold text-center mb-1">Game Discovery</h1>
          <p className="text-center text-sm max-w-2xl mx-auto text-gray-600 dark:text-gray-300">
            Discover your next favorite game! Like or dislike games to get personalized recommendations.
          </p>
        </div>

        {/* Main content area */}
        <div className="flex-1 flex flex-col h-[calc(100vh-80px)] overflow-hidden">
          {/* History Section - collapsed by default with toggle */}
          {(likedGames.length > 0 || dislikedGames.length > 0) && (
            <div className="mb-2 bg-white dark:bg-gray-800 rounded-lg shadow-md p-3 overflow-auto max-h-[30vh]">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-lg font-semibold">Your Game History</h2>
                <button
                  onClick={handleResetHistory}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors duration-200"
                >
                  Reset History
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {/* Liked Games */}
                {likedGames.length > 0 && (
                  <div>
                    <h3 className="text-base font-medium text-green-600 mb-1">Games You Liked</h3>
                    <div className="space-y-1 max-h-[20vh] overflow-y-auto pr-1">
                      {likedGames.map((game) => (
                        <Link 
                          key={`liked-${game.id}`} 
                          href={`/game/${game.id}`}
                          className="flex items-center p-1 bg-green-50 dark:bg-green-900/20 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30"
                        >
                          <div className="relative w-8 h-8 flex-shrink-0">
                            <Image 
                              src={game.imageUrl} 
                              alt={game.name}
                              fill
                              className="object-cover rounded"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = "https://placehold.co/100x100/222/fff?text=No+Image";
                              }}
                            />
                          </div>
                          <div className="ml-2 flex-1 overflow-hidden">
                            <p className="font-medium text-xs truncate">{game.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{formatPrice(game.price)}</p>
                          </div>
                          <div className="ml-1 text-green-600 dark:text-green-400">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                              <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                            </svg>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Disliked Games */}
                {dislikedGames.length > 0 && (
                  <div>
                    <h3 className="text-base font-medium text-red-600 mb-1">Games You Disliked</h3>
                    <div className="space-y-1 max-h-[20vh] overflow-y-auto pr-1">
                      {dislikedGames.map((game) => (
                        <Link 
                          key={`disliked-${game.id}`} 
                          href={`/game/${game.id}`}
                          className="flex items-center p-1 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30"
                        >
                          <div className="relative w-8 h-8 flex-shrink-0">
                            <Image 
                              src={game.imageUrl} 
                              alt={game.name}
                              fill
                              className="object-cover rounded"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = "https://placehold.co/100x100/222/fff?text=No+Image";
                              }}
                            />
                          </div>
                          <div className="ml-2 flex-1 overflow-hidden">
                            <p className="font-medium text-xs truncate">{game.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{formatPrice(game.price)}</p>
                          </div>
                          <div className="ml-1 text-red-600 dark:text-red-400">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                              <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                            </svg>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Messages - compact */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-2 py-2 text-sm rounded-lg mb-2" role="alert">
              <p className="font-bold">Error</p>
              <p>{error}</p>
            </div>
          )}

          {actionError && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-2 py-2 text-sm rounded-lg mb-2" role="alert">
              <p className="font-bold">Warning</p>
              <p>{actionError}</p>
            </div>
          )}

          {/* Game Grid - takes remaining space */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden flex-1 flex flex-col">
            <div className="p-2 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Discover Games</h2>
              <button
                onClick={fetchRandomGames}
                disabled={loading}
                className="px-3 py-1 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex justify-center items-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-2"></div>
                    <p>Loading games...</p>
                  </div>
                </div>
              ) : games.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 p-3 h-full">
                  {games.map((game) => (
                    <div 
                      key={game.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-900 hover:shadow-md transition-shadow duration-200 flex flex-col"
                    >
                      <Link href={`/game/${game.id}`}>
                        <div className="relative w-full h-24">
                          <Image 
                            src={game.imageUrl} 
                            alt={`${game.name} cover`}
                            fill
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                            className="object-cover"
                            onError={(e) => {
                              const target = e.target as HTMLImageElement;
                              target.src = "https://placehold.co/600x400/222/fff?text=No+Image";
                            }}
                          />
                        </div>
                      </Link>
                      
                      <div className="p-2 flex-1 flex flex-col">
                        <Link href={`/game/${game.id}`}>
                          <h3 className="font-semibold text-sm mb-1 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200 line-clamp-1">{game.name}</h3>
                        </Link>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{formatPrice(game.price)}</p>
                        <p className="text-sm line-clamp-3 mb-2 flex-grow">{game.short_description}</p>
                        
                        <div className="flex flex-wrap gap-1 mb-2">
                          {splitString(game.genres).slice(0, 2).map((genre, idx) => (
                            <span 
                              key={idx}
                              className="bg-blue-50 text-blue-700 text-xs px-1 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300"
                            >
                              {genre}
                            </span>
                          ))}
                          {splitString(game.genres).length > 2 && (
                            <span className="text-xs text-gray-500">+{splitString(game.genres).length - 2} more</span>
                          )}
                        </div>
                        
                        <div className="flex justify-between gap-1 mt-auto">
                          <button
                            onClick={() => handleLike(game)}
                            disabled={loading || !!actionLoading[game.id]}
                            className="flex-1 py-1 px-2 text-xs bg-green-100 hover:bg-green-200 text-green-800 rounded-lg flex items-center justify-center gap-1 transition-colors duration-200 disabled:opacity-50"
                          >
                            {actionLoading[game.id] ? (
                              <div className="animate-spin h-3 w-3 border-b-2 border-green-800 rounded-full"></div>
                            ) : (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                              </svg>
                            )}
                            Like
                          </button>
                          <button
                            onClick={() => handleDislike(game)}
                            disabled={loading || !!actionLoading[game.id]}
                            className="flex-1 py-1 px-2 text-xs bg-red-100 hover:bg-red-200 text-red-800 rounded-lg flex items-center justify-center gap-1 transition-colors duration-200 disabled:opacity-50"
                          >
                            {actionLoading[game.id] ? (
                              <div className="animate-spin h-3 w-3 border-b-2 border-red-800 rounded-full"></div>
                            ) : (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                              </svg>
                            )}
                            Dislike
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex justify-center items-center h-full">
                  <div className="text-center">
                    <p className="mb-2">No games available. Try refreshing!</p>
                    <button
                      onClick={fetchRandomGames}
                      className="px-3 py-1 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                      Get Random Games
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
