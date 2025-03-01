# Deployment Guide

This guide explains how to deploy the Steam Games Search frontend to Vercel.

## Prerequisites

1. GitHub account
2. Vercel account (you can sign up with your GitHub account)

## Deployment Steps

### 1. Push your code to GitHub

If your code is already on GitHub, you can skip this step. Otherwise:

```bash
# Initialize a new git repository if not already done
git init

# Add all files
git add .

# Commit the changes
git commit -m "Prepare for deployment"

# Add a remote GitHub repository (create one on GitHub first)
git remote add origin https://github.com/yourusername/steam-games-search.git

# Push the code
git push -u origin main
```

### 2. Deploy to Vercel

#### Option 1: Using the Vercel Dashboard

1. Go to [Vercel](https://vercel.com) and sign in with your GitHub account
2. Click "Add New..." and select "Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework Preset: Next.js
   - Root Directory: `frontend` (if your frontend code is in a subdirectory)
   - Environment Variables: 
     - Name: `BACKEND_URL`
     - Value: `https://fastapi-5aw3.onrender.com`
5. Click "Deploy"

#### Option 2: Using the Vercel CLI

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Log in to Vercel:
   ```bash
   vercel login
   ```

3. Deploy the project:
   ```bash
   cd frontend
   vercel
   ```

4. Follow the prompts:
   - Set up and deploy: Yes
   - Link to existing project: No
   - Project name: steam-games-search (or your preferred name)
   - Root directory: ./
   - Want to override settings: Yes
   - Environment variables: Add BACKEND_URL=https://fastapi-5aw3.onrender.com

### 3. Verify Deployment

1. After the deployment is complete, Vercel will provide you with a URL to access your deployed application.
2. Visit the URL to ensure everything is working correctly.
3. Test the search functionality, random games, and other features to make sure they're working with the backend API.

## Updating the Deployment

When you make changes to your application, you can update the deployment by pushing the changes to your GitHub repository. Vercel will automatically redeploy your application.

```bash
git add .
git commit -m "Update application"
git push
```

## Custom Domain (Optional)

If you want to use a custom domain for your application:

1. Go to your project on the Vercel dashboard
2. Click "Settings"
3. Go to "Domains"
4. Add your domain and follow the instructions to configure DNS settings 