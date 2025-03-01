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

# Start the backend in the background
echo "Starting backend server on port 8000..."
cd .. && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Return to frontend directory
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