#!/usr/bin/env python3
"""
Customer Event CSV Utility

This script processes customer event CSV files with the following operations:
1. Removes duplicate customer/timestamp records by keeping the last occurrence
2. Selects the chronologically latest record for each customer
3. Calculates count and total amount by status using retained records
4. Writes deterministic output sorted by customer_id

Usage:
    python customer_event_utility.py input.csv output.csv

Input CSV format: customer_id,timestamp,status,amount
Output CSV format: customer_id,timestamp,status,amount
"""

import csv
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object with multiple format support."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    # If no format matches, try parsing with dateutil if available
    try:
        from dateutil import parser
        return parser.parse(timestamp_str)
    except (ImportError, ValueError):
        pass
    
    raise ValueError(f"Unable to parse timestamp: {timestamp_str}")


def read_csv_file(filename: str) -> List[Dict]:
    """Read CSV file and return list of dictionaries."""
    records = []
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            # Detect delimiter (comma or semicolon)
            sample = csvfile.read(1024)
            csvfile.seek(0)
            delimiter = ',' if ',' in sample else ';'
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Normalize column names
            fieldnames = [col.strip().lower() for col in reader.fieldnames]
            
            for row in reader:
                # Create normalized record
                record = {}
                for orig_col, normalized_col in zip(reader.fieldnames, fieldnames):
                    record[normalized_col] = row[orig_col].strip()
                
                # Validate required columns
                required = ['customer_id', 'timestamp', 'status', 'amount']
                if all(col in record for col in required):
                    records.append(record)
                else:
                    print(f"Warning: Skipping row with missing columns: {row}")
                    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)
    
    return records


def remove_duplicate_keep_last(records: List[Dict]) -> List[Dict]:
    """
    Remove duplicate customer/timestamp records by keeping the last occurrence.
    Uses (customer_id, timestamp) as key for uniqueness.
    """
    unique_records = {}
    
    for record in records:
        key = (record['customer_id'], record['timestamp'])
        unique_records[key] = record
    
    return list(unique_records.values())


def get_latest_record_per_customer(records: List[Dict]) -> List[Dict]:
    """
    Select the chronologically latest record for each customer.
    If timestamps are identical, keep the first encountered.
    """
    latest_records = {}
    
    for record in records:
        customer_id = record['customer_id']
        timestamp_str = record['timestamp']
        
        try:
            current_time = parse_timestamp(timestamp_str)
        except ValueError:
            print(f"Warning: Skipping record with invalid timestamp: {record}")
            continue
        
        if customer_id not in latest_records:
            latest_records[customer_id] = record
        else:
            existing_time = parse_timestamp(latest_records[customer_id]['timestamp'])
            if current_time > existing_time:
                latest_records[customer_id] = record
    
    return list(latest_records.values())


def calculate_status_stats(records: List[Dict]) -> Dict[str, Tuple[int, float]]:
    """
    Calculate count and total amount by status.
    Returns dict mapping status -> (count, total_amount)
    """
    stats = defaultdict(lambda: [0, 0.0])
    
    for record in records:
        status = record['status']
        try:
            amount = float(record['amount'])
        except ValueError:
            print(f"Warning: Invalid amount '{record['amount']}' for record: {record}")
            continue
        
        stats[status][0] += 1
        stats[status][1] += amount
    
    return {status: (count, total) for status, (count, total) in stats.items()}


def write_csv_file(records: List[Dict], filename: str) -> None:
    """Write records to CSV file sorted by customer_id."""
    if not records:
        print("Warning: No records to write.")
        return
    
    # Sort by customer_id (convert to int for numeric sorting, fallback to string)
    try:
        sorted_records = sorted(records, key=lambda x: int(x['customer_id']))
    except ValueError:
        sorted_records = sorted(records, key=lambda x: x['customer_id'])
    
    fieldnames = ['customer_id', 'timestamp', 'status', 'amount']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            writer.writerows(sorted_records)
            print(f"Successfully wrote {len(sorted_records)} records to '{filename}'")
    except Exception as e:
        print(f"Error writing file '{filename}': {e}")
        sys.exit(1)


def print_statistics(stats: Dict[str, Tuple[int, float]]) -> None:
    """Print status statistics in a formatted manner."""
    if not stats:
        print("No statistics to display.")
        return
    
    print("\n" + "=" * 50)
    print("STATUS STATISTICS")
    print("=" * 50)
    print(f"{'Status':<15} {'Count':<10} {'Total Amount':<15}")
    print("-" * 50)
    
    # Sort by status for deterministic output
    for status in sorted(stats.keys()):
        count, total = stats[status]
        print(f"{status:<15} {count:<10} {total:>14.2f}")
    
    print("=" * 50)


def main():
    """Main function to process customer event CSV files."""
    if len(sys.argv) != 3:
        print("Usage: python customer_event_utility.py <input_file.csv> <output_file.csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Processing '{input_file}'...")
    
    # Step 1: Read input CSV
    records = read_csv_file(input_file)
    print(f"Read {len(records)} records from input file.")
    
    if not records:
        print("No valid records found. Exiting.")
        sys.exit(1)
    
    # Step 2: Remove duplicate customer/timestamp records (keep last)
    unique_records = remove_duplicate_keep_last(records)
    removed_duplicates = len(records) - len(unique_records)
    print(f"Removed {removed_duplicates} duplicate records (kept last occurrence).")
    
    # Step 3: Select chronologically latest record for each customer
    latest_records = get_latest_record_per_customer(unique_records)
    removed_older = len(unique_records) - len(latest_records)
    print(f"Selected {len(latest_records)} latest records per customer (removed {removed_older} older records).")
    
    # Step 4: Calculate statistics by status
    stats = calculate_status_stats(latest_records)
    print_statistics(stats)
    
    # Step 5: Write output CSV sorted by customer_id
    write_csv_file(latest_records, output_file)
    
    # Summary
    print(f"\nProcessing complete!")
    print(f"  - Input records: {len(records)}")
    print(f"  - Unique records: {len(unique_records)}")
    print(f"  - Latest records: {len(latest_records)}")
    print(f"  - Statuses found: {len(stats)}")
    print(f"  - Output file: {output_file}")


if __name__ == "__main__":
    main()