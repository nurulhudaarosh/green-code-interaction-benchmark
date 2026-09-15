#!/usr/bin/env python3
"""
Offline NDJSON Analyzer
Extracts nested user and request fields, handles malformed JSON,
and produces deterministic statistics.
"""

import json
import sys
from collections import defaultdict
from typing import Dict, Any


class NDJSONAnalyzer:
    def __init__(self):
        self.malformed_count = 0
        self.user_stats: Dict[str, Dict] = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'latency_sum': 0.0,
            'latency_count': 0,
            'endpoint_counts': defaultdict(int)
        })
    
    def process_line(self, line: str) -> None:
        """Process a single line of NDJSON. Skips malformed lines and counts them."""
        line = line.strip()
        if not line:
            return
        
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            self.malformed_count += 1
            return
        
        # Extract user and request fields
        user = self._extract_nested_field(data, 'user')
        request = self._extract_nested_field(data, 'request')
        
        # Skip if user or request is missing (count as malformed)
        if user is None or request is None:
            self.malformed_count += 1
            return
        
        # Ensure user is a string
        user = str(user)
        stats = self.user_stats[user]
        stats['request_count'] += 1
        
        # Extract endpoint
        endpoint = self._extract_nested_field(request, 'endpoint')
        if endpoint is not None:
            stats['endpoint_counts'][str(endpoint)] += 1
        
        # Check for error
        error = self._extract_nested_field(request, 'error')
        if error is not None:
            # Convert to boolean if possible
            if isinstance(error, bool):
                is_error = error
            elif isinstance(error, (int, float)):
                is_error = bool(error)
            elif isinstance(error, str):
                is_error = error.lower() in ('true', '1', 'yes', 'y')
            else:
                is_error = bool(error)
            
            if is_error:
                stats['error_count'] += 1
        
        # Extract latency
        latency = self._extract_nested_field(request, 'latency')
        if latency is not None:
            try:
                latency_val = float(latency)
                if latency_val >= 0:  # Only count non-negative latencies
                    stats['latency_sum'] += latency_val
                    stats['latency_count'] += 1
                else:
                    # Negative latency is malformed
                    stats['request_count'] -= 1
                    self.malformed_count += 1
            except (ValueError, TypeError):
                # Invalid latency format counts as malformed for this record
                stats['request_count'] -= 1
                self.malformed_count += 1
    
    def _extract_nested_field(self, obj: Any, field_name: str) -> Any:
        """Extract a field from possibly nested structure."""
        if obj is None:
            return None
        
        # Direct match
        if isinstance(obj, dict) and field_name in obj:
            return obj[field_name]
        
        # Check for nested structure
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Direct nested
                if isinstance(value, dict) and field_name in value:
                    return value[field_name]
                
                # Array of objects
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and field_name in item:
                            return item[field_name]
                        # Recursively check nested in array items
                        nested = self._extract_nested_field(item, field_name)
                        if nested is not None:
                            return nested
                
                # Recursively check nested dictionaries
                if isinstance(value, dict):
                    nested = self._extract_nested_field(value, field_name)
                    if nested is not None:
                        return nested
        
        return None
    
    def get_most_requested_endpoint(self, endpoint_counts: Dict[str, int]) -> str:
        """
        Get most requested endpoint with lexical tie-breaking.
        If two endpoints have the same count, choose the lexically smaller endpoint.
        """
        if not endpoint_counts:
            return ""
        
        # Find max count
        max_count = max(endpoint_counts.values())
        
        # Get all endpoints with max count
        top_endpoints = [ep for ep, count in endpoint_counts.items() if count == max_count]
        
        # Lexical tie-breaking: choose the lexically smallest endpoint
        return min(top_endpoints)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate the final report."""
        report = {}
        
        # Sort users by ID (lexicographically) for deterministic output
        for user in sorted(self.user_stats.keys()):
            stats = self.user_stats[user]
            
            # Calculate average latency
            avg_latency = 0.0
            if stats['latency_count'] > 0:
                avg_latency = stats['latency_sum'] / stats['latency_count']
            
            # Get most requested endpoint with lexical tie-breaking
            most_requested = self.get_most_requested_endpoint(stats['endpoint_counts'])
            
            report[user] = {
                'request_count': stats['request_count'],
                'error_count': stats['error_count'],
                'average_latency': round(avg_latency, 6),
                'most_requested_endpoint': most_requested
            }
        
        return report
    
    def process_file(self, file_path: str) -> None:
        """Process an NDJSON file. Continues processing even if malformed lines are found."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        self.process_line(line)
                    except Exception:
                        # Any unexpected error during processing counts as malformed
                        self.malformed_count += 1
                        # Continue processing the rest of the file
                        continue
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error processing file: {e}", file=sys.stderr)
            sys.exit(1)
    
    def save_report(self, output_file: str = None) -> str:
        """Save the report as JSON and return the JSON string."""
        report = self.generate_report()
        
        # Add malformed count to report metadata
        full_report = {
            'malformed_lines': self.malformed_count,
            'users': report
        }
        
        # Deterministic JSON output
        json_output = json.dumps(full_report, indent=2, sort_keys=True)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
        
        return json_output


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python ndjson_analyzer.py <input_file> [output_file]", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyzer = NDJSONAnalyzer()
    analyzer.process_file(input_file)
    
    json_output = analyzer.save_report(output_file)
    
    if not output_file:
        print(json_output)


if __name__ == "__main__":
    main()