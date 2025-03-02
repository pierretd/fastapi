"""
Test script to verify that importing get_discovery_games from search.search works correctly.
This simulates the import path that Render is trying to use.
"""

try:
    # Try to import the functions from search.search
    from search.search import get_discovery_games, get_discovery_context
    
    print("✅ Successfully imported get_discovery_games and get_discovery_context from search.search")
    
    # Test a basic call to get_discovery_games
    print("\nTesting get_discovery_games with no parameters:")
    games = get_discovery_games(limit=3)
    
    if games:
        print(f"Successfully retrieved {len(games)} games:")
        for i, game in enumerate(games):
            name = game.get('payload', {}).get('name', 'Unknown')
            print(f"  {i+1}. {name}")
    else:
        print("No games returned from get_discovery_games")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error testing functions: {e}") 