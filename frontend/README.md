# Steam Games Search App

A modern web application for searching and discovering Steam games using a vector search API.

## Features

- Search Steam games with semantic search capabilities
- View random game recommendations
- Browse detailed game information 
- Responsive design for all devices

## Technology Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python
- **Database**: Vector search powered by Qdrant

## Getting Started

### Development

1. Clone the repository
2. Install dependencies:
   ```
   npm install
   ```
3. Run the development server:
   ```
   npm run dev:frontend-only
   ```
   
4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Deployment

This application is configured for easy deployment to Vercel.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fyourusername%2Fsteam-games-search)

## Environment Variables

- `BACKEND_URL`: URL of the FastAPI backend (defaults to local development URL if not set)

## License

MIT
