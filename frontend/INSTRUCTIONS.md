# How to Run the Steam Games Search Application

This application consists of two parts:
1. A FastAPI backend that provides search and recommendation functionality
2. A Next.js frontend that provides the user interface

## Running the Backend

From the project root directory, run:

```bash
./start-backend.sh
```

This will start the FastAPI server on http://localhost:8000.

You can verify the API is running by visiting:
- http://localhost:8000/docs - API documentation
- http://localhost:8000/health - Health check endpoint

## Running the Frontend

From the frontend directory, run:

```bash
./start-frontend.sh
```

This will:
1. Set up a Python virtual environment if needed
2. Install required Python dependencies
3. Start the Next.js development server

The frontend will be available at http://localhost:3000.

## Testing the Application

1. Open your browser and navigate to http://localhost:3000
2. Use the search page to search for games
3. Click on game results to see details and recommendations

## Troubleshooting

If you encounter any issues:

1. Ensure both backend and frontend servers are running
2. Check that the BACKEND_URL environment variable is set correctly
3. Check the browser console for any JavaScript errors
4. Check the terminal windows for any backend errors

## Development Notes

- The frontend communicates with the backend through a FastAPI proxy at `/api/py/`
- Any changes to the frontend code will be automatically reflected in the browser
- Changes to the backend API code will require a restart of the backend server 