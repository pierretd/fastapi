# Local Development Guide

While this application is designed for cloud deployment, you can also run it locally for development and testing purposes.

## Requirements

- Python 3.8+
- Qdrant (local instance or cloud)
- Steam games CSV file

## Setup Options

There are two ways to set up local development:

1. Direct Python installation
2. Docker Compose (recommended)

## Option 1: Direct Python Installation

### 1. Clone the repository:

```bash
git clone https://github.com/yourusername/steam-games-search.git
cd steam-games-search
```

### 2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up your environment variables:

```bash
cp .env.example .env
```

Edit the `.env` file with your Qdrant connection details and other settings.

### 4. Run a local Qdrant instance:

You can run Qdrant locally using Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 5. Update your .env file to point to your local Qdrant:

```
QDRANT_URL=http://localhost:6333
```

### 6. Run the FastAPI application:

```bash
python main.py
```

The server will start at http://localhost:8000.

### 7. Initialize the data:

Make a POST request to the data upload endpoint:

```bash
curl -X POST http://localhost:8000/admin/upload
```

## Option 2: Docker Compose (Recommended)

This method runs both the FastAPI application and Qdrant in Docker containers.

### 1. Clone the repository:

```bash
git clone https://github.com/yourusername/steam-games-search.git
cd steam-games-search
```

### 2. Run the application with Docker Compose:

```bash
docker-compose up -d
```

This will:
- Build the Docker image for the FastAPI application
- Pull and run the Qdrant Docker image
- Configure the network between the services
- Mount the necessary volumes

### 3. Initialize the data:

```bash
curl -X POST http://localhost:8000/admin/upload
```

## Accessing the API

- API Documentation: http://localhost:8000/docs
- Search Endpoint: http://localhost:8000/search?query=your+search+query
- Recommendations: http://localhost:8000/recommend/{game_id}

## Development Workflow

1. Make changes to the code
2. If using Direct Python Installation, the server will automatically reload if you used `uvicorn` with the `--reload` flag
3. If using Docker Compose, rebuild and restart the containers:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Testing

To test the application locally:

```bash
# Basic test search
curl "http://localhost:8000/search?query=open%20world%20RPG"

# Test recommendations (replace 123456 with actual game ID)
curl "http://localhost:8000/recommend/123456"
``` 