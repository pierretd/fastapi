'use client';

import { useState, useEffect } from 'react';
import DiscoveryGrid from '../components/DiscoveryGrid';
import Image from 'next/image';
import Link from 'next/link';

export default function DiscoveryPage() {
  const [initialGames, setInitialGames] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch initial games on mount
  useEffect(() => {
    const fetchInitialGames = async () => {
      try {
        const response = await fetch('/api/py/random-games?limit=9');
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        const data = await response.json();
        setInitialGames(data);
      } catch (error) {
        console.error('Failed to fetch initial games:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchInitialGames();
  }, []);
  
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 sm:p-6 md:p-12">
      {/* Navigation Bar */}
      <nav className="w-full max-w-7xl flex items-center justify-between mb-8">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/logo.png"
            alt="Steam Explorer Logo"
            width={40}
            height={40}
            className="rounded-full"
          />
          <span className="text-xl font-bold hidden sm:inline">Steam Explorer</span>
        </Link>
        
        <div className="flex gap-4">
          <Link
            href="/"
            className="px-3 py-2 text-sm rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            Home
          </Link>
          <Link
            href="/search"
            className="px-3 py-2 text-sm rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            Search
          </Link>
          <Link
            href="/discovery"
            className="px-3 py-2 text-sm rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-colors"
          >
            Discovery
          </Link>
        </div>
      </nav>
      
      {/* Discovery Grid */}
      <DiscoveryGrid initialGames={initialGames} loading={isLoading} />
      
      {/* Footer */}
      <footer className="w-full max-w-7xl mt-12 border-t border-gray-200 dark:border-gray-800 pt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>
          Powered by semantic search using Qdrant vector database and FastEmbed.
        </p>
        <p className="mt-2">
          Discover new games based on your preferences. Like games you enjoy, dislike ones you don't.
        </p>
      </footer>
    </main>
  );
} 