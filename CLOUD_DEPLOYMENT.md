# Cloud Deployment Guide

This guide will help you deploy the Steam Games Search API entirely in the cloud, with no local setup required.

## Overview

We'll use:
- **Render**: To host the FastAPI application
- **Qdrant Cloud**: To host the vector database for search

## Step 1: Set Up Qdrant Cloud

1. Go to [Qdrant Cloud](https://cloud.qdrant.io/) and create an account if you don't already have one.

2. Create a new cluster:
   - Choose your preferred region
   - Select a plan that suits your needs (start with the free tier for testing)
   - Set a name for your cluster

3. Once the cluster is created, note down:
   - The cluster URL (looks like: `https://[cluster-id].[region].gcp.cloud.qdrant.io`)
   - Your API key from the dashboard

## Step 2: Deploy to Render

1. Fork or clone this repository to your GitHub account.

2. Go to [Render Dashboard](https://dashboard.render.com/) and create an account if needed.

3. Click "New +" and select "Web Service".

4. Connect your GitHub repository.

5. Render will detect the `render.yaml` file and suggest the service configuration.

6. Configure the environment variables:
   - `QDRANT_URL`: Your Qdrant Cloud cluster URL 
   - `QDRANT_API_KEY`: Your Qdrant Cloud API key

7. Click "Create Web Service".

8. Wait for the deployment to complete. Render will provide you with a URL for your service.

## Step 3: Initialize the Data

After deployment is complete, you need to trigger the data upload to Qdrant:

1. Make a POST request to the `/admin/upload` endpoint using curl or any API testing tool:

```bash
curl -X POST https://your-render-app-url.com/admin/upload
```

2. This will:
   - Create the collection in your Qdrant Cloud instance
   - Process and upload the game data from the CSV file
   - Generate embeddings for each game

This may take several minutes to complete, especially for the first upload.

## Step 4: Using the API

Once deployment and data upload are complete, you can use your API:

- API Documentation: `https://your-render-app-url.com/docs`
- Search Endpoint: `https://your-render-app-url.com/search?query=your+search+query`
- Recommendations: `https://your-render-app-url.com/recommend/{game_id}`

## Monitoring and Management

- Monitor your Render service through the Render dashboard
- Monitor your Qdrant database through the Qdrant Cloud dashboard

## Cost Considerations

- Render offers a free tier for web services with some limitations
- Qdrant Cloud has a free tier for testing, but you may need to upgrade for production use

## Troubleshooting

If you encounter issues:

1. Check the logs in your Render dashboard for API errors
2. Verify the connection to Qdrant by examining the logs
3. Make sure your environment variables are correctly set
4. Confirm the CSV file is properly included in the repository 