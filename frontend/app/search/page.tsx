'use client';

import { useState } from 'react';
import Link from 'next/link';

interface Game {
  id: number;
  name: string;
  price: number;
  short_description: string;
  release_date: string;
  developer: string;
  genres: string[];
  relevance?: number;
}

interface SearchResponse {
  items: Game[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Game[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/py/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          limit: 10
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
      
      const data: SearchResponse = await response.json();
      setResults(data.items || []); 
      setTotalResults(data.total || 0);
      setCurrentPage(data.page || 1);
      setTotalPages(data.pages || 0);
      setSearchPerformed(true);
    } catch (err) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : String(err));
      setResults([]);
      setTotalResults(0);
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    if (price === 0) return 'Free to Play';
    return `$${price.toFixed(2)}`;
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
          </div>
          
          {/* Search Form */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <h1 className="text-2xl font-bold mb-4">Search Steam Games</h1>
              <form onSubmit={handleSearch} className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter game title, genre, or description..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                  required
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </button>
              </form>
            </div>
          </div>
          
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">
              <p className="font-bold">Error</p>
              <p>{error}</p>
            </div>
          )}
          
          {/* Results */}
          {searchPerformed && !isLoading && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4">
                  {totalResults > 0 
                    ? `Found ${totalResults} games matching "${query}"`
                    : `No results found for "${query}"`}
                </h2>
                
                {results.length > 0 ? (
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {results.map((game) => (
                      <div key={game.id} className="py-4">
                        <Link 
                          href={`/game/${game.id}`}
                          className="block hover:bg-gray-50 dark:hover:bg-gray-700 -mx-6 px-6 py-2 transition-colors"
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <h3 className="text-lg font-medium text-gray-900 dark:text-white">{game.name}</h3>
                              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-3">{game.short_description}</p>
                              
                              <div className="mt-2 flex items-center gap-x-4">
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  <span className="font-medium text-gray-900 dark:text-white">{formatPrice(game.price)}</span>
                                </div>
                                
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  <span>{game.release_date}</span>
                                </div>
                                
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  <span>{game.developer}</span>
                                </div>
                              </div>
                              
                              <div className="mt-2 flex flex-wrap gap-1">
                                {game.genres.map((genre, idx) => (
                                  <span 
                                    key={idx}
                                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
                                  >
                                    {genre}
                                  </span>
                                ))}
                              </div>
                            </div>
                            
                            {game.relevance !== undefined && (
                              <div className="ml-4 flex-shrink-0">
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                                  {(game.relevance * 100).toFixed(0)}% match
                                </span>
                              </div>
                            )}
                          </div>
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">
                    Try adjusting your search terms or browse our catalog.
                  </p>
                )}
                
                {totalPages > 1 && (
                  <div className="mt-4 flex justify-center">
                    <div className="inline-flex rounded-md shadow-sm">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="px-3 py-2 text-sm rounded-l-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-3 py-2 text-sm border-t border-b border-gray-300 bg-gray-50">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                        className="px-3 py-2 text-sm rounded-r-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
} 