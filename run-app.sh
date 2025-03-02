#!/bin/bash

# Create and activate Python environment for backend
cd ..
echo "Setting up backend environment..."
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt
pip install python-dotenv

# Start the backend in the background
echo "Starting backend server on port 8000..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Change to frontend directory
echo "Setting up frontend environment..."
cd frontend

# Start the frontend on port 3000
echo "Starting Next.js on port 3000..."
PORT=3000 npm run next-dev

# Cleanup function to kill backend when script terminates
cleanup() {
  echo "Stopping backend process..."
  kill $BACKEND_PID
  exit 0
}

# Set up trap to catch script termination
trap cleanup SIGINT SIGTERM

# Wait for the frontend process
wait 