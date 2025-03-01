#!/bin/bash

# Install Python dependencies if venv exists or create it if it doesn't
if [ -d "venv" ]; then
  echo "Virtual environment exists, activating..."
  source venv/bin/activate
else
  echo "Creating virtual environment..."
  python3 -m venv venv
  source venv/bin/activate
fi

# Install Python dependencies from requirements.txt
pip install -r requirements.txt

# Set environment variable for the backend URL
export BACKEND_URL="http://localhost:8000"

# Start the development server
echo "Starting Next.js development server..."
npm run dev 