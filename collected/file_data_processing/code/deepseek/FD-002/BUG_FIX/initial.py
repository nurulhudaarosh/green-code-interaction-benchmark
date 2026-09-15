#!/usr/bin/env python3
"""
Offline NDJSON Analyzer
Extracts nested user and request fields, handles malformed JSON,
and generates deterministic statistics sorted by user ID.
"""

import json
import sys
from collections import defaultdict
from typing import Dict, List, Optional


def analyze_ndjson(filepath: str) -> Dict:
    """
    Analyze NDJSON file and return statistics.
    
    Args:
        filepath: Path to NDJSON file
        
    Returns:
        Dictionary with user statistics and malformed count
    """
    # Data structures
    user_stats = defaultdict(lambda: {
        'request_count': 0,
        'error_count': 0,
        'total_latency': 0.0,
        'endpoint_counts': defaultdict(int)
    })
    
    malformed_count = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Extract nested user and request fields
                    user = data.get('user')
                    request = data.get('request')
                    
                    # Skip if user or request is missing
                    if user is None or request is None:
                        malformed_count += 1
                        continue
                    
                    # Convert user to string for consistency
                    user_id = str(user)
                    
                    # Extract request details
                    endpoint = request.get('endpoint')
                    latency = request.get('latency')
                    status = request.get('status')
                    
                    # Validate required fields
                    if endpoint is None or latency is None:
                        malformed_count += 1
                        continue
                    
                    # Convert latency to float
                    try:
                        latency_val = float(latency)
                    except (TypeError, ValueError):
                        malformed_count += 1
                        continue
                    
                    # Update statistics
                    stats = user_stats[user_id]
                    stats['request_count'] += 1
                    stats['total_latency'] += latency_val
                    
                    # Determine if request is an error
                    is_error = False
                    
                    # Check status code if present
                    if status is not None:
                        try:
                            status_code = int(status)
                            if status_code >= 400:
                                is_error = True
                        except (TypeError, ValueError):
                            pass
                    
                    # Check for explicit error field
                    if request.get('error') is not None:
                        is_error = True
                    
                    if is_error:
                        stats['error_count'] += 1
                    
                    # Count endpoint requests
                    stats['endpoint_counts'][str(endpoint)] += 1
                    
                except json.JSONDecodeError:
                    malformed_count += 1
                except Exception:
                    malformed_count += 1
                    
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Build results with deterministic sorting
    results = {}
    
    for user_id, stats in user_stats.items():
        # Calculate average latency
        avg_latency = stats['total_latency'] / stats['request_count'] if stats['request_count'] > 0 else 0.0
        
        # Find most-requested endpoint with lexical tie-breaking
        most_requested = None
        if stats['endpoint_counts']:
            # Find maximum count
            max_count = max(stats['endpoint_counts'].values())
            
            # Get all endpoints with max count
            top_endpoints = [
                endpoint for endpoint, count in stats['endpoint_counts'].items()
                if count == max_count
            ]
            
            # Sort lexically and pick the first (smallest)
            most_requested = sorted(top_endpoints)[0]
        
        results[user_id] = {
            'user_id': user_id,
            'request_count': stats['request_count'],
            'error_count': stats['error_count'],
            'average_latency': round(avg_latency, 6),
            'most_requested_endpoint': most_requested
        }
    
    # Sort by user ID (lexicographically)
    sorted_results = dict(sorted(results.items()))
    
    return {
        'users': sorted_results,
        'malformed_count': malformed_count
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <ndjson_file>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    result = analyze_ndjson(filepath)
    
    # Print malformed count to stderr
    print(f"Malformed JSON lines: {result['malformed_count']}", file=sys.stderr)
    
    # Write deterministic JSON sorted by user ID
    json.dump(result['users'], sys.stdout, indent=2, sort_keys=True)
    print()  # Add newline


if __name__ == "__main__":
    main()