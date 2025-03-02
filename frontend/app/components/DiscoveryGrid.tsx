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
    }));
  };
  
  // Load games on initial mount
  useEffect(() => {
    if (initialGames && initialGames.length > 0) {
      setGames(processGames(initialGames));
      setIsLoading(false);
    } else {
      fetchDiscoveryGames();
    }
  }, [initialGames]);
  
  // Fetch discovery games based on preferences
  const fetchDiscoveryGames = async (action = 'refresh', gameId = '') => {
    try {
      setIsLoading(true);
      
      const response = await fetch('/api/py/discovery-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          liked_ids: likedGames,
          disliked_ids: dislikedGames,
          action: action,
          game_id: gameId,
          limit: 9
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      setGames(processGames(data));
    } catch (error) {
      console.error('Failed to fetch discovery games:', error);
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
      
      // Fetch new discovery games
      await fetchDiscoveryGames('like', game.id);
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
      
      // Fetch new discovery games
      await fetchDiscoveryGames('dislike', game.id);
    }
  };
  
  // Handler for refreshing the discovery feed
  const handleRefresh = async () => {
    await fetchDiscoveryGames('refresh');
  };
  
  // Handler for resetting preferences
  const handleReset = async () => {
    setLikedGames([]);
    setDislikedGames([]);
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
        <p className={styles.subtitle}>Find your next favorite game by liking or disliking games below</p>
        
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
            No games found. Try resetting your preferences or try again later.
          </div>
        )}
      </div>
    </div>
  );
};

export default DiscoveryGrid; 