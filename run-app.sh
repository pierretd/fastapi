#!/bin/bash

# Simple script to run both the backend and frontend

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to cleanup processes on exit
cleanup() {
  echo "Cleaning up processes..."
  
  if [ -f "server_pid.txt" ]; then
    SERVER_PID=$(cat server_pid.txt)
    if [ ! -z "$SERVER_PID" ]; then
      echo "Stopping backend server (PID: $SERVER_PID)..."
      kill -9 $SERVER_PID 2>/dev/null
      rm server_pid.txt
    fi
  fi
  
  if [ -f "frontend/frontend_pid.txt" ]; then
    FRONTEND_PID=$(cat frontend/frontend_pid.txt)
    if [ ! -z "$FRONTEND_PID" ]; then
      echo "Stopping frontend server (PID: $FRONTEND_PID)..."
      kill -9 $FRONTEND_PID 2>/dev/null
      rm frontend/frontend_pid.txt
    fi
  fi
  
  echo "Cleanup complete"
  exit 0
}

# Set up trap for cleanup on script exit
trap cleanup EXIT INT TERM

# Check if Python is installed
if ! command_exists python3 && ! command_exists python; then
  echo "Error: Python is not installed. Please install Python 3.8 or higher."
  exit 1
fi

# Check if Node.js is installed
if ! command_exists node; then
  echo "Error: Node.js is not installed. Please install Node.js 14 or higher."
  exit 1
fi

# Check if npm is installed
if ! command_exists npm; then
  echo "Error: npm is not installed. Please install npm."
  exit 1
fi

# Start backend server
echo "Starting backend server..."
if command_exists python3; then
  python3 main.py > server_stdout.log 2>&1 &
else
  python main.py > server_stdout.log 2>&1 &
fi
echo $! > server_pid.txt
echo "Backend server started with PID: $(cat server_pid.txt)"

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 5

# Start frontend server
echo "Starting frontend server..."
cd frontend
npm run dev > frontend_stdout.log 2>&1 &
echo $! > frontend_pid.txt
echo "Frontend server started with PID: $(cat frontend_pid.txt)"
cd ..

echo "Application is running!"
echo "- Backend: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the application"

# Keep the script running
while true; do
  sleep 1
done 