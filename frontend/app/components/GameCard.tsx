import { useState, useEffect } from 'react';
import Image from 'next/image';

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
  const fetchGameDetails = async (gameId: string) => {
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
  };

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

  // Format the price to just show the number
  const displayPrice = game.price === 0 ? "Free" : `$${game.price}`;
  
  // Get up to three genres for display
  const genreTags = splitString(game.genres).slice(0, 3) || [];
  
  // Define price color based on price value
  const getPriceColor = (price: number) => {
    if (price === 0) return "bg-emerald-500/90"; // Free games get a green highlight
    if (price < 5) return "bg-blue-500/90";      // Budget games (<$5)
    if (price < 15) return "bg-indigo-500/90";   // Mid-range games
    return "bg-purple-500/90";                   // Premium games
  };

  return (
    <div
      className={`overflow-hidden bg-black border-0 outline-none focus:outline-none focus:ring-0 hover:outline-none transform transition-all duration-300 ${isHovered ? 'scale-[1.03] hover-glow' : 'hover:scale-[1.02]'} group rounded-sm ${zenMode ? 'zen-mode-transition' : ''} border-glow`}
      style={{ 
        outline: 'none',
        margin: 0,
        padding: 0,
        position: 'relative',
        zIndex: isHovered ? 50 : 1
      }}
      onMouseEnter={() => {
        console.log("Hovering on game:", game.name);
        console.log("Short description:", game.short_description);
        console.log("Detailed description:", game.detailed_description);
        console.log("Raw description:", game.raw_description);
        console.log("Full game object:", game);
        setIsHovered(true);
      }}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative h-full">
        {/* Game image */}
        <div className="relative w-full h-full">
          <Image
            src={imageUrl}
            alt={game.name}
            layout="fill"
            objectFit="cover"
            className={`transition-all duration-300 ${isHovered ? 'brightness-90' : `group-hover:brightness-105 thumbnail-hover ${zenMode ? 'zen-mode-image' : ''}`} group-hover:shadow-lg`}
            onError={handleImageError}
          />
          
          {/* Add subtle border highlight effect on hover */}
          <div className={`absolute inset-0 border-0 border-white/0 group-hover:border-2 group-hover:border-white/20 transition-all duration-300 pointer-events-none rounded-sm ${zenMode && !isHovered ? 'opacity-0' : ''}`}></div>
          
          {/* Always visible genre badges (top-left) - Up to 3 genres */}
          {(!zenMode || isHovered) && genreTags.length > 0 && (
            <div className={`absolute top-1 left-1 z-20 flex flex-col gap-1 ${zenMode && isHovered ? 'zen-hover-reveal' : ''}`}>
              {genreTags.map((genre, index) => (
                <span 
                  key={index} 
                  className="text-[9px] px-1.5 py-0.5 bg-black/70 text-white rounded-md shadow-md border border-white/10 backdrop-blur-sm max-w-[110px] truncate drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)] outline outline-1 outline-white/10"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}
          
          {/* Always visible platform indicators (bottom-left) */}
          {(!zenMode || isHovered) && (
            <div className={`absolute bottom-1 left-1 flex gap-0.5 z-20 ${zenMode && isHovered ? 'zen-hover-reveal' : ''}`}>
              {platforms.windows && (
                <div className="bg-black/70 p-0.5 rounded-full border border-white/10 shadow-sm" title="Windows">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.9-1.801"/>
                  </svg>
                </div>
              )}
              {platforms.mac && (
                <div className="bg-black/70 p-0.5 rounded-full border border-white/10 shadow-sm" title="Mac">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                  </svg>
                </div>
              )}
              {platforms.linux && (
                <div className="bg-black/70 p-0.5 rounded-full border border-white/10 shadow-sm" title="Linux">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.504 0c-.155 0-.315.008-.48.021-4.226.333-3.105 4.807-3.17 6.298-.076 1.092-.3 1.953-1.05 3.02-.885 1.051-2.127 2.75-2.716 4.521-.278.832-.41 1.684-.287 2.489a3.5 3.5 0 0 0 1.63 1.952c1.006.39 2.077.802 3.105 1.274 1.027.471 2.089.95 2.954 1.375.43.213.94.396 1.504.396s1.152-.189 1.594-.407c.89-.43 1.982-.927 3.027-1.408 1.043-.477 2.128-.897 3.135-1.289.994-.39 1.598-1.125 1.736-1.936.113-.727-.126-1.526-.372-2.303-.637-2.012-1.653-3.563-2.61-4.675-.642-.747-1.018-1.917-2.96-1.517-1.7-.341-5.301.383-6.602 1.251-.146.098-.27.197-.373.298-.103.101-.186.206-.245.309"/>
                  </svg>
                </div>
              )}
              {platforms.vr && (
                <div className="bg-black/70 p-0.5 rounded-full border border-white/10 shadow-sm" title="VR">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2m7 13.5c3.31 0 6-2.69 6-6s-2.69-6-6-6-6 2.69-6 6 2.69 6 6 6m0-11c2.76 0 5 2.24 5 5s-2.24 5-5 5-5-2.24-5-5 2.24-5 5-5z"/>
                  </svg>
                </div>
              )}
            </div>
          )}
          
          {/* Price indicator (bottom-right) - Enhanced with color and font weight */}
          {(!zenMode || isHovered) && (
            <div className={`absolute bottom-1 right-1 z-20 ${zenMode && isHovered ? 'zen-hover-reveal' : ''}`}>
              <span className={`text-[10px] px-2 py-0.5 ${getPriceColor(game.price)} text-white rounded-md shadow-lg border border-white/20 font-semibold backdrop-blur-sm drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] outline outline-1 outline-white/15`}>
                {game.price === 0 ? "Free" : `$${game.price}`}
              </span>
            </div>
          )}
        </div>
        
        {/* Overlay that appears on hover - Contains all game info and action buttons */}
        {isHovered && (
          <div 
            className={`absolute inset-0 backdrop-blur-md flex flex-col p-1.5 shadow-xl z-50 ${zenMode ? 'zen-hover-reveal' : 'card-hover-in'} overflow-hidden`}
            style={{ 
              pointerEvents: 'auto',
              display: 'flex',
              maxHeight: '100%',
              background: 'linear-gradient(to bottom, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.9) 100%)'
            }}
          >
            {/* Top section: Game title and platforms */}
            <div className="flex justify-between items-start mb-0.5">
              <h3 className="text-white font-bold text-xs leading-tight pr-2">{game.name}</h3>
              
              {/* Platform icons */}
              <div className="flex gap-0.5 ml-1 flex-shrink-0">
                {platforms.windows && (
                  <div className="bg-black/60 p-0.5 rounded-full border border-white/10 shadow-sm" title="Windows">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.9-1.801"/>
                    </svg>
                  </div>
                )}
                {platforms.mac && (
                  <div className="bg-black/60 p-0.5 rounded-full border border-white/10 shadow-sm" title="Mac">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                    </svg>
                  </div>
                )}
                {platforms.linux && (
                  <div className="bg-black/60 p-0.5 rounded-full border border-white/10 shadow-sm" title="Linux">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12.504 0c-.155 0-.315.008-.48.021-4.226.333-3.105 4.807-3.17 6.298-.076 1.092-.3 1.953-1.05 3.02-.885 1.051-2.127 2.75-2.716 4.521-.278.832-.41 1.684-.287 2.489a3.5 3.5 0 0 0 1.63 1.952c1.006.39 2.077.802 3.105 1.274 1.027.471 2.089.95 2.954 1.375.43.213.94.396 1.504.396s1.152-.189 1.594-.407c.89-.43 1.982-.927 3.027-1.408 1.043-.477 2.128-.897 3.135-1.289.994-.39 1.598-1.125 1.736-1.936.113-.727-.126-1.526-.372-2.303-.637-2.012-1.653-3.563-2.61-4.675-.642-.747-1.018-1.917-2.96-1.517-1.7-.341-5.301.383-6.602 1.251-.146.098-.27.197-.373.298-.103.101-.186.206-.245.309"/>
                    </svg>
                  </div>
                )}
                {platforms.vr && (
                  <div className="bg-black/60 p-0.5 rounded-full border border-white/10 shadow-sm" title="VR">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2m7 13.5c3.31 0 6-2.69 6-6s-2.69-6-6-6-6 2.69-6 6 2.69 6 6 6m0-11c2.76 0 5 2.24 5 5s-2.24 5-5 5-5-2.24-5-5 2.24-5 5-5z"/>
                    </svg>
                  </div>
                )}
              </div>
            </div>
            
            {/* Game description - Fixed height, no scrolling - With additional lines for more content */}
            <div className="bg-black/30 p-1 rounded-md mb-1 overflow-hidden" style={{ maxHeight: '10rem' }}>
              {isLoadingDetails && !verifiedDescription ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span className="ml-2 text-white/70 text-xs">Loading...</span>
                </div>
              ) : verifiedDescription ? (
                <>
                  <div className="mb-0.5">
                    <p className="text-white text-xs font-normal leading-relaxed line-clamp-2" style={{ lineHeight: '1.3' }}>
                      {verifiedDescription}
                    </p>
                  </div>
                </>
              ) : fetchFailed ? (
                <p className="text-white/70 text-xs italic">Could not load description. Server may be busy.</p>
              ) : (
                <p className="text-white/70 text-xs italic">No description available</p>
              )}
            </div>
            
            {/* Game details section - Simplified */}
            <div className="flex items-center justify-between bg-white/5 rounded-md p-1 text-white/70 text-[9px] mb-1.5">
              <span className="truncate">
                {/* Extract year from date string if possible */}
                {game.release_date ? game.release_date.match(/\d{4}/)?.at(0) ?? game.release_date : 'Unknown year'}
              </span>
              <span className="mx-1">•</span>
              <span className="truncate max-w-[70%] text-right">{game.developers || 'Unknown developer'}</span>
            </div>
            
            {/* Price and genres section - Moved from top to bottom - Enhanced price display */}
            <div className="flex justify-between mb-2 items-center mt-auto">
              <span className={`text-white text-xs font-semibold ${getPriceColor(game.price)} px-2 py-0.5 rounded shadow-md border border-white/10 drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]`}>
                {game.price === 0 ? "Free" : `$${game.price}`}
              </span>
              
              {/* Tags - more refined badges */}
              <div className="flex flex-wrap gap-1 justify-end">
                {genreTags.map((genre, index) => (
                  <span key={index} className="text-[9px] px-1.5 py-0.5 bg-white/10 text-white rounded-md tracking-wide shadow-md max-w-[90px] truncate border border-white/10 outline outline-1 outline-white/5">
                    {genre}
                  </span>
                ))}
              </div>
            </div>
            
            {/* Action buttons */}
            <div className="flex justify-center gap-3 relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onLike(game);
                }}
                disabled={isLoading}
                className="flex items-center justify-center p-2 rounded-full bg-green-500 text-white hover:bg-green-400 active:scale-90 transition-all duration-200 shadow-md focus:outline-none focus:ring-2 focus:ring-white/50 hover:shadow-green-500/40 hover:scale-110 like-button-hover"
                style={{
                  transform: 'scale(1)',
                  transition: 'transform 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease'
                }}
                title="Like"
              >
                {isLoading ? (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                  </svg>
                )}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDislike(game);
                }}
                disabled={isLoading}
                className="flex items-center justify-center p-2 rounded-full bg-red-500 text-white hover:bg-red-400 active:scale-90 transition-all duration-200 shadow-md focus:outline-none focus:ring-2 focus:ring-white/50 hover:shadow-red-500/40 hover:scale-110 dislike-button-hover"
                style={{
                  transform: 'scale(1)',
                  transition: 'transform 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease'
                }}
                title="Dislike"
              >
                {isLoading ? (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" style={{ transform: 'rotate(180deg)' }}>
                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GameCard; 