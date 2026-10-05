import csv
import re
from typing import List, Dict, Optional
from datetime import datetime

def parse_access_log_to_csv(log_lines: List[str], output_file: str) -> None:
    """
    Parse access log lines and write them to a CSV file with status class.
    
    Args:
        log_lines: List of access log lines (Common Log Format or Combined Log Format)
        output_file: Path to the output CSV file
    """
    
    # Regex pattern for Common/Combined Log Format
    # Matches: IP - user [timestamp] "method path protocol" status size "referer" "user-agent"
    log_pattern = re.compile(
        r'^(?P<ip>\S+) '           # IP address
        r'\S+ '                     # ident (usually -)
        r'(?P<user>\S+) '          # user (usually -)
        r'\[(?P<timestamp>[^\]]+)\] '  # timestamp
        r'"(?P<method>\S+) '       # HTTP method
        r'(?P<path>\S+) '          # request path
        r'(?P<protocol>[^"]+)" '   # protocol
        r'(?P<status>\d{3}) '      # status code
        r'(?P<size>\S+)'           # response size
        r'(?:\s+"(?P<referer>[^"]*)" '  # referer (optional)
        r'"(?P<user_agent>[^"]*)")?'    # user-agent (optional)
    )
    
    def get_status_class(status_code: int) -> str:
        """Determine status class from status code."""
        if 100 <= status_code < 200:
            return '1xx'
        elif 200 <= status_code < 300:
            return '2xx'
        elif 300 <= status_code < 400:
            return '3xx'
        elif 400 <= status_code < 500:
            return '4xx'
        elif 500 <= status_code < 600:
            return '5xx'
        else:
            return 'unknown'
    
    def parse_timestamp(timestamp_str: str) -> Optional[str]:
        """Parse timestamp and convert to ISO format."""
        try:
            # Common Log Format: 10/Oct/2000:13:55:36 -0700
            dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            return dt.isoformat()
        except ValueError:
            return timestamp_str  # Return original if parsing fails
    
    parsed_entries = []
    
    for line in log_lines:
        line = line.strip()
        if not line:
            continue
            
        match = log_pattern.match(line)
        if not match:
            # Handle malformed lines - you could log these separately
            print(f"Warning: Could not parse line: {line[:100]}...")
            continue
        
        data = match.groupdict()
        
        # Parse status code and determine class
        try:
            status_code = int(data['status'])
            status_class = get_status_class(status_code)
        except (ValueError, TypeError):
            status_code = 0
            status_class = 'unknown'
        
        # Parse size (convert '-' to 0)
        try:
            size = int(data['size']) if data['size'] != '-' else 0
        except ValueError:
            size = 0
        
        # Build the parsed entry
        entry = {
            'ip': data['ip'],
            'user': data['user'],
            'timestamp': parse_timestamp(data['timestamp']),
            'method': data['method'],
            'path': data['path'],
            'protocol': data['protocol'].strip(),
            'status_code': status_code,
            'status_class': status_class,
            'size': size,
            'referer': data.get('referer', ''),
            'user_agent': data.get('user_agent', '')
        }
        
        parsed_entries.append(entry)
    
    # Write to CSV
    if parsed_entries:
        fieldnames = [
            'ip', 'user', 'timestamp', 'method', 'path', 'protocol',
            'status_code', 'status_class', 'size', 'referer', 'user_agent'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(parsed_entries)
        
        print(f"Successfully wrote {len(parsed_entries)} entries to {output_file}")
    else:
        print("No valid log entries found to write")


# Example usage and helper functions
def parse_log_file_to_csv(input_file: str, output_file: str) -> None:
    """Parse an access log file and write to CSV."""
    with open(input_file, 'r', encoding='utf-8') as f:
        log_lines = f.readlines()
    
    parse_access_log_to_csv(log_lines, output_file)


def get_status_class_summary(csv_file: str) -> Dict[str, int]:
    """Get a summary of status classes from the CSV file."""
    summary = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status_class = row['status_class']
            summary[status_class] = summary.get(status_class, 0) + 1
    
    return summary


# Example with sample log lines
if __name__ == "__main__":
    sample_logs = [
        '192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326 "-" "Mozilla/5.0"',
        '192.168.1.2 - admin [10/Oct/2000:13:56:36 -0700] "POST /api/login HTTP/1.1" 401 128 "-" "curl/7.64.1"',
        '10.0.0.1 - - [10/Oct/2000:13:57:36 -0700] "GET /missing HTTP/1.1" 404 512 "http://example.com" "Mozilla/5.0"',
        '10.0.0.2 - - [10/Oct/2000:13:58:36 -0700] "GET /error HTTP/1.1" 500 1024 "-" "Mozilla/5.0"',
        'invalid log line that should be skipped',
        '172.16.0.1 - user1 [10/Oct/2000:13:59:36 -0700] "GET /redirect HTTP/1.1" 301 0 "-" "Mozilla/5.0"',
    ]
    
    # Parse and write to CSV
    parse_access_log_to_csv(sample_logs, 'access_log_parsed.csv')
    
    # Show summary
    summary = get_status_class_summary('access_log_parsed.csv')
    print("\nStatus Class Summary:")
    for status_class, count in sorted(summary.items()):
        print(f"  {status_class}: {count}")