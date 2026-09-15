#!/usr/bin/env python3
"""
Offline NDJSON Analyzer
Extracts nested user and request fields, handles malformed JSON,
and generates deterministic statistics sorted by user ID.
"""

import json
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


def analyze_ndjson(filepath: str) -> Dict:
    """
    Analyze NDJSON file and return statistics.
    
    Args:
        filepath: Path to NDJSON file
        
    Returns:
        Dictionary with statistics and malformed count
    """
    # Data structures for aggregation
    user_stats = defaultdict(lambda: {
        'request_count': 0,
        'error_count': 0,
        'total_latency': 0.0,
        'endpoint_counts': defaultdict(int)
    })
    
    malformed_count = 0
    line_number = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                line = line.strip()
                
                if not line:  # Skip empty lines
                    continue
                
                try:
                    # Parse JSON line
                    data = json.loads(line)
                    
                    # Extract user and request fields
                    user = data.get('user')
                    request = data.get('request')
                    
                    # Skip if user or request is missing or invalid
                    if user is None or request is None:
                        malformed_count += 1
                        continue
                    
                    # Ensure user is a valid identifier (string or number)
                    user_str = str(user)
                    
                    # Extract request fields
                    endpoint = request.get('endpoint')
                    latency = request.get('latency')
                    status = request.get('status')
                    
                    # Skip if essential fields are missing
                    if endpoint is None or latency is None:
                        malformed_count += 1
                        continue
                    
                    # Validate latency is numeric
                    try:
                        latency_float = float(latency)
                    except (TypeError, ValueError):
                        malformed_count += 1
                        continue
                    
                    # Update user statistics
                    stats = user_stats[user_str]
                    stats['request_count'] += 1
                    stats['total_latency'] += latency_float
                    
                    # Count errors (status >= 400 or error field present)
                    is_error = False
                    if status is not None:
                        try:
                            status_int = int(status)
                            if status_int >= 400:
                                is_error = True
                        except (TypeError, ValueError):
                            pass
                    
                    # Also check for explicit error field
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
    
    # Build final results
    results = {}
    for user, stats in user_stats.items():
        # Calculate average latency
        avg_latency = stats['total_latency'] / stats['request_count'] if stats['request_count'] > 0 else 0.0
        
        # Find most-requested endpoint with lexical tie-breaking
        if stats['endpoint_counts']:
            max_count = max(stats['endpoint_counts'].values())
            # Get all endpoints with max count and sort lexically
            top_endpoints = sorted([
                endpoint for endpoint, count in stats['endpoint_counts'].items()
                if count == max_count
            ])
            most_requested_endpoint = top_endpoints[0]  # Lexically smallest among ties
        else:
            most_requested_endpoint = None
        
        results[user] = {
            'user_id': user,
            'request_count': stats['request_count'],
            'error_count': stats['error_count'],
            'average_latency': round(avg_latency, 6),  # Round for deterministic output
            'most_requested_endpoint': most_requested_endpoint
        }
    
    # Sort by user ID (lexicographically as strings)
    sorted_results = {
        user: results[user]
        for user in sorted(results.keys())
    }
    
    return {
        'users': sorted_results,
        'malformed_count': malformed_count,
        'total_lines': line_number
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
    print(f"Total lines processed: {result['total_lines']}", file=sys.stderr)
    
    # Output deterministic JSON sorted by user ID
    json.dump(result['users'], sys.stdout, indent=2, sort_keys=True)
    print()  # Newline at end


if __name__ == "__main__":
    main()