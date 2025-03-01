"""
Performance test script for the Steam Games Search API.

This script benchmarks the search functionality and stress tests the API.
It measures response times, throughput, and error rates under various loads.
"""

import requests
import json
import os
import time
import statistics
import concurrent.futures
import random
import argparse
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Set the base URL for API calls
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Example gaming-related search queries of varying complexity
SEARCH_QUERIES = [
    # Simple genre queries
    "RPG", "FPS", "strategy", "puzzle", "racing", "horror", "adventure", "simulation",
    
    # More specific game types
    "open world RPG", "tactical shooter", "turn-based strategy", "puzzle platformer",
    
    # Complex queries with features
    "open world RPG with dragons", "multiplayer shooter with vehicles",
    "strategy games with base building", "horror games with zombies",
    "racing games with customization", "relaxing puzzle games",
    
    # Very specific requests 
    "medieval open world RPG with magic and dragons",
    "sci-fi first person shooter with space travel and aliens",
    "historical strategy games with diplomacy and economy management",
    "relaxing puzzle games with beautiful art style and no time pressure",
    "zombie survival games with crafting and base building"
]

def benchmark_search(query, use_hybrid=True, limit=5):
    """Benchmark a single search request"""
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/search", 
            params={"query": query, "limit": limit, "use_hybrid": use_hybrid}
        )
        end_time = time.time()
        
        if response.status_code == 200:
            results = response.json()
            return {
                "success": True,
                "query": query,
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "results_count": len(results),
                "error": None
            }
        else:
            return {
                "success": False,
                "query": query,
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "results_count": 0,
                "error": response.text
            }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "query": query,
            "response_time": end_time - start_time,
            "status_code": None,
            "results_count": 0,
            "error": str(e)
        }

def run_serial_benchmark(queries=None, use_hybrid=True, limit=5, iterations=1):
    """Run serial benchmarks, one query at a time"""
    if queries is None:
        queries = SEARCH_QUERIES
    
    all_results = []
    for _ in range(iterations):
        for query in tqdm(queries, desc="Running serial benchmark"):
            result = benchmark_search(query, use_hybrid, limit)
            all_results.append(result)
    
    return all_results

def run_parallel_benchmark(queries=None, use_hybrid=True, limit=5, iterations=1, max_workers=10):
    """Run parallel benchmarks, simulating multiple concurrent users"""
    if queries is None:
        queries = SEARCH_QUERIES
    
    all_results = []
    for iteration in range(iterations):
        print(f"Running parallel benchmark iteration {iteration+1}/{iterations}")
        # Create list of all tasks to submit
        tasks = []
        for query in queries:
            tasks.append((query, use_hybrid, limit))
        
        # Run tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(benchmark_search, q, h, l) for q, h, l in tasks]
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Completing requests"):
                result = future.result()
                all_results.append(result)
    
    return all_results

def analyze_results(results):
    """Analyze benchmark results"""
    if not results:
        print("No results to analyze!")
        return
    
    # Calculate statistics
    response_times = [r["response_time"] for r in results]
    success_count = sum(1 for r in results if r["success"])
    error_count = sum(1 for r in results if not r["success"])
    
    # Print summary
    print("\n=== Benchmark Results ===")
    print(f"Total Requests: {len(results)}")
    print(f"Successful Requests: {success_count} ({success_count/len(results)*100:.2f}%)")
    print(f"Failed Requests: {error_count} ({error_count/len(results)*100:.2f}%)")
    
    if response_times:
        print("\nResponse Time (seconds):")
        print(f"  Minimum: {min(response_times):.4f}")
        print(f"  Maximum: {max(response_times):.4f}")
        print(f"  Average: {statistics.mean(response_times):.4f}")
        print(f"  Median: {statistics.median(response_times):.4f}")
        if len(response_times) > 1:
            print(f"  Std Dev: {statistics.stdev(response_times):.4f}")
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        print(f"  95th Percentile: {p95:.4f}")
        print(f"  99th Percentile: {p99:.4f}")
    
    # Group by query complexity
    short_queries = [r for r in results if len(r["query"].split()) <= 2]
    medium_queries = [r for r in results if 3 <= len(r["query"].split()) <= 5]
    long_queries = [r for r in results if len(r["query"].split()) > 5]
    
    print("\nResponse Times by Query Complexity:")
    
    if short_queries:
        short_times = [r["response_time"] for r in short_queries]
        print(f"  Short Queries: Avg {statistics.mean(short_times):.4f}s")
    
    if medium_queries:
        medium_times = [r["response_time"] for r in medium_queries]
        print(f"  Medium Queries: Avg {statistics.mean(medium_times):.4f}s")
    
    if long_queries:
        long_times = [r["response_time"] for r in long_queries]
        print(f"  Long Queries: Avg {statistics.mean(long_times):.4f}s")
    
    # Print most expensive queries
    print("\nSlowest Queries:")
    sorted_by_time = sorted(results, key=lambda x: x["response_time"], reverse=True)
    for i, result in enumerate(sorted_by_time[:5]):
        print(f"  {i+1}. '{result['query']}' - {result['response_time']:.4f}s")
    
    # Print errors if any
    if error_count > 0:
        print("\nErrors:")
        error_results = [r for r in results if not r["success"]]
        for i, result in enumerate(error_results[:5]):  # Show first 5 errors
            print(f"  {i+1}. Query: '{result['query']}'")
            print(f"     Error: {result['error']}")
            print(f"     Status: {result['status_code']}")

def main():
    """Main function to run benchmarks"""
    parser = argparse.ArgumentParser(description="Benchmark Steam Games Search API")
    parser.add_argument("--mode", choices=["serial", "parallel", "both"], default="both",
                        help="Benchmark mode: serial, parallel, or both")
    parser.add_argument("--iterations", type=int, default=1,
                        help="Number of iterations to run for each benchmark")
    parser.add_argument("--workers", type=int, default=10,
                        help="Number of concurrent workers for parallel benchmark")
    parser.add_argument("--hybrid", type=bool, default=True,
                        help="Whether to use hybrid search")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of results to return for each query")
    
    args = parser.parse_args()
    
    print(f"Starting search performance benchmark for {BASE_URL}...")
    print(f"Mode: {args.mode}, Workers: {args.workers}, Iterations: {args.iterations}")
    print(f"Using hybrid search: {args.hybrid}, Result limit: {args.limit}")
    
    all_results = []
    
    if args.mode in ["serial", "both"]:
        print("\n=== Running Serial Benchmark ===")
        print("This simulates users making requests one after another")
        serial_results = run_serial_benchmark(
            use_hybrid=args.hybrid,
            limit=args.limit,
            iterations=args.iterations
        )
        print("\n=== Serial Benchmark Results ===")
        analyze_results(serial_results)
        all_results.extend(serial_results)
    
    if args.mode in ["parallel", "both"]:
        print("\n=== Running Parallel Benchmark ===")
        print(f"This simulates {args.workers} concurrent users")
        parallel_results = run_parallel_benchmark(
            use_hybrid=args.hybrid,
            limit=args.limit,
            iterations=args.iterations,
            max_workers=args.workers
        )
        print("\n=== Parallel Benchmark Results ===")
        analyze_results(parallel_results)
        all_results.extend(parallel_results)
    
    if args.mode == "both":
        print("\n=== Overall Benchmark Results ===")
        analyze_results(all_results)
    
    print("\n=== Performance Testing Complete! ===")

if __name__ == "__main__":
    main() 