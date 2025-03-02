import { useState } from 'react';
import Image from 'next/image';

interface Game {
  id: string;
  name: string;
  price: number;
  short_description: string;
  release_date: string;
  developers: string;
  genres: string;
  tags: string;
  platforms: string;
  relevance?: number;
  imageUrl: string;
}

interface HistoryPanelProps {
  likedGames: Game[];
  dislikedGames: Game[];
  onRemoveFromLiked: (game: Game) => void;
  onRemoveFromDisliked: (game: Game) => void;
  onResetHistory: () => void;
  onRefreshGames: () => void;
  refreshing: boolean;
  isExpanded: boolean;
  onToggleExpanded: () => void;
  horizontalLayout?: boolean;
}

const HistoryPanel = ({
  likedGames,
  dislikedGames,
  onRemoveFromLiked,
  onRemoveFromDisliked,
  onResetHistory,
  onRefreshGames,
  refreshing,
  isExpanded,
  onToggleExpanded,
  horizontalLayout = false
}: HistoryPanelProps) => {
  const [likedExpanded, setLikedExpanded] = useState(true);
  const [dislikedExpanded, setDislikedExpanded] = useState(true);
  const [hoveredGame, setHoveredGame] = useState<string | null>(null);
  
  return (
    <div 
      className={`${horizontalLayout ? 'h-full' : 'h-full'} relative history-panel-content`} 
    >
      {/* Header with collapse button */}
      <div className={`flex items-center justify-between ${horizontalLayout ? 'p-2' : 'p-4'} border-b border-white/10`}>
        <h2 className={`font-bold text-white flex items-center gap-2 ${horizontalLayout ? 'text-sm' : 'text-base'}`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-purple-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
          </svg>
          Game History
        </h2>
        <div className="flex gap-2">
          {/* Collapse/Expand button */}
          <button
            onClick={onToggleExpanded}
            className="text-xs py-1 px-2 rounded-md bg-white/5 hover:bg-white/10 text-white/70 hover:text-white/90 transition-colors flex items-center gap-1"
            title="Hide history panel"
            aria-label="Hide history panel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="hidden sm:inline text-[10px]">Hide</span>
          </button>
        </div>
      </div>
      
      {/* Action Buttons - Always visible as long as the panel itself is visible */}
      <div className={`flex gap-2 ${horizontalLayout ? 'p-2' : 'p-4'}`}>
        <button
          onClick={onRefreshGames}
          className={`flex items-center justify-center gap-1 px-2 py-1 rounded-full bg-gradient-to-r from-[#3CCBA0] to-[#4CAF50] text-white text-xs font-medium hover:shadow-lg hover:shadow-[#4CAF50]/20 transition-all duration-200 flex-1 ${
            refreshing ? 'opacity-50 cursor-wait' : ''
          }`}
          disabled={refreshing}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={`h-3 w-3 ${refreshing ? 'animate-rotate' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {refreshing ? 'Refreshing...' : 'Refresh Games'}
        </button>
        
        {(likedGames.length > 0 || dislikedGames.length > 0) && (
          <button
            onClick={onResetHistory}
            className="flex items-center justify-center gap-1 px-2 py-1 rounded-full bg-white/10 hover:bg-white/15 text-white text-xs border border-white/10 transition-all duration-200 flex-1"
            title="Clear all liked and disliked games"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Reset History
          </button>
        )}
      </div>
    
      {/* History Panel - Now positioned between hero and game grid */}
      <div className={`overflow-hidden px-4 pb-4 gap-4 ${horizontalLayout ? 'flex-row flex' : 'flex-grow flex flex-col'}`}>
        {/* Empty state */}
        {likedGames.length === 0 && dislikedGames.length === 0 && (
          <div className="py-6 px-4 rounded-lg bg-black/50 border border-white/10 my-2">
            <div className="flex flex-col items-center text-center">
              {/* Game controller icon */}
              <div className="w-16 h-16 mb-4 flex items-center justify-center rounded-full bg-indigo-500/20">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" className="w-8 h-8 text-indigo-400">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 01-.657.643 48.39 48.39 0 01-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 01-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 00-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 01-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 00.657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 005.427-.63 48.05 48.05 0 00.582-4.717.532.532 0 00-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.96.401v0a.656.656 0 00.658-.663 48.422 48.422 0 00-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 01-.61-.58v0z" />
                </svg>
              </div>
              
              <h3 className="text-lg font-medium text-white mb-2">No Rated Games Yet</h3>
              
              <p className="text-sm text-white/70 mb-4">
                Your liked and disliked games will appear here once you start rating.
              </p>
              
              <div className="flex justify-center gap-8 mb-4">
                <div className="flex flex-col items-center">
                  <div className="bg-green-500/20 p-2 rounded-full mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                    </svg>
                  </div>
                  <span className="text-xs text-green-400">Like</span>
                </div>
                
                <div className="flex flex-col items-center">
                  <div className="bg-red-500/20 p-2 rounded-full mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor" style={{ transform: "rotate(180deg)" }}>
                      <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                    </svg>
                  </div>
                  <span className="text-xs text-red-400">Dislike</span>
                </div>
              </div>
              
              <button
                onClick={onRefreshGames}
                disabled={refreshing}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm py-2 px-4 rounded-full font-medium hover:shadow-lg transition-all duration-300"
              >
                {refreshing ? 'Loading...' : 'Find Games to Rate'}
              </button>
            </div>
          </div>
        )}
        
        {/* Liked Games Section */}
        {likedGames.length > 0 && (
          <div className={`bg-white/5 backdrop-blur-sm rounded-lg overflow-hidden animate-fadeIn ${horizontalLayout ? 'flex-1' : ''}`}>
            <div 
              className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/5 transition-colors"
              onClick={() => setLikedExpanded(!likedExpanded)}
            >
              <h3 className="font-semibold text-[#4CAF50] flex items-center gap-2 text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                </svg>
                Liked Games 
                <span className="ml-1 text-xs text-white/60">({likedGames.length})</span>
              </h3>
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 text-white/60 transition-transform duration-300 ${likedExpanded ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </div>
            
            {/* Collapsible content */}
            <div className={`transition-all duration-300 ease-in-out overflow-hidden ${
              likedExpanded ? 'max-h-[60px] opacity-100' : 'max-h-0 opacity-0'
            }`}>
              <div className="px-2 pb-2">
                <div className={`${horizontalLayout ? 'h-[40px] overflow-x-auto flex gap-2' : 'max-h-[240px] overflow-y-auto'} custom-scrollbar pr-1 ${!horizontalLayout && 'space-y-2'}`}>
                  {likedGames.map((game) => (
                    <div 
                      key={game.id} 
                      className={`group relative ${horizontalLayout ? 'flex-shrink-0 w-44' : ''} flex items-center rounded-lg bg-white/5 hover:bg-white/10 transition-all duration-200 backdrop-blur-sm border border-white/5 overflow-hidden`}
                      onMouseEnter={() => setHoveredGame(game.id)}
                      onMouseLeave={() => setHoveredGame(null)}
                    >
                      <div className="flex-shrink-0 w-8 h-8 relative">
                        <Image 
                          src={game.imageUrl} 
                          alt={game.name}
                          width={32}
                          height={32}
                          className="object-cover w-full h-full"
                        />
                      </div>
                      <div className="flex-1 min-w-0 px-2 py-1">
                        <h4 className="text-xs font-medium text-white truncate">{game.name}</h4>
                        <p className="text-[9px] text-white/60 truncate">{game.developers}</p>
                      </div>
                      <button
                        onClick={() => onRemoveFromLiked(game)}
                        className={`absolute right-1 top-1 text-white/40 hover:text-white/90 focus:text-white/90 focus:outline-none p-1 rounded-full hover:bg-white/10 transition-all ${
                          hoveredGame === game.id ? 'opacity-100' : 'opacity-0'
                        }`}
                        aria-label="Remove from liked games"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Disliked Games Section */}
        {dislikedGames.length > 0 && (
          <div className={`bg-white/5 backdrop-blur-sm rounded-lg overflow-hidden animate-fadeIn ${horizontalLayout ? 'flex-1' : ''}`}>
            <div 
              className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/5 transition-colors"
              onClick={() => setDislikedExpanded(!dislikedExpanded)}
            >
              <h3 className="font-semibold text-[#E57373] flex items-center gap-2 text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                </svg>
                Disliked Games
                <span className="ml-1 text-xs text-white/60">({dislikedGames.length})</span>
              </h3>
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 text-white/60 transition-transform duration-300 ${dislikedExpanded ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </div>
            
            {/* Collapsible content */}
            <div className={`transition-all duration-300 ease-in-out overflow-hidden ${
              dislikedExpanded ? 'max-h-[60px] opacity-100' : 'max-h-0 opacity-0'
            }`}>
              <div className="px-2 pb-2">
                <div className={`${horizontalLayout ? 'h-[40px] overflow-x-auto flex gap-2' : 'max-h-[240px] overflow-y-auto'} custom-scrollbar pr-1 ${!horizontalLayout && 'space-y-2'}`}>
                  {dislikedGames.map((game) => (
                    <div 
                      key={game.id} 
                      className={`group relative ${horizontalLayout ? 'flex-shrink-0 w-44' : ''} flex items-center rounded-lg bg-white/5 hover:bg-white/10 transition-all duration-200 backdrop-blur-sm border border-white/5 overflow-hidden`}
                      onMouseEnter={() => setHoveredGame(game.id)}
                      onMouseLeave={() => setHoveredGame(null)}
                    >
                      <div className="flex-shrink-0 w-8 h-8 relative">
                        <Image 
                          src={game.imageUrl} 
                          alt={game.name}
                          width={32}
                          height={32}
                          className="object-cover w-full h-full"
                        />
                      </div>
                      <div className="flex-1 min-w-0 px-2 py-1">
                        <h4 className="text-xs font-medium text-white truncate">{game.name}</h4>
                        <p className="text-[9px] text-white/60 truncate">{game.developers}</p>
                      </div>
                      <button
                        onClick={() => onRemoveFromDisliked(game)}
                        className={`absolute right-1 top-1 text-white/40 hover:text-white/90 focus:text-white/90 focus:outline-none p-1 rounded-full hover:bg-white/10 transition-all ${
                          hoveredGame === game.id ? 'opacity-100' : 'opacity-0'
                        }`}
                        aria-label="Remove from disliked games"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPanel; 