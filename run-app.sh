#!/bin/bash

# Simple script to run both the backend and frontend

# Function to kill processes on exit
cleanup() {
  echo "Stopping all processes..."
  if [ -f server_pid.txt ]; then
    kill $(cat server_pid.txt) 2>/dev/null
    rm server_pid.txt
  fi
  if [ -f frontend_pid.txt ]; then
    kill $(cat frontend_pid.txt) 2>/dev/null
    rm frontend_pid.txt
  fi
  exit 0
}

# Set up trap to catch signals
trap cleanup SIGINT SIGTERM

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start the backend server
echo "Starting backend server..."
python main.py > server_stdout.log 2>&1 &
echo $! > server_pid.txt
echo "Backend server started (PID: $(cat server_pid.txt))"

# Change to frontend directory
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# Start the frontend
echo "Starting frontend..."
npm run dev > ../frontend_stdout.log 2>&1 &
echo $! > ../frontend_pid.txt
echo "Frontend started (PID: $(cat ../frontend_pid.txt))"

echo "Application is running!"
echo "- Backend: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all services"

# Wait for user to press Ctrl+C
wait 