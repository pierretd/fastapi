# Steam Games Search - Deployment Guide

This guide explains how to deploy the Steam Games Search application, which consists of a Next.js frontend and a FastAPI backend.

## Project Overview

- **Backend**: Steam Games Search API (FastAPI)
  - Already deployed at: https://fastapi-5aw3.onrender.com/
  - Provides game search, recommendations, and other functionality

- **Frontend**: Next.js application
  - Located in the `frontend/` directory
  - Connected to the deployed API

## Setup Summary

We've configured the Next.js application to connect to the deployed FastAPI backend by:

1. Updating the `next.config.js` to rewrite API requests to the deployed API URL
2. Modifying the API proxy in `frontend/api/index.py` to use the production backend URL
3. Updating the frontend components to use the correct API methods (POST for search)
4. Adding configuration files for deployment platforms

## Deployment Options

### Option 1: Deploy to Vercel (Recommended)

Vercel is the platform built by the creators of Next.js and offers the simplest deployment process:

1. Push your code to a GitHub repository
2. Visit [Vercel](https://vercel.com) and sign up/login with your GitHub account
3. Click "New Project" and import your repository
4. Configure the project:
   - Framework Preset: Next.js
   - Root Directory: `frontend` (specify this if your frontend code is in a subdirectory)
   - Environment Variables: Set `BACKEND_URL` to `https://fastapi-5aw3.onrender.com`
5. Click "Deploy"

### Option 2: Deploy to Render

You can also deploy the application to Render using these steps:

1. Push your code to a GitHub repository
2. Visit [Render](https://render.com) and sign up/login
3. Click "New" and select "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - Name: `steam-games-frontend` (or your preferred name)
   - Root Directory: `frontend` (if your frontend code is in a subdirectory)
   - Environment: Node
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`
   - Environment Variables: Set `BACKEND_URL` to `https://fastapi-5aw3.onrender.com`
6. Click "Create Web Service"

### Option 3: Deploy to Netlify

Netlify also provides straightforward deployment for Next.js applications:

1. Push your code to a GitHub repository
2. Visit [Netlify](https://netlify.com) and sign up/login
3. Click "New site from Git" and select your repository
4. Configure the build settings:
   - Base directory: `frontend` (if your frontend code is in a subdirectory)
   - Build command: `npm run build`
   - Publish directory: `.next`
   - Environment Variables: Set `BACKEND_URL` to `https://fastapi-5aw3.onrender.com`
5. Click "Deploy site"

## Local Development

To run the frontend application locally connected to the production API:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the frontend-only development server
npm run dev:frontend-only
```

## Testing the API Connection

You can test the connection to the deployed API using the provided test script:

```bash
cd frontend
node test-api-connection.js
```

This script checks the health endpoint and makes a test search request to verify functionality.

## Configuration Files

The main configuration files for the deployment are:

- `frontend/next.config.js`: Configures API rewrites
- `frontend/vercel.json`: Contains Vercel deployment settings
- `frontend/api/index.py`: API proxy configuration for local development with FastAPI

## API Endpoints Used

The frontend communicates with the following API endpoints:

- `/search` - POST request to search for games
- `/recommend/{game_id}` - GET request for game recommendations 
- `/game/{game_id}` - GET request for detailed game information
- `/health` - GET request for health check
- `/random-games` - GET request for random games

## Troubleshooting

If you encounter any issues during deployment:

1. **API Connection Issues**: Check the browser's developer console for network errors. Make sure the API rewrites in `next.config.js` are correctly configured.

2. **Build Errors**: Ensure all dependencies are installed by running `npm install` before building.

3. **Environment Variables**: Verify that the `BACKEND_URL` environment variable is correctly set on your deployment platform.

4. **CORS Issues**: If you encounter CORS errors, ensure the API allows requests from your frontend domain. 