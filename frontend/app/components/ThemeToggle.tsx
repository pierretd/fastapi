'use client';

import { useEffect, useState } from 'react';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';

export default function ThemeToggle() {
  const [theme, setTheme] = useState('light');
  
  useEffect(() => {
    // Check for saved theme or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.classList.toggle('dark', savedTheme === 'dark');
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
      document.documentElement.classList.add('dark');
    }
  }, []);
  
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
    localStorage.setItem('theme', newTheme);
  };
  
  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-full bg-color-2 hover:bg-color-3 border border-color-4 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-color-5"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <MoonIcon className="w-5 h-5 text-color-9" />
      ) : (
        <SunIcon className="w-5 h-5 text-color-9" />
      )}
    </button>
  );
} 