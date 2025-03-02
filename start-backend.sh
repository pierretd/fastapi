#!/bin/bash

# Go to the parent directory where the backend is located
cd ..

echo "Starting FastAPI backend..."

# Run the API with CORS enabled for frontend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 