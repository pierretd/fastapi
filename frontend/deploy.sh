#!/bin/bash

# Steam Games Search Frontend Deployment Script

echo "🚀 Starting deployment process for Steam Games Search frontend..."

# Build the application
echo "📦 Building the Next.js application..."
npm run build

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null
then
    echo "🔧 Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete! Check the URL above to access your application." 