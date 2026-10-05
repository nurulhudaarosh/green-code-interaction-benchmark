import re
from collections import Counter
from typing import Dict, Optional, Tuple
import os
import logging


def analyze_error_log(path: str) -> Dict[str, int]:
    """
    Analyze a server log file and count ERROR-level entries per normalized message.
    Skips blank and malformed lines instead of raising.
    
    Args:
        path: Path to the log file
        
    Returns:
        Dictionary mapping normalized error messages to their counts
        
    Raises:
        FileNotFoundError: If the log file doesn't exist
        PermissionError: If the file can't be read
    """
    
    error_pattern = re.compile(
        r'\[?[\d\-:\s]+\]?\s*'
        r'ERROR[:\s]+'
        r'(.+?)$',
        re.IGNORECASE | re.MULTILINE
    )
    
    normalization_patterns = _get_default_patterns()
    error_counts = Counter()
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            error_counts = _process_file(file, error_pattern, normalization_patterns)
    except PermissionError:
        raise PermissionError(f"Cannot read log file: {path}")
    except UnicodeDecodeError:
        # Fallback to latin-1
        with open(path, 'r', encoding='latin-1', errors='replace') as file:
            error_counts = _process_file(file, error_pattern, normalization_patterns)
    
    return dict(error_counts)


def analyze_error_log_with_stats(path: str) -> Dict[str, object]:
    """
    Analyze a server log file with detailed statistics about skipped/malformed lines.
    
    Args:
        path: Path to the log file
        
    Returns:
        Dictionary with keys:
            - 'errors': Dict[str, int] mapping normalized messages to counts
            - 'stats': Dict with total_lines, blank_lines, malformed_lines, 
                       error_lines, parsed_errors, skipped_lines
            - 'malformed_samples': List of (line_number, raw_line) for first N malformed lines
    """
    
    error_pattern = re.compile(
        r'\[?[\d\-:\s]+\]?\s*'
        r'ERROR[:\s]+'
        r'(.+?)$',
        re.IGNORECASE | re.MULTILINE
    )
    
    normalization_patterns = _get_default_patterns()
    error_counts = Counter()
    
    stats = {
        'total_lines': 0,
        'blank_lines': 0,
        'malformed_lines': 0,
        'error_lines': 0,
        'parsed_errors': 0,
        'skipped_lines': 0,
    }
    malformed_samples = []
    MAX_SAMPLES = 10
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            error_counts, stats, malformed_samples = _process_file_with_stats(
                file, error_pattern, normalization_patterns, MAX_SAMPLES
            )
    except PermissionError:
        raise PermissionError(f"Cannot read log file: {path}")
    except UnicodeDecodeError:
        with open(path, 'r', encoding='latin-1', errors='replace') as file:
            error_counts, stats, malformed_samples = _process_file_with_stats(
                file, error_pattern, normalization_patterns, MAX_SAMPLES
            )
    
    return {
        'errors': dict(error_counts),
        'stats': stats,
        'malformed_samples': malformed_samples,
    }


def _process_file(file, error_pattern, normalization_patterns) -> Counter:
    """Process file lines, skipping blanks and malformed lines silently."""
    error_counts = Counter()
    
    for line in file:
        try:
            # Skip blank lines
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check for ERROR entry
            match = error_pattern.search(stripped)
            if not match:
                continue
            
            message = match.group(1).strip()
            if not message:
                continue
            
            normalized = normalize_message(message, normalization_patterns)
            if normalized:
                error_counts[normalized] += 1
                
        except (AttributeError, IndexError, TypeError, re.error) as e:
            # Malformed line - skip silently in basic version
            continue
        except Exception as e:
            # Catch-all for any unexpected parsing errors
            continue
    
    return error_counts


def _process_file_with_stats(file, error_pattern, normalization_patterns, 
                              max_samples: int) -> Tuple[Counter, Dict, list]:
    """Process file lines with detailed statistics tracking."""
    error_counts = Counter()
    malformed_samples = []
    stats = {
        'total_lines': 0,
        'blank_lines': 0,
        'malformed_lines': 0,
        'error_lines': 0,
        'parsed_errors': 0,
        'skipped_lines': 0,
    }
    
    for line_num, line in enumerate(file, 1):
        stats['total_lines'] += 1
        
        try:
            # Handle non-string input defensively
            if not isinstance(line, str):
                _record_malformed(line_num, line, malformed_samples, max_samples)
                stats['malformed_lines'] += 1
                stats['skipped_lines'] += 1
                continue
            
            stripped = line.strip()
            
            # Skip blank lines (whitespace-only)
            if not stripped:
                stats['blank_lines'] += 1
                continue
            
            # Skip lines that are too short to be meaningful
            if len(stripped) < 5:
                _record_malformed(line_num, line, malformed_samples, max_samples)
                stats['malformed_lines'] += 1
                stats['skipped_lines'] += 1
                continue
            
            # Check for ERROR entry
            match = error_pattern.search(stripped)
            if not match:
                continue
            
            stats['error_lines'] += 1
            message = match.group(1).strip()
            
            if not message:
                _record_malformed(line_num, line, malformed_samples, max_samples)
                stats['malformed_lines'] += 1
                stats['skipped_lines'] += 1
                continue
            
            normalized = normalize_message(message, normalization_patterns)
            
            if not normalized:
                _record_malformed(line_num, line, malformed_samples, max_samples)
                stats['malformed_lines'] += 1
                stats['skipped_lines'] += 1
                continue
            
            error_counts[normalized] += 1
            stats['parsed_errors'] += 1
            
        except re.error as e:
            # Regex error on this line
            _record_malformed(line_num, line, malformed_samples, max_samples)
            stats['malformed_lines'] += 1
            stats['skipped_lines'] += 1
        except (AttributeError, IndexError, TypeError, ValueError) as e:
            # Parsing/extraction error
            _record_malformed(line_num, line, malformed_samples, max_samples)
            stats['malformed_lines'] += 1
            stats['skipped_lines'] += 1
        except Exception as e:
            # Unexpected error - still don't crash the whole run
            _record_malformed(line_num, line, malformed_samples, max_samples)
            stats['malformed_lines'] += 1
            stats['skipped_lines'] += 1
    
    return error_counts, stats, malformed_samples


def _record_malformed(line_num: int, line, samples: list, max_samples: int) -> None:
    """Record a malformed line sample if we haven't hit the cap."""
    if len(samples) < max_samples:
        try:
            # Truncate very long lines for readability
            raw = repr(line)
            if len(raw) > 200:
                raw = raw[:200] + '...'
            samples.append((line_num, raw))
        except Exception:
            samples.append((line_num, '<unreprable>'))


def _get_default_patterns() -> list:
    """Return the default normalization patterns."""
    return [
        (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '<IP>'),
        (re.compile(r':\d{2,5}\b'), ':<PORT>'),
        (re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I), '<UUID>'),
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '<EMAIL>'),
        (re.compile(r'(?:[A-Za-z]:)?[/\\](?:[^/\\\s]+[/\\])*[^/\\\s]+'), '<PATH>'),
        (re.compile(r'\b\d+\b'), '<NUM>'),
        (re.compile(r"'[^']*'"), "'<STR>'"),
        (re.compile(r'"[^"]*"'), '"<STR>"'),
        (re.compile(r'\b0x[0-9a-fA-F]+\b'), '<HEX>'),
        (re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?'), '<TIMESTAMP>'),
        (re.compile(r'\b[A-Za-z0-9]{8,}\b'), '<ID>'),
    ]


def normalize_message(message: str, patterns: list) -> str:
    """
    Normalize an error message by replacing variable data with placeholders.
    Returns empty string on failure rather than raising.
    """
    if not isinstance(message, str):
        return ''
    
    try:
        normalized = message
        for pattern, replacement in patterns:
            try:
                normalized = pattern.sub(replacement, normalized)
            except (re.error, TypeError):
                # Skip this particular pattern if it fails
                continue
        
        normalized = ' '.join(normalized.split())
        return normalized
    except Exception:
        return ''


# ============ Example usage ============
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a sample log file with problematic lines
    sample_log = (
        "[2024-01-15 10:23:45] INFO: Server started on port 8080\n"
        "[2024-01-15 10:23:46] ERROR: Database connection failed for user 'john' at 192.168.1.1:5432\n"
        "\n"                                          # blank line
        "   \t   \n"                                  # whitespace-only line
        "[2024-01-15 10:23:47] WARNING: High memory\n"
        "\x00\x01\x02corrupted binary junk\xff\xfe\n" # corrupted line
        "ERR\n"                                       # too short
        "[2024-01-15 10:23:48] ERROR: Database connection failed for user 'jane' at 192.168.1.2:5432\n"
        "random noise that is not a log entry at all\n"
        "[2024-01-15 10:23:49] ERROR: File not found: /var/log/app.log\n"
        "[malformed timestamp ERROR:\n"               # malformed but has ERROR
        "[2024-01-15 10:23:51] ERROR: Database connection failed for user 'bob' at 10.0.0.1:3306\n"
        "[2024-01-15 10:23:52] ERROR: File not found: /etc/config/settings.json\n"
        "[2024-01-15 10:23:53] ERROR: Authentication failed for user ID: abc123def456\n"
        "[2024-01-15 10:23:54] ERROR: Authentication failed for user ID: xyz789uvw012\n"
    )
    
    test_path = '/tmp/sample_corrupted.log'
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(sample_log)
    
    # Basic version — should not crash
    print("=== Basic analysis (skips malformed silently) ===")
    results = analyze_error_log(test_path)
    for message, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count:3d} x {message}")
    
    # Advanced version — with stats
    print("\n=== Analysis with stats ===")
    result = analyze_error_log_with_stats(test_path)
    
    print("\nError counts:")
    for message, count in sorted(result['errors'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {count:3d} x {message}")
    
    print("\nStatistics:")
    for key, value in result['stats'].items():
        print(f"  {key}: {value}")
    
    if result['malformed_samples']:
        print("\nMalformed line samples (line #, content):")
        for line_num, raw in result['malformed_samples']:
            print(f"  Line {line_num}: {raw}")
    
    os.remove(test_path)