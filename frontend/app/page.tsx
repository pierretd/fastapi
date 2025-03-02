'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import ThemeToggle from './components/ThemeToggle';
import GameCard from './components/GameCard';
import './components/animations.css';

interface GamePayload {
  name: string;
  price: number;
  short_description: string;
  detailed_description?: string;
  document?: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  steam_appid: string;
  platforms?: string;
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
  raw_description: string;
  detailed_description?: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  platforms: string;
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
  const [refreshing, setRefreshing] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<{message: string, type: 'success' | 'error' | ''}>({message: '', type: ''});
  // New state variables for collapsible sections
  const [likedGamesExpanded, setLikedGamesExpanded] = useState(true);
  const [dislikedGamesExpanded, setDislikedGamesExpanded] = useState(true);
  const [preferencesFullscreen, setPreferencesFullscreen] = useState(false);
  // Add new state variables for collapsible sections
  const [likesDislikesExpanded, setLikesDislikesExpanded] = useState(true);
  const [recommendationsExpanded, setRecommendationsExpanded] = useState(true);
  const [gameGridExpanded, setGameGridExpanded] = useState(true);
  const [showGuide, setShowGuide] = useState(false); // Changed to false by default, will check localStorage
  const [showGuideOverlay, setShowGuideOverlay] = useState(false); // New state for overlay
  const [zenMode, setZenMode] = useState(false); // New state for zen mode
  
  // Grid layout state
  const [gridLayout, setGridLayout] = useState({
    cols: 3,
    rows: 3
  });
  
  // Remove the resize-related states
  const sidebarRef = useRef<HTMLDivElement>(null);
  const gameGridRef = useRef<HTMLDivElement>(null);

  // Fetch random games from the API - using useCallback
  const fetchRandomGames = useCallback(async () => {
    setLoading(true);
    setError('');
    setRefreshing(true);
    
    try {
      // Generate a unique random seed
      const timestamp = new Date().getTime();
      const randomFactor = Math.random().toString().substring(2, 10);
      const randomSeed = parseInt(timestamp.toString() + randomFactor.substring(0, 4), 10) % 1000000000;
      const nonce = Math.random().toString(36).substring(2, 15);
      
      console.log(`Home page: Using random seed: ${randomSeed} for game discovery`);
      
      // Use discovery-preferences instead of random-games for better randomization
      const response = await fetch(`/api/py/discovery-preferences?nocache=${timestamp}-${nonce}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        body: JSON.stringify({
          liked_ids: [],
          disliked_ids: [],
          action: 'refresh',
          game_id: '',
          limit: 9,
          randomize: randomSeed,
          _cache_buster: `${timestamp}-${nonce}`
        }),
        cache: 'no-store',
        next: { revalidate: 0 }
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Home page: Got ${data.length} games from discovery API, first few IDs: ${data.slice(0, 3).map((g: ApiGame) => g.id).join(', ')}`);
      
      // Process the games
      const processedGames = processApiGames(data);
      
      setGames(processedGames);
    } catch (err) {
      console.error('Error fetching random games:', err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Fetch games on component mount
  useEffect(() => {
    // Load liked/disliked games from localStorage first
    loadLikedGames();
    loadDislikedGames();
    
    // Extract random value from URL if present
    const urlParams = new URLSearchParams(window.location.search);
    const randomParam = urlParams.get('random');
    
    if (randomParam) {
      console.log(`Home page: Loading with random parameter: ${randomParam}`);
    }
    
    // Call fetchRandomGames directly here as component mounts
    fetchRandomGames();
  }, [fetchRandomGames]);

  // Load liked and disliked games from local storage
  const loadLikedGames = () => {
    try {
      const storedLikedGames = localStorage.getItem('likedGames');
      if (storedLikedGames) {
        setLikedGames(JSON.parse(storedLikedGames));
      }
    } catch (error) {
      console.error('Error loading liked games:', error);
    }
  };

  const loadDislikedGames = () => {
    try {
      const storedDislikedGames = localStorage.getItem('dislikedGames');
      if (storedDislikedGames) {
        setDislikedGames(JSON.parse(storedDislikedGames));
      }
    } catch (error) {
      console.error('Error loading disliked games:', error);
    }
  };

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

  // Handle localStorage for guide visibility on mount
  useEffect(() => {
    // Check if the guide has been hidden before
    const hideGuide = localStorage.getItem('hideRecommendationsGuide');
    if (hideGuide === 'true') {
      // User has dismissed the guide before
      setShowGuide(false);
      setShowGuideOverlay(false);
    } else {
      // First-time user or they haven't dismissed the guide
      setShowGuide(true);
      setShowGuideOverlay(true); // Show as overlay on first visit
      setLikesDislikesExpanded(true);
    }
  }, []);

  // Fetch game recommendations based on liked and disliked games
  const fetchRecommendations = async (liked: string[], disliked: string[]) => {
    setLoading(true);
    setError('');
    
    try {
      // Generate a unique random seed for recommendations too
      const timestamp = new Date().getTime();
      const randomFactor = Math.random().toString().substring(2, 10);
      const randomSeed = parseInt(timestamp.toString() + randomFactor.substring(0, 4), 10) % 1000000000;
      const nonce = Math.random().toString(36).substring(2, 15);
      
      console.log(`Home page: Using random seed: ${randomSeed} for recommendations with ${liked.length} liked and ${disliked.length} disliked games`);
      
      const response = await fetch(`/api/py/discovery-preferences?nocache=${timestamp}-${nonce}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        body: JSON.stringify({
          liked_ids: liked,
          disliked_ids: disliked,
          action: 'refresh',
          game_id: '',
          limit: 9,
          randomize: randomSeed,
          _cache_buster: `${timestamp}-${nonce}`
        }),
        cache: 'no-store',
        next: { revalidate: 0 }
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Home page: Got ${data.length} recommendation games, first few IDs: ${data.slice(0, 3).map((g: ApiGame) => g.id).join(', ')}`);
      
      // Process the games
      const processedGames = processApiGames(data);
      
      setGames(processedGames);
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
      // Create new array to avoid mutation
      const newLikedGames = [...likedGames, game];
      
      // Update state in one go
      setLikedGames(newLikedGames);
      
      // Remove from current games display
      setGames(prevGames => prevGames.filter(g => g.id !== game.id));
      
      // Show feedback message
      setFeedbackMessage({
        message: "Liked! Finding similar games...",
        type: "success"
      });
      
      // Update recommendations based on new likes/dislikes
      await fetchRecommendations(
          newLikedGames.map(g => g.id), 
          dislikedGames.map(g => g.id)
        );
      
      // Clear feedback message after 3 seconds
      setTimeout(() => {
        setFeedbackMessage({message: '', type: ''});
      }, 3000);
      
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
      // Create new array to avoid mutation
      const newDislikedGames = [...dislikedGames, game];
      
      // Update state in one go
      setDislikedGames(newDislikedGames);
      
      // Remove from current games display
      setGames(prevGames => prevGames.filter(g => g.id !== game.id));
      
      // Show feedback message
      setFeedbackMessage({
        message: "Noted! We&apos;ll avoid similar titles.",
        type: "error"
      });
      
      // Update recommendations based on new likes/dislikes
      await fetchRecommendations(
          likedGames.map(g => g.id), 
          newDislikedGames.map(g => g.id)
        );
      
      // Clear feedback message after 3 seconds
      setTimeout(() => {
        setFeedbackMessage({message: '', type: ''});
      }, 3000);
      
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

  // Split comma-separated string into array
  const splitString = (str: string): string[] => {
    return str ? str.split(',').map(item => item.trim()).filter(Boolean) : [];
  };
  
  // Format price
  const formatPrice = (price: number): string => {
    return price === 0 ? 'Free to Play' : `$${price.toFixed(2)} USD`;
  };

  // Process API games into our internal format
  const processApiGames = (apiGames: ApiGame[]): Game[] => {
    return apiGames.map(apiGame => {
      // Get the descriptions from Qdrant
      const shortDesc = apiGame.payload.short_description;
      const detailedDesc = apiGame.payload.detailed_description;
      const documentDesc = apiGame.payload.document;
      
      console.log("API Game:", apiGame.payload.name);
      console.log("Short description:", shortDesc);
      console.log("Detailed description:", detailedDesc);
      console.log("Document field:", documentDesc);
      
      const processedGame = {
        id: apiGame.id,
        name: apiGame.payload.name,
        price: apiGame.payload.price,
        short_description: shortDesc || '',
        raw_description: documentDesc || '',
        detailed_description: detailedDesc || '',
        release_date: apiGame.payload.release_date,
        developers: apiGame.payload.developers,
        genres: apiGame.payload.genres,
        tags: apiGame.payload.tags,
        platforms: apiGame.payload.platforms || '',
        relevance: apiGame.score,
        // Construct Steam store image URL using the appid with fallback
        imageUrl: apiGame.payload.steam_appid 
          ? `https://cdn.cloudflare.steamstatic.com/steam/apps/${apiGame.payload.steam_appid}/header.jpg`
          : '/placeholder-game.jpg'
      };
      
      return processedGame;
    });
  };

  // Function to check if a game was released in the last 30 days
  const isNewRelease = (dateString: string): boolean => {
    if (!dateString) return false;
    const releaseDate = new Date(dateString);
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    return releaseDate >= thirtyDaysAgo;
  };

  // Handle removing a game from liked games list
  const handleRemoveFromLiked = (game: Game) => {
    setLikedGames(prev => prev.filter(g => g.id !== game.id));
  };

  // Handle removing a game from disliked games list
  const handleRemoveFromDisliked = (game: Game) => {
    setDislikedGames(prev => prev.filter(g => g.id !== game.id));
  };

  // Update grid layout based on screen size
  useEffect(() => {
    const updateGridLayout = () => {
      let cols = 3;
      if (window.innerWidth < 640) {
        cols = 1;
      } else if (window.innerWidth < 1024) {
        cols = 2;
      }
      
      // Calculate rows needed to fit all games without scrolling
      const rows = Math.min(3, Math.ceil(games.length / cols));
      
      setGridLayout({ cols, rows });
    };
    
    // Initial update
    updateGridLayout();
    
    // Update on resize
    window.addEventListener('resize', updateGridLayout);
    
    return () => {
      window.removeEventListener('resize', updateGridLayout);
    };
  }, [games.length]);

  // Function to refresh the game list with new random games
  const handleRefreshGames = () => {
    const timestamp = new Date().getTime();
    const randomNumber1 = Math.floor(Math.random() * 1000000);
    const randomNumber2 = Math.floor(Math.random() * 1000000);
    const timestampLastDigits = timestamp % 1000;
    
    // Combine multiple factors for a more unique random value
    const uniqueRandomValue = `${randomNumber1}-${timestampLastDigits}-${randomNumber2}`;
    
    console.log(`Home page: Refreshing games with a new random value: ${uniqueRandomValue}`);
    
    // Force a complete page reload with the new unique random value
    window.location.href = `${window.location.pathname}?random=${uniqueRandomValue}`;
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-black/30 border-b border-white/10 shadow-md animate-fadeIn">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Brand */}
            <div className="flex items-center">
              <Link href="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#3CCBA0] to-[#3B82F6] flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white">
                    <path d="M11.25 5.337c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.036 1.007-1.875 2.25-1.875S15 2.34 15 3.375c0 .369-.128.713-.349 1.003-.215.283-.401.604-.401.959 0 .332.278.598.61.578 1.91-.114 3.79-.342 5.632-.676a.75.75 0 01.878.645 49.17 49.17 0 01.376 5.452.657.657 0 01-.66.664c-.354 0-.675-.186-.958-.401a1.647 1.647 0 00-1.003-.349c-1.035 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401.31 0 .557.262.534.571a48.774 48.774 0 01-.595 4.845.75.75 0 01-.61.61c-1.82.317-3.673.533-5.555.642a.58.58 0 01-.611-.581c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.035-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349.283.215.604.401.959.401a.641.641 0 01-.658.643 49.118 49.118 0 01-4.708-.36.75.75 0 01-.645-.878c.293-1.614.504-3.257.629-4.924A.53.53 0 005.337 15c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.036 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.369 0 .713.128 1.003.349.283.215.604.401.959.401a.656.656 0 00.659-.663 47.703 47.703 0 00-.31-4.82.75.75 0 01.83-.832c1.343.155 2.703.254 4.077.294a.64.64 0 00.657-.642z" />
                  </svg>
                </div>
                <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-100 to-gray-300">
                  GameVault
                </span>
              </Link>
        </div>

            {/* Desktop Navigation Links */}
            <nav className="hidden md:flex space-x-1">
              {['Discover', 'Popular', 'Categories', 'Wishlist'].map((item) => (
                <Link
                  key={item}
                  href={`/${item.toLowerCase()}`}
                  className="px-4 py-2 text-sm font-medium text-white/80 hover:text-white rounded-full hover:bg-white/5 transition-all duration-200 interactive-element"
                >
                  {item}
                </Link>
              ))}
            </nav>
            
            {/* Right Section: Search & Profile */}
            <div className="flex items-center space-x-4">
              {/* Search Button */}
              <Link 
                href="/search" 
                className="glass-effect p-2 rounded-full hover:bg-white/15 transition-colors interactive-element"
                aria-label="Search"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white/90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </Link>
              
              {/* Advanced Search Link */}
              <Link 
                href="/advanced-search" 
                className="glass-effect px-3 py-2 rounded-lg hover:bg-white/15 transition-colors interactive-element text-white/90 text-sm font-medium"
              >
                Advanced Search
              </Link>
              
              {/* Profile Button */}
              <div className="relative">
                <button
                  className="glass-effect rounded-full w-8 h-8 flex items-center justify-center hover:bg-white/15 transition-colors interactive-element"
                  aria-label="Profile"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white/90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </button>
              </div>
              
              {/* Theme Toggle */}
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      <div className={`max-w-7xl mx-auto w-full px-4 pb-6 flex flex-col`}>
        {/* Feedback Message - Enhanced with glassmorphism */}
        {feedbackMessage && feedbackMessage.message && (
          <div className="glass-card p-4 mb-0 relative overflow-hidden animate-slideUp">
            <div className="flex items-center">
              <div className="mr-4 flex-shrink-0">
                {feedbackMessage.type === 'success' ? (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#3CCBA0]/20 to-[#4CAF50]/20 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-[#4CAF50]" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#F87171]/20 to-[#E57373]/20 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-[#E57373]" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
              <div className="flex-1">
                <p className="text-white font-medium">{feedbackMessage.message}</p>
              </div>
              <button
                onClick={() => setFeedbackMessage({ message: '', type: '' })}
                className="ml-4 text-white/60 hover:text-white/90 transition-colors focus:outline-none"
                aria-label="Dismiss message"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            {/* Gradient line at bottom */}
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#3CCBA0]/0 via-[#3CCBA0]/70 to-[#3CCBA0]/0"></div>
          </div>
        )}

        {/* Page Title Section */}
        <div className="w-full flex flex-col md:flex-row md:items-center md:justify-between mt-4 mb-4">
          <div className="flex flex-col items-center md:items-start animate-fadeIn">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-[#3CCBA0] animate-pulse-subtle">
                Game Discovery
              </h1>
              <button
                onClick={handleRefreshGames}
                className="flex items-center space-x-1 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
                title="Get fresh recommendations"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh Games</span>
              </button>
              
              {/* Clear Preferences Button */}
              {(likedGames.length > 0 || dislikedGames.length > 0) && (
                <button
                  onClick={() => {
                    if (confirm("This will clear all your liked and disliked games. Are you sure?")) {
                      handleResetHistory();
                    }
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-300 hover:text-red-200 rounded-lg transition-colors"
                  title="Clear all your preferences"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <span>Clear Preferences</span>
                </button>
              )}
            </div>
            <div className="flex justify-center">
              <div className="h-1.5 w-32 bg-gradient-to-r from-[#3CCBA0] to-[#3B82F6] rounded-full animate-expandWidth"></div>
            </div>
          </div>
          <p className="text-white/90 text-base md:text-xl mt-3 md:mt-0 md:ml-8 max-w-2xl text-center md:text-left font-semibold animate-slideInRight">
            Discover new games tailored to your preferences. Like or dislike games to improve future recommendations.
            <span className="block h-0.5 w-0 md:w-3/4 bg-gradient-to-r from-[#3CCBA0]/0 via-[#3CCBA0]/70 to-[#3CCBA0]/0 mt-1.5 animate-expandWidth"></span>
          </p>
        </div>

        {/* Guide Overlay Modal - New component that appears on first visit */}
        {showGuideOverlay && (
          <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4 md:p-6 animate-fadeIn">
            <div className="max-w-4xl w-full bg-gradient-to-r from-indigo-900/80 to-indigo-950/80 backdrop-blur-md border border-indigo-300/20 rounded-xl shadow-2xl animate-slideUp">
              <div className="flex justify-between items-center bg-indigo-700/30 border-b border-indigo-300/20 rounded-t-xl px-6 py-4">
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 text-indigo-200 mr-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <h3 className="text-2xl font-bold text-indigo-100">Welcome to GameVault</h3>
                </div>
                {/* Add close button */}
                <button
                  onClick={() => {
                    localStorage.setItem('hideRecommendationsGuide', 'true');
                    setShowGuideOverlay(false);
                    setShowGuide(false);
                  }}
                  className="p-2 rounded-full hover:bg-indigo-600/50 transition-colors focus:outline-none group"
                  aria-label="Close guide"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-200 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="px-8 py-8">
                <h2 className="text-3xl font-extrabold text-white text-center mb-8 tracking-tight">How Recommendations Work</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-7 mb-8">
                  <div className="flex">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full bg-green-500/30 flex items-center justify-center mr-4 border border-green-400/30">
                      <span className="text-xl font-bold text-green-300 flex items-center justify-center w-full h-full">1</span>
                    </div>
                    <div>
                      <p className="text-lg leading-relaxed text-white/95">
                        <span className="font-semibold text-green-300">Like</span> games that match your taste - our AI will recommend more similar titles.
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-500/30 flex items-center justify-center mr-4 border border-red-400/30">
                      <span className="text-xl font-bold text-red-300 flex items-center justify-center w-full h-full">2</span>
                    </div>
                    <div>
                      <p className="text-lg leading-relaxed text-white/95">
                        <span className="font-semibold text-red-300">Dislike</span> games that don&apos;t interest you - helps our AI avoid similar recommendations.
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full bg-indigo-500/30 flex items-center justify-center mr-4 border border-indigo-400/30">
                      <span className="text-xl font-bold text-indigo-300 flex items-center justify-center w-full h-full">3</span>
                    </div>
                    <div>
                      <p className="text-lg leading-relaxed text-white/95">
                        <span className="font-semibold text-indigo-300">The more you rate</span>, the smarter our recommendations become!
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full bg-purple-500/30 flex items-center justify-center mr-4 border border-purple-400/30">
                      <span className="text-xl font-bold text-purple-300 flex items-center justify-center w-full h-full">4</span>
                    </div>
                    <div>
                      <p className="text-lg leading-relaxed text-white/95">
                        <span className="font-semibold text-purple-300">Your liked and disliked games</span> will appear in the preferences section below.
                      </p>
                    </div>
                  </div>
                </div>
                  
                <div className="mx-auto max-w-3xl mb-10">
                  <div className="text-center px-6 py-6 border border-blue-500/30 bg-blue-500/10 rounded-xl">
                    <p className="text-lg text-blue-200 leading-relaxed">
                      <span className="font-bold text-xl inline-block mb-2">💡 Pro tip:</span><br/>
                      Hover over any game card to reveal more details about the game. Like or dislike games to receive better personalized recommendations.
                    </p>
                  </div>
                </div>
                  
                <div className="flex justify-center">
                  <button 
                    onClick={() => {
                      localStorage.setItem('hideRecommendationsGuide', 'true');
                      setShowGuideOverlay(false);
                      setShowGuide(false);
                    }}
                    className="px-8 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold text-xl rounded-xl shadow-xl hover:from-indigo-600 hover:to-purple-700 transition-all transform hover:scale-105 active:scale-95 flex items-center"
                  >
                    <span className="mr-2">I get it, let me browse games!</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Likes and Dislikes Section - Made collapsible */}
        <div className="w-full mb-6 mt-3 bg-[#F8FAFC]/5 backdrop-blur-sm border border-dashed border-white/20 rounded-xl">
          {/* Toggle button for likes/dislikes section */}
          <div className="flex justify-between items-center px-3 py-1.5 cursor-pointer" onClick={() => setLikesDislikesExpanded(!likesDislikesExpanded)}>
            <h2 className="text-sm sm:text-base font-semibold text-white">Your Game Preferences</h2>
            <div className="flex items-center">
              {/* Add a button to show the guide again */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowGuideOverlay(true);
                }}
                className="mr-2 text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded hover:bg-indigo-500/20 transition-colors"
              >
                <span className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  How it works
                </span>
              </button>
              
              {/* Add Clear Preferences button */}
              {(likedGames.length > 0 || dislikedGames.length > 0) && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm("This will clear all your liked and disliked games. Are you sure?")) {
                      handleResetHistory();
                    }
                  }}
                  className="mr-2 text-xs text-red-400 hover:text-red-300 bg-red-500/10 px-2 py-0.5 rounded hover:bg-red-500/20 transition-colors"
                >
                  <span className="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Clear Preferences
                  </span>
                </button>
              )}
              
              <button className="p-1 rounded-full hover:bg-white/10 transition-colors">
                {likesDislikesExpanded ? (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white/70">
                    <path fillRule="evenodd" d="M11.47 7.72a.75.75 0 011.06 0l7.5 7.5a.75.75 0 11-1.06 1.06L12 9.31l-6.97 6.97a.75.75 0 01-1.06-1.06l7.5-7.5z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white/70">
                    <path fillRule="evenodd" d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75 0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06 1.06l-7.5 7.5z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          
          {/* Collapsible content - Modified to be shorter with images in a row at 50% size */}
          {likesDislikesExpanded && (
            <div className="px-3 py-2 text-center">
              {/* Add placeholder message when no games in preferences */}
              {likedGames.length === 0 && dislikedGames.length === 0 ? (
                <div className="w-full py-2 flex items-center justify-center">
                  <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-400/20 flex items-center justify-center mr-3 relative">
                    {/* Game controller icon */}
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="6" width="20" height="12" rx="2" />
                      <circle cx="12" cy="12" r="2" />
                      <path d="M5 10h2" />
                      <path d="M17 10h2" />
                      <path d="M6 16v-2" />
                    </svg>
                    
                    {/* Small thumbs up/down notification dots */}
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full"></div>
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
                  </div>
                  <p className="text-white/60 text-sm">
                    <span className="text-indigo-400 font-medium">Ready to explore games?</span><br />
                    Like or dislike recommendations below to build your profile.
                  </p>
                </div>
              ) : (
                <div className="flex flex-col space-y-2">
                  {/* Liked Games Section */}
                  {likedGames.length > 0 && (
                    <div className="w-full">
                      <h4 className="text-xs font-medium text-green-400 text-left mb-1">Liked:</h4>
                      <div className="flex flex-row overflow-x-auto pb-2 gap-2">
                        {likedGames.map(game => (
                          <div key={game.id} className="relative flex-shrink-0 w-1/2 sm:w-1/3 md:w-1/5 max-w-[120px] group">
                            <Image 
                              src={game.imageUrl} 
                              alt={game.name} 
                              width={120}
                              height={45}
                              className="w-full h-auto object-cover rounded-md border border-white/10"
                            />
                            <button 
                              onClick={() => handleRemoveFromLiked(game)}
                              className="absolute top-1 right-1 bg-black/70 p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                              title="Remove from liked"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-white/80" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Disliked Games Section */}
                  {dislikedGames.length > 0 && (
                    <div className="w-full">
                      <h4 className="text-xs font-medium text-red-400 text-left mb-1">Disliked:</h4>
                      <div className="flex flex-row overflow-x-auto pb-2 gap-2">
                        {dislikedGames.map(game => (
                          <div key={game.id} className="relative flex-shrink-0 w-1/2 sm:w-1/3 md:w-1/5 max-w-[120px] group">
                            <Image 
                              src={game.imageUrl} 
                              alt={game.name}
                              width={120}
                              height={45}
                              className="w-full h-auto object-cover rounded-md border border-white/10 opacity-70"
                            />
                            <button 
                              onClick={() => handleRemoveFromDisliked(game)}
                              className="absolute top-1 right-1 bg-black/70 p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                              title="Remove from disliked"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-white/80" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Game Grid - With transition for when panels are collapsed */}
        <div className="w-full relative bg-gradient-to-br from-neutral-900 to-black rounded-xl border border-white/5 shadow-lg flex-grow transition-all duration-300 mt-8">
          {/* Game Grid Toggle Button */}
          <div className="flex justify-between items-center px-5 py-2 cursor-pointer">
            <div className="flex items-center flex-1" onClick={() => setGameGridExpanded(!gameGridExpanded)}>
              <div className="mr-3 flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-[#3B82F6]/20 to-[#6366F1]/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-[#3B82F6]" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                </svg>
              </div>
              <div className="flex flex-col md:flex-row md:items-center flex-1">
                <div className="flex items-center">
                  <h3 className="text-white font-semibold text-base md:text-lg md:mr-4">Game Recommendations</h3>
                </div>
                
                <div className="flex items-center">
                  <p className="text-white/70 text-xs sm:text-sm max-w-xl md:border-l md:border-white/10 md:pl-4 md:ml-4">
                    Select games you like and dislike to improve your personalized recommendation results.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center">
              {/* Expand/Collapse Button */}
              <button 
                className="p-1 rounded-full hover:bg-white/10 transition-colors ml-1"
                onClick={(e) => {
                  e.stopPropagation();
                  setGameGridExpanded(!gameGridExpanded);
                }}
              >
                {gameGridExpanded ? (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-white/70">
                    <path fillRule="evenodd" d="M11.47 7.72a.75.75 0 011.06 0l7.5 7.5a.75.75 0 11-1.06 1.06L12 9.31l-6.97 6.97a.75.75 0 01-1.06-1.06l7.5-7.5z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-white/70">
                    <path fillRule="evenodd" d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75 0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06 1.06l-7.5 7.5z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Collapsible game grid content */}
          {gameGridExpanded && (
            <div className={`game-grid-container w-full p-0 m-0 ${zenMode ? 'zen-mode-active' : ''}`}>
              {/* Loading state */}
              {loading && (
                <div className="flex-1 flex flex-col items-center justify-center p-8">
                  <div className="w-16 h-16 border-4 border-t-transparent border-blue-500 rounded-full animate-spin mb-4"></div>
                  <h3 className="text-xl font-semibold text-white mb-2">Finding Games</h3>
                  <p className="text-white/60 text-sm text-center max-w-md">Searching the Steam database for games that match your preferences...</p>
                </div>
              )}
                
              {/* Error state */}
              {!loading && error && (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                  <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">Error Loading Games</h3>
                  <p className="text-white/60 text-sm mb-4 max-w-md">{error}</p>
                  <button
                    onClick={handleRefreshGames}
                    className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              )}
              
              {/* Game grid - auto-fit responsive grid */}
              {!loading && !error && games.length > 0 && (
                <div className="w-full h-full bg-black p-0 overflow-hidden" ref={gameGridRef}>
                  <div 
                    className={`w-full h-full grid gap-0 ${zenMode ? 'zen-mode-grid' : ''}`}
                    style={{ 
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gridAutoRows: 'minmax(180px, 1fr)',
                      background: 'black',
                      margin: 0,
                      padding: 0
                    }}
                  >
                    {games.slice(0, 9).map((game) => (
                      <GameCard
                        key={game.id}
                        game={game}
                        onLike={() => handleLike(game)}
                        onDislike={() => handleDislike(game)}
                        isNewRelease={isNewRelease}
                        formatPrice={formatPrice}
                        splitString={splitString}
                        zenMode={zenMode}
                      />
                    ))}
                  </div>
                </div>
              )}
              
              {/* Empty state */}
              {!loading && !error && games.length === 0 && (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                  <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">No Games Found</h3>
                  <p className="text-white/60 mb-4 max-w-md">We couldn&apos;t find any games matching your preferences. Try refreshing or adjusting your search criteria.</p>
                  <button
                    onClick={handleRefreshGames}
                    className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
                  >
                    Refresh Games
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer with Glassmorphism */}
      <footer className="mt-auto backdrop-blur-md bg-black/30 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Logo and description */}
            <div className="md:col-span-1">
              <Link href="/" className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#3CCBA0] to-[#3B82F6] flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white">
                    <path d="M11.25 5.337c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.036 1.007-1.875 2.25-1.875S15 2.34 15 3.375c0 .369-.128.713-.349 1.003-.215.283-.401.604-.401.959 0 .332.278.598.61.578 1.91-.114 3.79-.342 5.632-.676a.75.75 0 01.878.645 49.17 49.17 0 01.376 5.452.657.657 0 01-.66.664c-.354 0-.675-.186-.958-.401a1.647 1.647 0 00-1.003-.349c-1.035 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401.31 0 .557.262.534.571a48.774 48.774 0 01-.595 4.845.75.75 0 01-.61.61c-1.82.317-3.673.533-5.555.642a.58.58 0 01-.611-.581c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.035-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349.283.215.604.401.959.401a.641.641 0 01-.658.643 49.118 49.118 0 01-4.708-.36.75.75 0 01-.645-.878c.293-1.614.504-3.257.629-4.924A.53.53 0 005.337 15c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.036 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.369 0 .713.128 1.003.349.283.215.604.401.959.401a.656.656 0 00.659-.663 47.703 47.703 0 00-.31-4.82.75.75 0 01.83-.832c1.343.155 2.703.254 4.077.294a.64.64 0 00.657-.642z" />
                  </svg>
                </div>
                <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-100 to-gray-300">
                  GameVault
                </span>
              </Link>
              <p className="text-white/60 text-sm mb-6">
                Your personal gaming discovery platform. Find your next favorite game with our AI-powered recommendation system.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-white/60 hover:text-white transition-colors" aria-label="Twitter">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
                  </svg>
                </a>
                <a href="https://github.com" className="text-white/60 hover:text-white transition-colors" aria-label="GitHub">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.031 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.244 0-1.093.349-.959.604-.959.604z" />
                  </svg>
                </a>
              </div>
            </div>
            
            {/* Navigation Links */}
            <div className="md:col-span-3 grid grid-cols-2 md:grid-cols-3 gap-8">
              <div>
                <h3 className="text-white font-semibold mb-4">Navigation</h3>
                <ul className="space-y-2">
                  {['Home', 'Discover', 'Popular', 'Categories', 'Wishlist'].map((item) => (
                    <li key={item}>
                      <Link 
                        href={`/${item.toLowerCase() === 'home' ? '' : item.toLowerCase()}`}
                        className="text-white/60 hover:text-white transition-colors text-sm"
                      >
                        {item}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h3 className="text-white font-semibold mb-4">Resources</h3>
                <ul className="space-y-2">
                  {['About', 'Blog', 'Support', 'Developers', 'Privacy Policy'].map((item) => (
                    <li key={item}>
                      <Link 
                        href={`/${item.toLowerCase().replace(' ', '-')}`}
                        className="text-white/60 hover:text-white transition-colors text-sm"
                      >
                        {item}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h3 className="text-white font-semibold mb-4">Contact</h3>
                <ul className="space-y-2">
                  <li className="flex items-start space-x-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white/60 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <span className="text-white/60 text-sm">contact@gamevault.com</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white/60 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="text-white/60 text-sm">123 Gaming Street, Digital City</span>
                  </li>
                </ul>
                
                <div className="mt-6">
                  <h3 className="text-white font-semibold mb-3">Join our newsletter</h3>
                  <div className="flex">
                    <input 
                      type="email" 
                      placeholder="Your email" 
                      className="glass-effect py-2 px-3 rounded-l-lg w-full text-sm placeholder:text-white/40 focus:outline-none" 
                    />
                    <button className="bg-gradient-to-r from-[#3CCBA0] to-[#4CAF50] text-white py-2 px-4 rounded-r-lg text-sm font-medium">
                      Subscribe
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Copyright */}
          <div className="mt-10 pt-6 border-t border-white/10 flex flex-col md:flex-row justify-between items-center">
            <p className="text-white/40 text-sm">
              © {new Date().getFullYear()} GameVault. All rights reserved.
            </p>
            <div className="mt-4 md:mt-0">
              <ul className="flex space-x-6">
                <li>
                  <Link href="/terms" className="text-white/40 hover:text-white/70 text-xs">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link href="/privacy" className="text-white/40 hover:text-white/70 text-xs">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="/cookies" className="text-white/40 hover:text-white/70 text-xs">
                    Cookie Policy
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
