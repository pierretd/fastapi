# Import the enhanced search module 
import search_enhanced

# Test the search function with enhanced parameters
print("DEBUG: Testing search with enhanced parameters (using positional arguments)")
try:
    # Using positional arguments to avoid parameter name issues
    results = search_enhanced.search_games(
        "adventure",  # First arg: query/query_text 
        5,            # Second arg: limit
        False,        # Third arg: use_hybrid
        True,         # Fourth arg: use_sparse
        False         # Fifth arg: use_dense
    )
    
    # Print the results
    print("Results:", len(results))
    for i, result in enumerate(results):
        print(f"{i+1}. {result['id']} - {result['payload'].get('name', 'Unknown')} (Score: {result['score']})")
except Exception as e:
    print(f"Error: {e}")
    
    # Print function signature
    print("\nFunction signature:")
    print(search_enhanced.search_games.__code__.co_varnames[:search_enhanced.search_games.__code__.co_argcount]) 