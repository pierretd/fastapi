import { useState, useEffect } from 'react';
import Image from 'next/image';
import { useLocalStorage } from 'react-use';
import styles from './DiscoveryGrid.module.css';

// Import the GameCard component
import GameCard from './GameCard';

// Game interface matching our API
interface Game {
  id: string;
  payload: {
    name: string;
    price: number;
    short_description: string;
    detailed_description?: string;
    release_date: string;
    developers: string;
    genres: string;
    tags: string;
    platforms?: string;
    steam_appid?: number;
    header_image?: string;
  };
  score: number;
}

// Processed game interface that matches GameCard requirements
interface ProcessedGame {
  id: string;
  name: string;
  price: number;
  short_description: string;
  raw_description: string;
  detailed_description?: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  relevance?: number;
  imageUrl: string;
  platforms?: string;
  steam_appid?: number;
}

interface DiscoveryGridProps {
  initialGames?: Game[];
  loading?: boolean;
}

const DiscoveryGrid = ({ initialGames = [], loading = false }: DiscoveryGridProps) => {
  // State for games
  const [games, setGames] = useState<ProcessedGame[]>([]);
  
  // State for loading
  const [isLoading, setIsLoading] = useState(loading);
  
  // State for discovery mode
  const [discoveryMode, setDiscoveryMode] = useState<'preferences' | 'context'>('preferences');
  
  // State for context game (when in context mode)
  const [contextGameId, setContextGameId] = useState<string | null>(null);
  const [contextGameName, setContextGameName] = useState<string>('');
  
  // Local storage for liked and disliked games
  const [likedGames, setLikedGames] = useLocalStorage<string[]>('discovery_liked_games', []);
  const [dislikedGames, setDislikedGames] = useLocalStorage<string[]>('discovery_disliked_games', []);
  
  // Process games from API format to GameCard format
  const processGames = (apiGames: Game[]): ProcessedGame[] => {
    return apiGames.map((game) => ({
      id: game.id,
      name: game.payload.name,
      price: game.payload.price || 0,
      short_description: game.payload.short_description || '',
      raw_description: game.payload.short_description || '',
      detailed_description: game.payload.detailed_description,
      release_date: game.payload.release_date || '',
      developers: game.payload.developers || '',
      genres: game.payload.genres || '',
      tags: game.payload.tags || '',
      relevance: game.score,
      imageUrl: game.payload.header_image || '/placeholder.jpg',
      platforms: game.payload.platforms || '',
      steam_appid: game.payload.steam_appid,
    }));
  };
  
  // Load games on initial mount
  useEffect(() => {
    // Extract the refresh parameter from the URL if it exists
    const urlParams = new URLSearchParams(window.location.search);
    const refreshParam = urlParams.get('refresh');
    
    console.log(`Initial page load with refresh param: ${refreshParam}`);
    
    if (initialGames && initialGames.length > 0) {
      console.log('Using initial games from server-side props');
      setGames(processGames(initialGames));
      setIsLoading(false);
    } else {
      console.log('Fetching fresh games on page load');
      fetchDiscoveryGames();
    }
  }, [initialGames]);
  
  // Fetch discovery games based on preferences
  const fetchDiscoveryGames = async (action = 'refresh', gameId = '') => {
    try {
      setIsLoading(true);
      
      // Reset to preferences mode if previously in context mode
      setDiscoveryMode('preferences');
      setContextGameId(null);
      setContextGameName('');
      
      // Generate a truly unique random seed
      const timestamp = new Date().getTime();
      const randomFactor = Math.random().toString().substring(2, 10);
      const randomSeed = parseInt(timestamp.toString() + randomFactor.substring(0, 4), 10) % 1000000000;
      const nonce = Math.random().toString(36).substring(2, 15);
      
      console.log(`REFRESH: Fetching discovery games with timestamp: ${timestamp}, random seed: ${randomSeed}, nonce: ${nonce}`);
      
      // Add the unique values directly to the URL to force the browser to treat it as a unique request
      const response = await fetch(`/api/py/discovery-preferences?nocache=${timestamp}-${nonce}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
          'X-Requested-With': 'fetch-' + timestamp
        },
        body: JSON.stringify({
          liked_ids: likedGames,
          disliked_ids: dislikedGames,
          action: action,
          game_id: gameId,
          limit: 9,
          randomize: randomSeed, // Add this parameter to ensure random results each time
          _cache_buster: `${timestamp}-${nonce}` // Add an additional cache busting field
        }),
        cache: 'no-store', // Added to ensure we don't use the browser cache
        next: { revalidate: 0 } // Added to ensure Next.js doesn't cache the result
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`Received ${data.length} games from API, processing...`);
      
      // Log first 3 game IDs for debugging
      if (data.length > 0) {
        console.log('Sample games received:', data.slice(0, 3).map(g => `${g.id}: ${g.payload.name}`));
      }
      
      setGames(processGames(data));
    } catch (error) {
      console.error('Failed to fetch discovery games:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch discovery games based on context (similar games)
  const fetchContextGames = async (gameId: string) => {
    try {
      setIsLoading(true);
      
      // Get the selected game first to display its name
      const selectedGame = games.find(game => game.id === gameId);
      if (selectedGame) {
        setContextGameName(selectedGame.name);
      }
      
      // Set context mode
      setDiscoveryMode('context');
      setContextGameId(gameId);
      
      // Get excluded IDs (include the game itself plus liked/disliked)
      const excludedIds = [gameId, ...(likedGames || []), ...(dislikedGames || [])].join(',');
      
      // Add timestamp and nonce for cache busting
      const timestamp = new Date().getTime();
      const nonce = Math.random().toString(36).substring(2, 15);
      
      console.log(`Fetching context games for ${gameId} with cache busting: ${timestamp}-${nonce}`);
      
      const response = await fetch(`/api/py/discovery-context?gameId=${gameId}&limit=9&excludedIds=${excludedIds}&nocache=${timestamp}-${nonce}`, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
          'X-Requested-With': 'fetch-' + timestamp
        },
        cache: 'no-store',
        next: { revalidate: 0 }
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`Received ${data.length} context games, processing...`);
      
      // Log first 3 game IDs for debugging
      if (data.length > 0) {
        console.log('Sample context games:', data.slice(0, 3).map(g => `${g.id}: ${g.payload.name}`));
      }
      
      setGames(processGames(data));
    } catch (error) {
      console.error('Failed to fetch context discovery games:', error);
      // Fall back to preference-based discovery if context fails
      fetchDiscoveryGames();
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handler for liking a game
  const handleLike = async (game: ProcessedGame) => {
    // Add to liked games if not already there
    if (!likedGames?.includes(game.id)) {
      const updatedLikedGames = [...(likedGames || []), game.id];
      setLikedGames(updatedLikedGames);
      
      // Remove from disliked if it was there
      if (dislikedGames?.includes(game.id)) {
        const updatedDislikedGames = dislikedGames.filter(id => id !== game.id);
        setDislikedGames(updatedDislikedGames);
      }
      
      // If in context mode, refresh context with new exclusions
      if (discoveryMode === 'context' && contextGameId) {
        await fetchContextGames(contextGameId);
      } else {
        // Otherwise get new preference-based recommendations
        await fetchDiscoveryGames('like', game.id);
      }
    }
  };
  
  // Handler for disliking a game
  const handleDislike = async (game: ProcessedGame) => {
    // Add to disliked games if not already there
    if (!dislikedGames?.includes(game.id)) {
      const updatedDislikedGames = [...(dislikedGames || []), game.id];
      setDislikedGames(updatedDislikedGames);
      
      // Remove from liked if it was there
      if (likedGames?.includes(game.id)) {
        const updatedLikedGames = likedGames.filter(id => id !== game.id);
        setLikedGames(updatedLikedGames);
      }
      
      // If in context mode, refresh context with new exclusions
      if (discoveryMode === 'context' && contextGameId) {
        await fetchContextGames(contextGameId);
      } else {
        // Otherwise get new preference-based recommendations
        await fetchDiscoveryGames('dislike', game.id);
      }
    }
  };
  
  // Handler for discovering similar games
  const handleFindSimilar = async (game: ProcessedGame) => {
    await fetchContextGames(game.id);
  };
  
  // Handler for refreshing the discovery feed
  const handleRefresh = async () => {
    console.log("Refresh button clicked - forcing completely new games");
    
    // Add a timestamp to the URL to force a complete reload bypassing all caches
    const timestamp = new Date().getTime();
    
    // Create a more complex random value by combining timestamp digits and random numbers
    const randomPart1 = Math.floor(Math.random() * 1000000);
    const randomPart2 = Math.floor(Math.random() * 1000000);
    const combinedRandomValue = `${randomPart1}-${timestamp.toString().substring(8)}-${randomPart2}`;
    
    console.log(`Refreshing with unique value: ${combinedRandomValue}`);
    
    // Force a complete page reload to bypass all caches
    window.location.href = `${window.location.pathname}?refresh=${timestamp}-${combinedRandomValue}`;
  };
  
  // Handler for resetting preferences
  const handleReset = async () => {
    setLikedGames([]);
    setDislikedGames([]);
    
    // Reset to preferences mode
    setDiscoveryMode('preferences');
    setContextGameId(null);
    setContextGameName('');
    
    await fetchDiscoveryGames('reset');
  };
  
  // Helper functions required by GameCard
  const isNewRelease = (dateString: string) => {
    if (!dateString) return false;
    
    const releaseDate = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - releaseDate.getTime()) / (1000 * 60 * 60 * 24));
    
    return diffInDays <= 30; // Consider games released in the last 30 days as new
  };
  
  const formatPrice = (price: number) => {
    if (price === 0) return 'Free';
    return `$${price.toFixed(2)}`;
  };
  
  const splitString = (str: string) => {
    if (!str) return [];
    return str.split(',').map(item => item.trim());
  };
  
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Game Discovery</h1>
        
        {discoveryMode === 'context' && contextGameName && (
          <p className={styles.subtitle}>
            Showing games similar to <strong>{contextGameName}</strong>
            <button 
              className={styles.backButton} 
              onClick={() => fetchDiscoveryGames()}
              disabled={isLoading}
            >
              Back to Recommendations
            </button>
          </p>
        )}
        
        {discoveryMode !== 'context' && (
          <p className={styles.subtitle}>Find your next favorite game by liking or disliking games below</p>
        )}
        
        <div className={styles.controls}>
          <button 
            className={styles.refreshButton} 
            onClick={handleRefresh}
            disabled={isLoading}
          >
            Refresh Games
          </button>
          <button 
            className={styles.resetButton} 
            onClick={handleReset}
            disabled={isLoading}
          >
            Reset Preferences
          </button>
          
          {likedGames?.length > 0 && (
            <div className={styles.likedCount}>
              {likedGames.length} liked game{likedGames.length !== 1 ? 's' : ''}
            </div>
          )}
          
          {dislikedGames?.length > 0 && (
            <div className={styles.dislikedCount}>
              {dislikedGames.length} disliked game{dislikedGames.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      </div>
      
      <div className={styles.grid}>
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 9 }).map((_, index) => (
            <div key={`skeleton-${index}`} className={styles.skeleton}>
              <div className={styles.skeletonImage} />
              <div className={styles.skeletonTitle} />
              <div className={styles.skeletonDescription} />
            </div>
          ))
        ) : games.length > 0 ? (
          // Render games
          games.map((game, index) => (
            <GameCard
              key={game.id}
              game={game}
              onLike={handleLike}
              onDislike={handleDislike}
              isLoading={isLoading}
              isNewRelease={isNewRelease}
              formatPrice={formatPrice}
              splitString={splitString}
              index={index}
            />
          ))
        ) : (
          // No games found
          <div className={styles.noGames}>
            <p>No games found. Try refreshing or resetting your preferences.</p>
            <button 
              className={styles.refreshButton} 
              onClick={handleRefresh}
              disabled={isLoading}
            >
              Refresh Games
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default DiscoveryGrid; 