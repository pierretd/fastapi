# Search Module Documentation

This codebase has multiple search modules which can cause confusion when importing.

## Search Module Structure

1. **search/ (package)**
   - Imported with `import search`
   - Located in the `search/` directory
   - Defined in `search/search.py` and imported through `search/__init__.py`
   - Function `search_games` signature: 
     ```python
     def search_games(query_text, limit=5, use_hybrid=True, use_sparse=False, use_dense=False, filter_params=None)
     ```

2. **search.py (module)**
   - Imported with `import search` when the package is not found
   - Located in the root directory
   - Function `search_games` signature:
     ```python
     def search_games(query, limit=12, use_hybrid=True, use_sparse=False, use_dense=False, filter_params=None)
     ```

3. **search_enhanced.py (module)**
   - New renamed module that clearly indicates its enhanced functionality
   - Imported with `import search_enhanced`
   - Function `search_games` with additional parameters:
     ```python
     def search_games(query, limit=12, use_hybrid=True, use_sparse=False, use_dense=False, filter_params=None)
     ```

## Recommended Imports

To avoid confusion, use these import patterns:

```python
# For original search functionality
import search

# For enhanced search functionality 
import search_enhanced
```

## Using in main.py

```python
# Original approach importing search directly
import search

# Enhanced approach using aliasing for clarity
import search_enhanced as search
```

## Parameter Mapping

The two modules use slightly different parameter names:

| search/ (package) | search_enhanced.py      |
|-------------------|-------------------------|
| query_text        | query                   |
| limit             | limit                   |
| use_hybrid        | use_hybrid              |
| use_sparse        | use_sparse              |
| use_dense         | use_dense               |
| filter_params     | filter_params           | 