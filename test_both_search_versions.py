#!/usr/bin/env python
"""
Test script to demonstrate the differences between the search module versions.
- search (package): Original module with basic parameters
- search_enhanced: Enhanced module with additional parameters
"""

# Import both versions
import search  # From search/ directory (package)
import search_enhanced  # From search_enhanced.py (standalone module)

def test_search_module_versions():
    """
    Test both search module versions and demonstrate their parameter differences
    """
    print("\n===== SEARCH MODULE VERSIONS TEST =====")
    
    # Print function signatures
    print("\nOriginal search.search_games signature:")
    print(search.search_games.__code__.co_varnames[:search.search_games.__code__.co_argcount])
    
    print("\nEnhanced search_enhanced.search_games signature:")
    print(search_enhanced.search_games.__code__.co_varnames[:search_enhanced.search_games.__code__.co_argcount])
    
    # Test original search
    print("\n----- Testing original search module -----")
    try:
        original_results = search.search_games(
            "adventure",  # query_text
            5,  # limit
            True,  # use_hybrid
        )
        print(f"Original search returned {len(original_results)} results")
    except Exception as e:
        print(f"Error with original search: {e}")
    
    # Test enhanced search
    print("\n----- Testing enhanced search module -----")
    try:
        enhanced_results = search_enhanced.search_games(
            "adventure",  # query 
            5,  # limit
            False,  # use_hybrid
            True,  # use_sparse
            False,  # use_dense
        )
        print(f"Enhanced search returned {len(enhanced_results)} results")
    except Exception as e:
        print(f"Error with enhanced search: {e}")

if __name__ == "__main__":
    test_search_module_versions() 