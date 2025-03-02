import requests
import json
import time

# API base URL - Using local server instead since discovery API is not on Render yet
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("\n===== TESTING HEALTH ENDPOINT =====")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error in health check: {e}")
        return False

def test_discovery_games():
    """Test the discovery-games endpoint"""
    print("\n===== TESTING DISCOVERY GAMES ENDPOINT =====")
    try:
        # 1. Test with no preferences
        print("\nTesting discovery with no preferences:")
        payload = {
            "positive_ids": [],
            "negative_ids": [],
            "excluded_ids": [],
            "limit": 5
        }
        response = requests.post(f"{BASE_URL}/discovery-games", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            games = response.json()
            print(f"Found {len(games)} games")
            for i, game in enumerate(games):
                name = game.get('payload', {}).get('name', 'Unknown')
                print(f"  {i+1}. {name}")
            
            # If we found games, test with one as a positive preference
            if games:
                liked_game_id = games[0]['id']
                liked_game_name = games[0]['payload'].get('name', 'Unknown')
                
                # 2. Test with a liked game
                print(f"\nTesting discovery with liked game: {liked_game_name} (ID: {liked_game_id})")
                payload = {
                    "positive_ids": [liked_game_id],
                    "negative_ids": [],
                    "excluded_ids": [liked_game_id],  # Exclude the liked game
                    "limit": 5
                }
                response = requests.post(f"{BASE_URL}/discovery-games", json=payload)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    games_with_liked = response.json()
                    print(f"Found {len(games_with_liked)} games based on liked game")
                    for i, game in enumerate(games_with_liked):
                        name = game.get('payload', {}).get('name', 'Unknown')
                        score = game.get('score', 0)
                        print(f"  {i+1}. {name} (score: {score:.4f})")
                    
                    # If we have more games, test with one as a negative preference
                    if len(games) > 1:
                        disliked_game_id = games[1]['id']
                        disliked_game_name = games[1]['payload'].get('name', 'Unknown')
                        
                        # 3. Test with both liked and disliked game
                        print(f"\nTesting discovery with liked game: {liked_game_name} and disliked game: {disliked_game_name}")
                        payload = {
                            "positive_ids": [liked_game_id],
                            "negative_ids": [disliked_game_id],
                            "excluded_ids": [liked_game_id, disliked_game_id],
                            "limit": 5
                        }
                        response = requests.post(f"{BASE_URL}/discovery-games", json=payload)
                        print(f"Status Code: {response.status_code}")
                        
                        if response.status_code == 200:
                            games_with_preferences = response.json()
                            print(f"Found {len(games_with_preferences)} games based on preferences")
                            for i, game in enumerate(games_with_preferences):
                                name = game.get('payload', {}).get('name', 'Unknown')
                                score = game.get('score', 0)
                                print(f"  {i+1}. {name} (score: {score:.4f})")
                        else:
                            print(f"Error: {response.text}")
                else:
                    print(f"Error: {response.text}")
        else:
            print(f"Error: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error in discovery games: {e}")
        return False

def test_discovery_context():
    """Test the discovery-context endpoint"""
    print("\n===== TESTING DISCOVERY CONTEXT ENDPOINT =====")
    try:
        # 1. First get some games to find an ID
        payload = {
            "positive_ids": [],
            "negative_ids": [],
            "excluded_ids": [],
            "limit": 1
        }
        response = requests.post(f"{BASE_URL}/discovery-games", json=payload)
        
        if response.status_code == 200:
            games = response.json()
            if games:
                game_id = games[0]['id']
                game_name = games[0]['payload'].get('name', 'Unknown')
                
                # 2. Test the context endpoint with this game ID
                print(f"\nTesting discovery context with game: {game_name} (ID: {game_id})")
                response = requests.get(f"{BASE_URL}/discovery-context/{game_id}?limit=5")
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    context_games = response.json()
                    print(f"Found {len(context_games)} similar games")
                    for i, game in enumerate(context_games):
                        name = game.get('payload', {}).get('name', 'Unknown')
                        score = game.get('score', 0)
                        print(f"  {i+1}. {name} (score: {score:.4f})")
                    
                    # 3. Test with exclusion
                    if len(context_games) > 0:
                        excluded_id = context_games[0]['id']
                        print(f"\nTesting discovery context with exclusion (ID: {excluded_id})")
                        response = requests.get(f"{BASE_URL}/discovery-context/{game_id}?limit=5&excluded_ids={excluded_id}")
                        print(f"Status Code: {response.status_code}")
                        
                        if response.status_code == 200:
                            filtered_games = response.json()
                            print(f"Found {len(filtered_games)} games with exclusion")
                            for i, game in enumerate(filtered_games):
                                name = game.get('payload', {}).get('name', 'Unknown')
                                score = game.get('score', 0)
                                print(f"  {i+1}. {name} (score: {score:.4f})")
                        else:
                            print(f"Error: {response.text}")
                else:
                    print(f"Error: {response.text}")
            else:
                print("No games found to test context discovery")
        else:
            print(f"Error: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error in discovery context: {e}")
        return False

def main():
    """Main function to run all tests"""
    print("===== TESTING DISCOVERY API =====")
    
    # Wait a moment for the server to start up
    time.sleep(2)
    
    # Test health endpoint
    health_ok = test_health()
    if not health_ok:
        print("Health check failed, exiting tests")
        return
    
    # Test discovery-games endpoint
    discovery_games_ok = test_discovery_games()
    if not discovery_games_ok:
        print("Discovery games test failed")
    
    # Test discovery-context endpoint
    discovery_context_ok = test_discovery_context()
    if not discovery_context_ok:
        print("Discovery context test failed")
    
    print("\n===== DISCOVERY API TESTING COMPLETE =====")

if __name__ == "__main__":
    main() 