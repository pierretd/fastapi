# Deploying Game Discovery on Render

This guide explains how to deploy the Game Discovery application on Render.

## Prerequisites

1. A [Render account](https://render.com/)
2. A [Qdrant Cloud](https://qdrant.tech/) account or another vector database service
3. Your game data in CSV format

## Deployment Steps

### 1. Set Up Qdrant Collection

Ensure you have a Qdrant collection set up with your game data. You'll need:
- Qdrant service URL
- Qdrant API key
- Collection name

### 2. Fork or Clone the Repository

Make sure you have your own copy of this repository on GitHub or GitLab.

### 3. Deploy Using Render Blueprint

The easiest way to deploy is using the render.yaml blueprint:

1. Go to your Render dashboard
2. Click "New" → "Blueprint"
3. Connect your repository
4. Provide the required environment variables:
   - `QDRANT_URL`: Your Qdrant service URL
   - `QDRANT_API_KEY`: Your Qdrant API key
   - Other optional variables as needed

Render will automatically deploy both the backend API and frontend application as specified in the render.yaml file.

### 4. Manual Deployment

If you prefer to set up services manually:

#### Backend API

1. In Render, create a new Web Service
2. Connect your repository
3. Configure the service:
   - Name: `game-discovery-api`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
4. Add environment variables:
   - `QDRANT_URL`: Your Qdrant service URL
   - `QDRANT_API_KEY`: Your Qdrant API key
   - `COLLECTION_NAME`: Your collection name
   - `EMBEDDING_MODEL`: `BAAI/bge-small-en-v1.5`
   - `VECTOR_SIZE`: `384`
   - `RENDER`: `true`

#### Frontend

1. In Render, create another Web Service
2. Connect to the same repository
3. Configure the service:
   - Name: `game-discovery-frontend`
   - Environment: `Node`
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm start`
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: URL of your backend API service
   - `NODE_ENV`: `production`

### 5. Initializing the Collection

If you need to upload data to your Qdrant collection:

1. SSH into your backend service on Render
2. Run the upload script: `python upload_data.py --csv your_data.csv`

## Troubleshooting

- **Backend can't connect to Qdrant**: Verify your Qdrant URL and API key
- **Frontend can't reach backend**: Check the NEXT_PUBLIC_API_URL environment variable
- **Slow initial response**: The first request may be slow as the embeddings model loads

## Monitoring

Monitor your application using Render's built-in logs and metrics dashboard.

## Updating

To update your application:
1. Push changes to your repository
2. Render will automatically detect changes and redeploy 