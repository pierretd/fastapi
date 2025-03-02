import { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import Link from 'next/link';

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
  relevance?: number;
  imageUrl: string;
  platforms?: string;
  steam_appid?: number;
}

interface DetailedGame extends Game {
  similar_games?: any[];
}

interface GameCardProps {
  game: Game;
  onLike: (game: Game) => void;
  onDislike: (game: Game) => void;
  isLoading?: boolean;
  isNewRelease: (dateString: string) => boolean;
  formatPrice: (price: number) => string;
  splitString: (str: string) => string[];
  index?: number;
  zenMode?: boolean;
}

const GameCard = ({ 
  game, 
  onLike, 
  onDislike,
  isLoading = false,
  isNewRelease,
  formatPrice,
  splitString,
  index = 0,
  zenMode = false
}: GameCardProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [verifiedDescription, setVerifiedDescription] = useState<string | null>(null);
  const [descriptionSource, setDescriptionSource] = useState<string | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [detailedGame, setDetailedGame] = useState<DetailedGame | null>(null);
  const [fetchFailed, setFetchFailed] = useState(false);
  const [fetchAttempted, setFetchAttempted] = useState(false);
  
  const fallbackImageUrl = "/grid-pattern.svg";
  const imageUrl = imageError ? fallbackImageUrl : game.imageUrl;

  // Programmatic verification system to identify which field contains the description
  useEffect(() => {
    // Reset states whenever the game changes
    setFetchAttempted(false);
    setFetchFailed(false);
    setVerifiedDescription(null);
    setDescriptionSource(null);
    
    // More detailed debug info about the game's descriptions
    console.log('----------- GAME DESCRIPTION DEBUG -----------');
    console.log('Game:', game.name, '| ID:', game.id);
    console.log('SHORT DESCRIPTION:', game.short_description);
    console.log('DETAILED DESCRIPTION:', game.detailed_description);
    console.log('RAW DESCRIPTION:', game.raw_description);

    // ALWAYS prioritize short_description 
    if (game.short_description) {
      console.log('Using short_description directly from Qdrant');
      setVerifiedDescription(game.short_description);
      setDescriptionSource('short_description from Qdrant');
      return;
    }
    
    // Second choice: detailed_description if short is missing
    if (game.detailed_description) {
      console.log('Using detailed_description as fallback');
      let trimmedDetail = game.detailed_description;
      if (trimmedDetail.length > 300) {
        trimmedDetail = trimmedDetail.substring(0, 300) + '...';
      }
      setVerifiedDescription(trimmedDetail);
      setDescriptionSource('detailed_description (trimmed)');
      return;
    }
    
    // Third choice: raw_description as last resort
    if (game.raw_description) {
      console.log('Using raw_description as fallback');
      setVerifiedDescription(game.raw_description);
      setDescriptionSource('raw_description');
      return;
    }
    
    // If we reach here, we couldn't find any description - we'll try to fetch one
    console.log('No description found - will need to fetch');
  }, [game.id]);

  // Simplify the fetchGameDetails function to prioritize short_description
  const fetchGameDetails = useCallback(async (gameId: string) => {
    // Don't try to fetch again if we already attempted or if we already have a description
    if (fetchAttempted || verifiedDescription) {
      console.log('Skipping fetch - already attempted or have description');
      setIsLoadingDetails(false);
      return;
    }
    
    try {
      setIsLoadingDetails(true);
      setFetchAttempted(true);
      console.log(`Fetching detailed info for game ${gameId}`);
      
      // Create an AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        console.log("Fetch timed out - aborting");
        setIsLoadingDetails(false);
        setFetchFailed(true);
      }, 3000);
      
      // Add a small delay to avoid too many requests
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // If the component is no longer mounted or user moved away, don't continue
      if (!isHovered) {
        console.log("User no longer hovering - canceling fetch");
        clearTimeout(timeoutId);
        setIsLoadingDetails(false);
        return;
      }
      
      // Send the request to the API
      const response = await fetch(`/api/py/game/${gameId}`, {
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache' 
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Error fetching game details: ${response.status}`);
      }
      
      const detailedData = await response.json();
      console.log(`Got detailed data for game ${gameId}:`, detailedData);
      
      // Log all description fields to help diagnose issues
      console.log('API Response - short_description:', detailedData.short_description);
      console.log('API Response - detailed_description:', detailedData.detailed_description);
      console.log('API Response - document/raw_description:', detailedData.document);
      
      setDetailedGame(detailedData);
      
      // ALWAYS prioritize short_description, even if it might look generic
      if (detailedData.short_description) {
        console.log('Using short_description from API response');
        setVerifiedDescription(detailedData.short_description);
        setDescriptionSource('API short_description');
      } 
      else if (detailedData.detailed_description) {
        console.log('Using detailed_description from API response');
        let trimmedDetail = detailedData.detailed_description;
        if (trimmedDetail.length > 300) {
          trimmedDetail = trimmedDetail.substring(0, 300) + '...';
        }
        setVerifiedDescription(trimmedDetail);
        setDescriptionSource('API detailed_description (trimmed)');
      }
      else if (detailedData.document) {
        console.log('Using document (raw_description) from API response');
        setVerifiedDescription(detailedData.document);
        setDescriptionSource('API document field');
      }
      else {
        // Create a minimal description as last resort
        console.log('No descriptions in API response, using minimal fallback');
        const developers = detailedData.developers || game.developers || "unknown developer";
        const name = detailedData.name || game.name;
        setVerifiedDescription(`${name} by ${developers}.`);
        setDescriptionSource('minimal fallback (no descriptions in API)');
      }
      
      setIsLoadingDetails(false);
    } catch (error) {
      console.error("Error fetching game details:", error);
      setFetchFailed(true);
      setIsLoadingDetails(false);
      
      // Use whatever description we already have in the game object
      if (game.short_description) {
        setVerifiedDescription(game.short_description);
        setDescriptionSource('original short_description (fallback after API error)');
      } else if (game.detailed_description) {
        setVerifiedDescription(game.detailed_description);
        setDescriptionSource('original detailed_description (fallback after API error)');
      } else if (game.raw_description) {
        setVerifiedDescription(game.raw_description);
        setDescriptionSource('original raw_description (fallback after API error)');
      } else {
        // Create a minimal description as last resort
        const developers = game.developers || "unknown developer";
        setVerifiedDescription(`${game.name} by ${developers}.`);
        setDescriptionSource('minimal fallback (after API error)');
      }
    }
  }, [game.id]);

  // New effect that handles fetching only when user hovers
  useEffect(() => {
    if (isHovered) {
      // Don't fetch if we already have a description
      const hasDescription = 
        (verifiedDescription && verifiedDescription.trim().length > 0);
        
      // Skip fetch 80% of the time to reduce API load
      const shouldSkipFetch = Math.random() < 0.8;
      
      if (!hasDescription && !shouldSkipFetch && !fetchAttempted) {
        // Delay the fetch slightly to avoid immediate API call on hover
        const timer = setTimeout(() => {
          // Only fetch if user is still hovering after delay
          if (isHovered && !fetchAttempted) {
            fetchGameDetails(game.id);
          }
        }, 300);
        
        return () => clearTimeout(timer);
      }
    }
  }, [isHovered, game.id, fetchAttempted, verifiedDescription]);

  // This useEffect will handle specifically resetting the loading state when a user hovers or the game changes
  useEffect(() => {
    // If we have isLoadingDetails stuck in true state, make sure to reset it
    if (isLoadingDetails && verifiedDescription) {
      console.log('Fixing stuck loading state');
      setIsLoadingDetails(false);
    }
    
    // Also reset loading state when hovering onto a new card
    if (isHovered) {
      const timer = setTimeout(() => {
        // If still loading after 2 seconds when hovered, force reset the loading state
        if (isLoadingDetails) {
          console.log('Force resetting stuck loading state on hover');
          setIsLoadingDetails(false);
          if (!verifiedDescription) {
            // Use a fallback if we don't have any description
            if (game.short_description) {
              setVerifiedDescription(game.short_description);
              setDescriptionSource('short_description (timeout fallback)');
            } else if (game.detailed_description) {
              setVerifiedDescription(game.detailed_description);
              setDescriptionSource('detailed_description (timeout fallback)');
            } else if (game.raw_description) {
              setVerifiedDescription(game.raw_description);
              setDescriptionSource('raw_description (timeout fallback)');
            } else {
              setVerifiedDescription(`${game.name} by ${game.developers || 'unknown developer'}.`);
              setDescriptionSource('minimal fallback (timeout)');
            }
          }
        }
      }, 2000);
      
      return () => clearTimeout(timer);
    }
  }, [isHovered, isLoadingDetails, verifiedDescription, game.id]);

  const handleImageError = () => {
    console.error(`Image load error for game: ${game.name}, URL: ${game.imageUrl}`);
    console.log(`Game object with error:`, game);
    setImageError(true);
  };

  // Determine platforms from the platforms field directly
  const hasPlatform = (platform: string) => {
    if (!game.platforms) return false;
    return game.platforms.toLowerCase().includes(platform.toLowerCase());
  };

  // Enhanced platform detection
  const platforms = {
    windows: !game.platforms || game.platforms.includes('windows'),
    mac: hasPlatform('mac') || hasPlatform('osx'),
    linux: hasPlatform('linux'),
    vr: game.tags ? game.tags.toLowerCase().includes('vr') || 
                   game.tags.toLowerCase().includes('virtual reality') : false
  };

  // Format the price to just show the number without decimals
  const displayPrice = game.price === 0 ? "Free" : `$${game.price.toFixed(2)}`;
  
  // Get genres for display - up to 3 tags
  const genreTags = splitString(game.genres).slice(0, 3) || [];
  
  // Simplified genre style matching the screenshot
  const getGenreStyle = (genre: string) => {
    const genreLower = genre.toLowerCase();
    if (genreLower.includes('action')) return 'bg-red-500';
    if (genreLower.includes('adventure')) return 'bg-blue-600';
    if (genreLower.includes('strategy')) return 'bg-yellow-500';
    if (genreLower.includes('rpg')) return 'bg-purple-600'; 
    if (genreLower.includes('simulation')) return 'bg-blue-500';
    if (genreLower.includes('casual')) return 'bg-gray-500';
    if (genreLower.includes('indie')) return 'bg-gray-600';
    return 'bg-gray-600'; // default
  };

  // Get release year from date string
  const getReleaseYear = () => {
    try {
      return new Date(game.release_date).getFullYear().toString();
    } catch (e) {
      return '';
    }
  };

  // Modified hover style that doesn't affect card dimensions
  const getHoverStyle = () => {
    return {
      zIndex: isHovered ? 10 : 1,
      boxShadow: isHovered ? 'rgba(0,0,0,0.2) 0 4px 8px' : 'rgba(0,0,0,0.05) 0 1px 3px',
      border: isHovered ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(255,255,255,0.05)',
    };
  };

  return (
    <Link 
      href={`/game/${game.id}`}
      className="block w-full h-full" 
      style={{ 
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div 
        className="relative w-full transition-all duration-200 rounded-md overflow-hidden bg-gray-900 flex flex-col"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          cursor: 'pointer',
          ...getHoverStyle()
        }}
      >
        {/* Clean image container - with like/dislike buttons at top */}
        <div className="relative w-full h-[160px]">
          <Image
            src={imageUrl}
            alt={game.name}
            fill
            className="object-cover w-full h-full"
            style={{
              transition: 'filter 0.3s ease-in-out',
              filter: isHovered ? 'brightness(0.85)' : 'brightness(1)',
            }}
            onError={handleImageError}
          />
          
          {/* Removed like/dislike buttons from here - moved to bottom of card */}
        </div>
        
        {/* Content section below the image */}
        <div className="p-3 bg-gray-800 flex-grow flex flex-col">
          {/* Title with improved readability */}
          <h3 className="text-white text-sm font-semibold line-clamp-1 mb-1.5 tracking-wide">{game.name}</h3>
          
          {/* Description preview - two lines with improved line height */}
          {verifiedDescription && (
            <p className="text-gray-300 text-xs line-clamp-2 mb-3 leading-relaxed">
              {verifiedDescription}
            </p>
          )}
          
          {/* Info rows with consistent spacing */}
          <div className="flex flex-col space-y-2 mt-auto">
            {/* Developer row with improved spacing */}
            <div className="flex items-center text-xs text-gray-300 mb-1.5">
              <span className="truncate font-medium">{game.developers}</span>
            </div>
            
            {/* Bottom section with price, genre tags, and metadata */}
            <div className="flex flex-col space-y-2">
              {/* Year/platform and price row with like/dislike buttons */}
              <div className="flex justify-between items-center">
                {/* Left section: Price, year badge, platform icons, and genre tags */}
                <div className="flex flex-wrap items-center gap-2">
                  {/* Price tag - moved to the left */}
                  <span className="bg-blue-600 text-white px-2.5 py-1 rounded text-xs font-medium">
                    {displayPrice}
                  </span>
                  
                  {/* Year badge */}
                  <span className="text-xs text-gray-300 bg-gray-700 px-1.5 py-0.5 rounded">
                    {getReleaseYear()}
                  </span>
                  
                  {/* Platform icons - show all supported platforms */}
                  <div className="flex space-x-1">
                    {platforms.windows && (
                      <Image 
                        src="/windows-icon.svg" 
                        alt="Windows" 
                        width={16} 
                        height={16}
                        className="opacity-80"
                      />
                    )}
                    {platforms.mac && (
                      <Image 
                        src="/apple-icon.svg" 
                        alt="Mac" 
                        width={14} 
                        height={14}
                        className="opacity-80"
                      />
                    )}
                    {platforms.linux && (
                      <Image 
                        src="/linux-icon.svg" 
                        alt="Linux" 
                        width={14} 
                        height={14}
                        className="opacity-80"
                      />
                    )}
                    {platforms.vr && (
                      <Image 
                        src="/vr-icon.svg" 
                        alt="VR" 
                        width={16} 
                        height={16}
                        className="opacity-80"
                      />
                    )}
                  </div>
                  
                  {/* Genre tags with improved spacing and contrast */}
                  {genreTags.slice(0, 2).map((genre, index) => (
                    <span 
                      key={index} 
                      className={`text-[10px] px-2 py-0.5 ${getGenreStyle(genre)} text-white font-medium rounded-sm shadow-sm`}
                    >
                      {genre}
                    </span>
                  ))}
                </div>
                
                {/* Like/Dislike buttons - positioned at the bottom right */}
                <div className="flex items-center space-x-2 z-30">
                  {/* Like button - circular */}
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onLike(game);
                    }}
                    disabled={isLoading}
                    className="w-8 h-8 rounded-full bg-green-500 hover:bg-green-400 flex items-center justify-center transition-colors shadow-md"
                    title="Like"
                  >
                    {isLoading ? (
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                      </svg>
                    )}
                  </button>
                  
                  {/* Dislike button - circular */}
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onDislike(game);
                    }}
                    disabled={isLoading}
                    className="w-8 h-8 rounded-full bg-red-500 hover:bg-red-400 flex items-center justify-center transition-colors shadow-md"
                    title="Dislike"
                  >
                    {isLoading ? (
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor" style={{ transform: 'rotate(180deg)' }}>
                        <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Hover overlay with gradient for better text contrast */}
        {isHovered && (
          <div className="absolute top-0 left-0 w-full h-[160px] pointer-events-none">
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/40 transition-opacity duration-300"></div>
          </div>
        )}
      </div>
    </Link>
  );
};

export default GameCard; 