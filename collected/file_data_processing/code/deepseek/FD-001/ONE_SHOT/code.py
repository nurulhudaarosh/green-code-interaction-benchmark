#!/usr/bin/env python3
"""
Customer Event CSV Processor

This utility processes customer event CSV files with the following operations:
1. Removes duplicate customer/timestamp records (keeps last occurrence)
2. Selects chronologically latest record for each customer
3. Calculates count and total amount by status using retained records
4. Writes deterministic output sorted by customer_id

Usage:
    python customer_event_processor.py input.csv output.csv
    python customer_event_processor.py --help
"""

import argparse
import csv
import sys
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
import os


class CustomerEventProcessor:
    """Process customer event CSV files with deduplication and aggregation."""
    
    def __init__(self):
        self.records: Dict[str, Dict] = {}  # customer_id -> latest record
        self.status_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {'count': 0, 'total_amount': 0.0}
        )
        self.duplicate_count = 0
        self.processed_count = 0
        self.errors = []
        
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string with support for multiple formats.
        
        Args:
            timestamp_str: Timestamp string to parse
            
        Returns:
            datetime object or None if parsing fails
        """
        # Common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y%m%d %H:%M:%S',
            '%b %d %Y %H:%M:%S',
            '%d-%b-%Y %H:%M:%S',
        ]
        
        timestamp_str = timestamp_str.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # Try parsing with dateutil if available (optional dependency)
        try:
            from dateutil import parser
            return parser.parse(timestamp_str)
        except (ImportError, ValueError):
            pass
        
        # Last resort: try to parse common ISO formats
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        return None
    
    def validate_record(self, record: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate that a record has all required fields.
        
        Args:
            record: Dictionary representing a CSV row
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['customer_id', 'timestamp', 'status', 'amount']
        
        for field in required_fields:
            if field not in record or not record[field].strip():
                return False, f"Missing or empty field: {field}"
        
        # Validate amount is numeric
        try:
            float(record['amount'].strip())
        except ValueError:
            return False, f"Invalid amount: {record['amount']}"
        
        # Validate timestamp
        if self.parse_timestamp(record['timestamp']) is None:
            return False, f"Invalid timestamp: {record['timestamp']}"
        
        return True, ""
    
    def process_record(self, record: Dict[str, str]) -> None:
        """
        Process a single record, handling deduplication and updates.
        
        Args:
            record: Dictionary representing a CSV row
        """
        customer_id = record['customer_id'].strip()
        timestamp_str = record['timestamp'].strip()
        
        # Parse timestamp for comparison
        timestamp = self.parse_timestamp(timestamp_str)
        if timestamp is None:
            self.errors.append(f"Could not parse timestamp: {timestamp_str}")
            return
        
        # Check if we already have a record for this customer
        if customer_id in self.records:
            existing_record = self.records[customer_id]
            existing_timestamp = self.parse_timestamp(existing_record['timestamp'])
            
            if existing_timestamp is None:
                # Shouldn't happen as we validate before storing
                self.records[customer_id] = record
                return
            
            # Keep the latest record (chronologically)
            if timestamp > existing_timestamp:
                # We're keeping the new record, need to adjust stats for old record
                self._remove_from_stats(existing_record)
                self.records[customer_id] = record
                self._add_to_stats(record)
            elif timestamp == existing_timestamp:
                # Duplicate timestamp, keep the later occurrence (this one)
                # But since we process sequentially, this is the same timestamp
                # We'll keep this one as the "last occurrence"
                self._remove_from_stats(existing_record)
                self.records[customer_id] = record
                self._add_to_stats(record)
                self.duplicate_count += 1
            # If timestamp is older, ignore this record
        else:
            # New customer, add record
            self.records[customer_id] = record
            self._add_to_stats(record)
            
        self.processed_count += 1
    
    def _add_to_stats(self, record: Dict[str, str]) -> None:
        """Add a record's status and amount to statistics."""
        status = record['status'].strip()
        amount = float(record['amount'].strip())
        self.status_stats[status]['count'] += 1
        self.status_stats[status]['total_amount'] += amount
    
    def _remove_from_stats(self, record: Dict[str, str]) -> None:
        """Remove a record's status and amount from statistics."""
        status = record['status'].strip()
        amount = float(record['amount'].strip())
        self.status_stats[status]['count'] -= 1
        self.status_stats[status]['total_amount'] -= amount
        
        # Clean up empty stats
        if self.status_stats[status]['count'] == 0:
            del self.status_stats[status]
    
    def process_csv(self, input_file: str) -> Tuple[bool, str]:
        """
        Process the input CSV file.
        
        Args:
            input_file: Path to input CSV file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(input_file, 'r', newline='', encoding='utf-8') as f:
                # Detect dialect to handle various CSV formats
                sample = f.read(1024)
                f.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    # Default to Excel dialect if sniffing fails
                    dialect = csv.excel()
                
                reader = csv.DictReader(f, dialect=dialect)
                
                if not reader.fieldnames:
                    return False, "CSV file has no headers"
                
                # Check for required columns
                required_fields = ['customer_id', 'timestamp', 'status', 'amount']
                missing_fields = [f for f in required_fields if f not in reader.fieldnames]
                
                if missing_fields:
                    return False, f"Missing required columns: {', '.join(missing_fields)}"
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header row
                    # Check if row is empty
                    if not any(row.values()):
                        continue
                    
                    # Validate record
                    is_valid, error_msg = self.validate_record(row)
                    if not is_valid:
                        self.errors.append(f"Row {row_num}: {error_msg}")
                        continue
                    
                    self.process_record(row)
            
            return True, ""
            
        except FileNotFoundError:
            return False, f"File not found: {input_file}"
        except PermissionError:
            return False, f"Permission denied: {input_file}"
        except Exception as e:
            return False, f"Error processing file: {str(e)}"
    
    def write_output(self, output_file: str, include_stats: bool = True) -> Tuple[bool, str]:
        """
        Write the processed records and statistics to the output file.
        
        Args:
            output_file: Path to output CSV file
            include_stats: Whether to include statistics at the end
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Sort records by customer_id (deterministic output)
            sorted_customers = sorted(
                self.records.items(),
                key=lambda x: x[0]  # Sort by customer_id
            )
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                # First section: Customer records
                if sorted_customers:
                    fieldnames = ['customer_id', 'timestamp', 'status', 'amount']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for customer_id, record in sorted_customers:
                        writer.writerow({
                            'customer_id': customer_id,
                            'timestamp': record['timestamp'],
                            'status': record['status'],
                            'amount': record['amount']
                        })
                
                # Add a separator and statistics section if requested
                if include_stats and self.status_stats:
                    f.write('\n# Statistics\n')
                    f.write('# Status,Count,Total_Amount\n')
                    
                    # Sort stats by status for deterministic output
                    sorted_stats = sorted(self.status_stats.items())
                    
                    for status, stats in sorted_stats:
                        f.write(f'{status},{stats["count"]},{stats["total_amount"]:.2f}\n')
            
            return True, ""
            
        except PermissionError:
            return False, f"Permission denied: {output_file}"
        except Exception as e:
            return False, f"Error writing output: {str(e)}"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary statistics."""
        return {
            'total_records_processed': self.processed_count,
            'duplicate_records_removed': self.duplicate_count,
            'unique_customers': len(self.records),
            'status_stats': dict(self.status_stats),
            'errors': self.errors[:10]  # First 10 errors
        }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Process customer event CSV files with deduplication and statistics.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python customer_event_processor.py input.csv output.csv
    python customer_event_processor.py input.csv output.csv --no-stats
    python customer_event_processor.py input.csv output.csv --verbose
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to input CSV file'
    )
    
    parser.add_argument(
        'output_file',
        help='Path to output CSV file'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Do not include statistics in output file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Display detailed processing information'
    )
    
    args = parser.parse_args()
    
    # Create processor and process the file
    processor = CustomerEventProcessor()
    
    if args.verbose:
        print(f"Processing: {args.input_file}")
        print("=" * 50)
    
    success, error_msg = processor.process_csv(args.input_file)
    
    if not success:
        print(f"❌ Error: {error_msg}")
        sys.exit(1)
    
    if args.verbose:
        print(f"✓ Processed {processor.processed_count} records")
        print(f"✓ Found {processor.duplicate_count} duplicates")
        print(f"✓ Found {len(processor.records)} unique customers")
    
    # Write output
    success, error_msg = processor.write_output(args.output_file, not args.no_stats)
    
    if not success:
        print(f"❌ Error: {error_msg}")
        sys.exit(1)
    
    # Show summary
    if args.verbose:
        summary = processor.get_summary()
        print("\n📊 Processing Summary:")
        print(f"  Total records: {summary['total_records_processed']}")
        print(f"  Unique customers: {summary['unique_customers']}")
        print(f"  Duplicates removed: {summary['duplicate_records_removed']}")
        
        if summary['status_stats']:
            print("\n📈 Status Statistics:")
            for status, stats in sorted(summary['status_stats'].items()):
                print(f"  {status}: {stats['count']} records, ${stats['total_amount']:.2f}")
        
        if summary['errors']:
            print(f"\n⚠️  Errors ({len(summary['errors'])} total):")
            for error in summary['errors'][:5]:  # Show first 5 errors
                print(f"  {error}")
    
    print(f"\n✅ Output written to: {args.output_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()