'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

interface GamePayload {
  name: string;
  price: number;
  short_description: string;
  detailed_description?: string;
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

// Interface for detailed game info
interface DetailedGame {
  id: string;
  name: string;
  price: number;
  short_description: string;
  detailed_description?: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  platforms: string;
  steam_appid: string;
}

// Filter options type
type FilterOption = 'all' | 'free' | 'price-asc' | 'price-desc' | 'newest';

export default function DiscoveryPage() {
  const router = useRouter();
  const [games, setGames] = useState<ApiGame[]>([]);
  const [filteredGames, setFilteredGames] = useState<ApiGame[]>([]);
  const [featuredGame, setFeaturedGame] = useState<ApiGame | null>(null);
  const [selectedGame, setSelectedGame] = useState<DetailedGame | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState('');
  const [limit, setLimit] = useState(12);
  const [filter, setFilter] = useState<FilterOption>('all');
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Function to get a random featured game
  const selectFeaturedGame = (games: ApiGame[]) => {
    if (games.length > 0) {
      const randomIndex = Math.floor(Math.random() * games.length);
      return games[randomIndex];
    }
    return null;
  };

  // Apply filters and search to games
  const applyFilters = useCallback(() => {
    if (!games.length) return;
    
    let result = [...games];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(game => 
        game.payload.name.toLowerCase().includes(query) || 
        game.payload.developers.toLowerCase().includes(query) ||
        game.payload.genres.toLowerCase().includes(query) ||
        game.payload.tags.toLowerCase().includes(query)
      );
    }
    
    // Apply selected filter
    switch (filter) {
      case 'free':
        result = result.filter(game => game.payload.price === 0);
        break;
      case 'price-asc':
        result = result.sort((a, b) => a.payload.price - b.payload.price);
        break;
      case 'price-desc':
        result = result.sort((a, b) => b.payload.price - a.payload.price);
        break;
      case 'newest':
        result = result.sort((a, b) => {
          const dateA = new Date(a.payload.release_date);
          const dateB = new Date(b.payload.release_date);
          return dateB.getTime() - dateA.getTime();
        });
        break;
      default:
        // 'all' - no additional filtering needed
        break;
    }
    
    setFilteredGames(result);
  }, [games, filter, searchQuery]);

  // Apply filters whenever filter or search query changes
  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const fetchRandomGames = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`/api/py/random-games?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      // Store the API response
      const apiGames: ApiGame[] = await response.json();
      
      // Fetch detailed information for each game including proper descriptions
      const gamesWithDetails = await Promise.all(
        apiGames.map(async (game) => {
          try {
            const detailResponse = await fetch(`/api/py/game/${game.id}`);
            if (detailResponse.ok) {
              const gameDetail = await detailResponse.json();
              // Update the game with proper description from the detail endpoint
              game.payload.short_description = gameDetail.short_description || game.payload.short_description;
            }
          } catch (err) {
            console.error(`Error fetching details for game ${game.id}:`, err);
          }
          return game;
        })
      );
      
      // Set featured game
      const featured = selectFeaturedGame(gamesWithDetails);
      setFeaturedGame(featured);
      
      // Set all games
      setGames(gamesWithDetails);
      
      // Initial filter application
      setFilteredGames(gamesWithDetails);
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
  
  // Function to fetch detailed game information
  const fetchGameDetails = async (gameId: string) => {
    setLoadingDetails(true);
    
    try {
      const response = await fetch(`/api/py/game/${gameId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch game details');
      }
      
      const gameData: DetailedGame = await response.json();
      setSelectedGame(gameData);
      setShowAboutModal(true);
    } catch (err) {
      console.error('Error fetching game details:', err);
      // If error, navigate to the game page instead
      router.push(`/game/${gameId}`);
    } finally {
      setLoadingDetails(false);
    }
  };

  // Format price display
  const formatPrice = (price: number): string => {
    if (price === 0) return 'Free to Play';
    return `$${price.toFixed(2)}`;
  };

  // Check if a game is new (released in the last 30 days)
  const isNewRelease = (releaseDate: string): boolean => {
    const release = new Date(releaseDate);
    const now = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(now.getDate() - 30);
    return release >= thirtyDaysAgo;
  };

  // Format date
  const formatDate = (dateString: string): string => {
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Generate skeleton loading cards
  const renderSkeletonCards = () => {
    return Array(limit).fill(0).map((_, index) => (
      <div key={`skeleton-${index}`} className="flex flex-col bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow animate-pulse">
        <div className="relative w-full h-40 bg-gray-300 dark:bg-gray-700"></div>
        <div className="p-4 flex-1 flex flex-col gap-2">
          <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4"></div>
          <div className="flex gap-1 mt-1">
            <div className="h-5 bg-gray-300 dark:bg-gray-700 rounded w-16"></div>
            <div className="h-5 bg-gray-300 dark:bg-gray-700 rounded w-16"></div>
          </div>
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full mt-2"></div>
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-2/3"></div>
          <div className="mt-auto pt-2">
            <div className="h-5 bg-gray-300 dark:bg-gray-700 rounded w-1/3"></div>
          </div>
        </div>
      </div>
    ));
  };

  // Render a game card
  const renderGameCard = (game: ApiGame, isFeatured: boolean = false) => (
    <div
      key={game.id}
      className={`
        flex flex-col bg-gradient-to-br from-white to-gray-100 dark:from-gray-800 dark:to-gray-900
        rounded-xl overflow-hidden shadow-md border border-gray-200 dark:border-gray-700
        hover:shadow-xl hover:scale-[1.02] transition-all duration-300
        ${isFeatured ? 'md:col-span-2' : ''}
      `}
    >
      {/* Game Title on top with improved styling */}
      <div className="p-4 pb-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 dark:from-blue-900/30 dark:to-purple-900/30">
        <Link href={`/game/${game.id}`}>
          <h3 className={`font-bold ${isFeatured ? 'text-xl' : 'text-lg'} text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 truncate`}>
            {game.payload.name}
          </h3>
        </Link>
      </div>
      
      {/* Game Image with improved styling */}
      <Link 
        href={`/game/${game.id}`}
        className={`
          relative block w-full
          ${isFeatured ? 'h-80' : 'h-52'}
        `}
      >
        <Image 
          src={`https://cdn.cloudflare.steamstatic.com/steam/apps/${game.payload.steam_appid}/header.jpg`}
          alt={`${game.payload.name} cover`}
          fill
          sizes={isFeatured 
            ? "(max-width: 768px) 100vw, 100vw" 
            : "(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          }
          className="object-cover transition-transform duration-300 hover:scale-105"
          onError={(e) => {
            // Fallback for image loading errors
            const target = e.target as HTMLImageElement;
            target.src = "https://placehold.co/600x400/222/fff?text=Game+Image";
          }}
        />
        
        {/* Status tags with improved styling */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2">
          {game.payload.price === 0 && (
            <span className="px-3 py-1 text-xs font-bold bg-green-500 text-white rounded-full shadow-lg">Free</span>
          )}
          {isNewRelease(game.payload.release_date) && (
            <span className="px-3 py-1 text-xs font-bold bg-blue-500 text-white rounded-full shadow-lg">New</span>
          )}
        </div>
      </Link>
      
      {/* Tags and Price with improved styling */}
      <div className="p-4 flex flex-col">
        {/* Tags row with improved styling */}
        <div className="flex flex-wrap gap-2 mb-3">
          {game.payload.genres.split(',').slice(0, 3).map((genre, index) => (
            <span 
              key={index} 
              className="px-3 py-1.5 text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full border border-gray-200 dark:border-gray-600"
            >
              {genre.trim()}
            </span>
          ))}
        </div>
        
        {/* Price with improved styling */}
        <div className="flex justify-end mt-1">
          <p className="px-4 py-1.5 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 font-bold rounded-full text-sm">
            {formatPrice(game.payload.price)}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-6xl">
        <div className="flex flex-col gap-6 md:gap-8">
          {/* Header with Navigation */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-1">Game Discovery</h1>
              <p className="text-gray-600 dark:text-gray-400">Find your next favorite game</p>
            </div>
            <div className="flex items-center gap-2">
              <Link href="/" className="text-blue-500 hover:underline">
                Home
              </Link>
              <span className="text-gray-400">/</span>
              <Link href="/search" className="text-blue-500 hover:underline">
                Search
              </Link>
            </div>
          </div>
          
          {/* Filters, Search and Refresh */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-4 md:p-6">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search games..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="flex flex-wrap gap-2">
                  <select 
                    value={filter}
                    onChange={(e) => setFilter(e.target.value as FilterOption)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700"
                  >
                    <option value="all">All Games</option>
                    <option value="free">Free Games</option>
                    <option value="price-asc">Price: Low to High</option>
                    <option value="price-desc">Price: High to Low</option>
                    <option value="newest">Newest Releases</option>
                  </select>
                  
                  <select 
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700"
                  >
                    <option value={6}>6 games</option>
                    <option value={12}>12 games</option>
                    <option value={24}>24 games</option>
                    <option value={36}>36 games</option>
                  </select>
                  
                  <button
                    onClick={handleRefresh}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center gap-2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                    </svg>
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
          
          {/* Featured Game */}
          {!loading && featuredGame && (
            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                Featured Game
              </h2>
              {renderGameCard(featuredGame, true)}
            </section>
          )}
          
          {/* Games Grid */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Discover Games</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {filteredGames.length} {filteredGames.length === 1 ? 'game' : 'games'} found
              </p>
            </div>
            
            {/* Loading State - Skeleton */}
            {loading && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {renderSkeletonCards()}
              </div>
            )}
            
            {/* Results */}
            {!loading && (
              <>
                {filteredGames.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredGames.map(game => renderGameCard(game))}
                  </div>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center">
                    <p className="text-lg mb-4">No games match your criteria.</p>
                    <button
                      onClick={() => {
                        setSearchQuery('');
                        setFilter('all');
                      }}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                      Reset Filters
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </div>
      
      {/* About This Game Modal */}
      {showAboutModal && selectedGame && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden max-w-3xl w-full max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h2 className="text-xl font-bold">{selectedGame.name}</h2>
              <button 
                onClick={() => setShowAboutModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              {loadingDetails ? (
                <div className="flex justify-center items-center py-10">
                  <svg className="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold mb-2">About This Game</h3>
                    {selectedGame.detailed_description ? (
                      <div 
                        className="prose prose-blue max-w-none dark:prose-invert"
                        dangerouslySetInnerHTML={{ __html: selectedGame.detailed_description }}
                      />
                    ) : (
                      <p className="text-gray-600 dark:text-gray-400">
                        {selectedGame.short_description || "No description available."}
                      </p>
                    )}
                  </div>
                  
                  <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-semibold">Developer:</p>
                      <p>{selectedGame.developers}</p>
                    </div>
                    <div>
                      <p className="font-semibold">Release Date:</p>
                      <p>{formatDate(selectedGame.release_date)}</p>
                    </div>
                    <div>
                      <p className="font-semibold">Price:</p>
                      <p>{formatPrice(selectedGame.price)}</p>
                    </div>
                    <div>
                      <p className="font-semibold">Genres:</p>
                      <p>{selectedGame.genres}</p>
                    </div>
                  </div>
                </>
              )}
            </div>
            
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <Link 
                href={`/game/${selectedGame.id}`}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                View Full Details
              </Link>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
