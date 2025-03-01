#!/bin/bash
# Script to set up and run the Steam Games Search API

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the API
echo "Starting the API server..."
python -m uvicorn main:app --reload

# This line won't be reached while the server is running
# When server is stopped, deactivate the virtual environment
deactivate 