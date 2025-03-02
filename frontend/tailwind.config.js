/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      fontFamily: {
        'montserrat': ['Montserrat', 'sans-serif'],
        'inter': ['Inter', 'sans-serif'],
      },
      colors: {
        'steam-blue': '#1A9FFF',
        'steam-teal': '#00D1FF',
        'steam-black': '#1B1C21',
        'steam-card': '#222530',
        'steam-nav': '#171A21',
        'steam-button': '#2A475E',
        'steam-button-hover': '#366E96',
        'like-green': '#33CC66',
        'dislike-red': '#FF5C5C',
        'color-bg-1': 'var(--color-bg-1)',
        'color-bg-2': 'var(--color-bg-2)',
        'color-1': 'var(--color-1)',
        'color-2': 'var(--color-2)',
        'color-3': 'var(--color-3)',
        'color-4': 'var(--color-4)',
        'color-5': 'var(--color-5)',
        'color-6': 'var(--color-6)',
        'color-7': 'var(--color-7)',
        'color-8': 'var(--color-8)',
        'color-9': 'var(--color-9)',
        'color-10': 'var(--color-10)',
      },
    },
  },
  plugins: [],
}
