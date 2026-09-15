#!/usr/bin/env python3
"""
Customer Event CSV Processor

Removes duplicates, keeps latest records, calculates statistics, outputs sorted results.
Usage: python processor.py input.csv output.csv
"""

import csv
import sys
from datetime import datetime
from collections import defaultdict


class CustomerEventProcessor:
    def __init__(self):
        self.records = {}
        self.stats = defaultdict(lambda: {'count': 0, 'amount': 0.0})
        self.duplicates = 0
        self.processed = 0
    
    def parse_timestamp(self, ts):
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
        ]
        ts = ts.strip()
        for fmt in formats:
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return None
    
    def process_file(self, input_file):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required = ['customer_id', 'timestamp', 'status', 'amount']
                if not all(col in reader.fieldnames for col in required):
                    return False, f"Missing required columns: {required}"
                
                for row in reader:
                    self.processed += 1
                    if not all(row.get(col, '').strip() for col in required):
                        continue
                    try:
                        float(row['amount'].strip())
                    except:
                        continue
                    ts = self.parse_timestamp(row['timestamp'])
                    if not ts:
                        continue
                    
                    cid = row['customer_id'].strip()
                    if cid in self.records:
                        existing = self.records[cid]
                        existing_ts = self.parse_timestamp(existing['timestamp'])
                        if ts > existing_ts:
                            self._remove_stats(existing)
                            self.records[cid] = row
                            self._add_stats(row)
                        elif ts == existing_ts:
                            self._remove_stats(existing)
                            self.records[cid] = row
                            self._add_stats(row)
                            self.duplicates += 1
                    else:
                        self.records[cid] = row
                        self._add_stats(row)
            return True, ""
        except FileNotFoundError:
            return False, f"File not found: {input_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _add_stats(self, record):
        status = record['status'].strip()
        amount = float(record['amount'].strip())
        self.stats[status]['count'] += 1
        self.stats[status]['amount'] += amount
    
    def _remove_stats(self, record):
        status = record['status'].strip()
        amount = float(record['amount'].strip())
        self.stats[status]['count'] -= 1
        self.stats[status]['amount'] -= amount
        if self.stats[status]['count'] == 0:
            del self.stats[status]
    
    def write_output(self, output_file):
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['customer_id', 'timestamp', 'status', 'amount'])
                writer.writeheader()
                for cid in sorted(self.records.keys()):
                    writer.writerow(self.records[cid])
                
                if self.stats:
                    f.write('\n# Statistics\n')
                    f.write('# Status,Count,Total_Amount\n')
                    for status in sorted(self.stats.keys()):
                        stats = self.stats[status]
                        f.write(f'{status},{stats["count"]},{stats["amount"]:.2f}\n')
            return True, ""
        except Exception as e:
            return False, f"Error writing output: {str(e)}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python processor.py input.csv output.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    processor = CustomerEventProcessor()
    success, error = processor.process_file(input_file)
    if not success:
        print(f"Error: {error}")
        sys.exit(1)
    
    success, error = processor.write_output(output_file)
    if not success:
        print(f"Error: {error}")
        sys.exit(1)
    
    print(f"Processed: {processor.processed} records")
    print(f"Duplicates removed: {processor.duplicates}")
    print(f"Unique customers: {len(processor.records)}")
    print(f"Output written: {output_file}")


if __name__ == "__main__":
    main()