import re
from collections import Counter
from typing import Dict, Optional, Tuple, List
import os


def analyze_error_log(path: str, top_n: Optional[int] = None) -> Dict[str, int]:
    """
    Analyze a server log file and count ERROR-level entries per normalized message.
    Skips blank and malformed lines instead of raising.
    
    Args:
        path: Path to the log file
        top_n: If provided, return only the top-N error signatures sorted by
               count descending. If None or <= 0, return all signatures.
        
    Returns:
        Dictionary mapping normalized error messages to their counts,
        sorted by count descending (always sorted; sliced to top_n if given).
        
    Raises:
        FileNotFoundError: If the log file doesn't exist
        PermissionError: If the file can't be read
        ValueError: If top_n is not a positive integer or None
    """
    _validate_top_n(top_n)
    
    error_pattern = re.compile(
        r'\[?[\d\-:\s]+\]?\s*'
        r'ERROR[:\s]+'
        r'(.+?)$',
        re.IGNORECASE | re.MULTILINE
    )
    
    normalization_patterns = _get_default_patterns()
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            error_counts = _process_file(file, error_pattern, normalization_patterns)
    except PermissionError:
        raise PermissionError(f"Cannot read log file: {path}")
    except UnicodeDecodeError:
        with open(path, 'r', encoding='latin-1', errors='replace') as file:
            error_counts = _process_file(file, error_pattern, normalization_patterns)
    
    return _sorted_counts(error_counts, top_n)


def analyze_error_log_with_stats(path: str, top_n: Optional[int] = None) -> Dict[str, object]:
    """
    Analyze a server log file with detailed statistics about skipped/malformed lines.
    
    Args:
        path: Path to the log file
        top_n: If provided, return only the top-N error signatures sorted by
               count descending. If None or <= 0, return all signatures.
        
    Returns:
        Dictionary with keys:
            - 'errors': Dict[str, int] mapping normalized messages to counts
                        (sorted desc, limited to top_n if provided)
            - 'stats': Dict with total_lines, blank_lines, malformed_lines, 
                       error_lines, parsed_errors, skipped_lines, unique_signatures
            - 'malformed_samples': List of (line_number, raw_line) for first N malformed lines
    """
    _validate_top_n(top_n)
    
    error_pattern = re.compile(
        r'\[?[\d\-:\s]+\]?\s*'
        r'ERROR[:\s]+'
        r'(.+?)$',
        re.IGNORECASE | re.MULTILINE
    )
    
    normalization_patterns = _get_default_patterns()
    
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
    
    # Record total unique signatures BEFORE slicing (useful stat)
    stats['unique_signatures'] = len(error_counts)
    
    return {
        'errors': _sorted_counts(error_counts, top_n),
        'stats': stats,
        'malformed_samples': malformed_samples,
    }


def _validate_top_n(top_n: Optional[int]) -> None:
    """Validate the top_n parameter."""
    if top_n is None:
        return
    if not isinstance(top_n, int) or isinstance(top_n, bool):
        raise ValueError(f"top_n must be an int or None, got {type(top_n).__name__}")
    if top_n < 1:
        raise ValueError(f"top_n must be >= 1 (or None for all), got {top_n}")


def _sorted_counts(counter: Counter, top_n: Optional[int]) -> Dict[str, int]:
    """
    Return a dict sorted by count descending. Ties are broken alphabetically
    for deterministic output. Sliced to top_n entries when provided.
    """
    # Sort by (-count, signature) for stable, deterministic ordering
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    
    if top_n is not None:
        sorted_items = sorted_items[:top_n]
    
    return dict(sorted_items)


def _process_file(file, error_pattern, normalization_patterns) -> Counter:
    """Process file lines, skipping blanks and malformed lines silently."""
    error_counts = Counter()
    
    for line in file:
        try:
            stripped = line.strip()
            if not stripped:
                continue
            
            match = error_pattern.search(stripped)
            if not match:
                continue
            
            message = match.group(1).strip()
            if not message:
                continue
            
            normalized = normalize_message(message, normalization_patterns)
            if normalized:
                error_counts[normalized] += 1
                
        except (AttributeError, IndexError, TypeError, re.error):
            continue
        except Exception:
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
            if not isinstance(line, str):
                _record_malformed(line_num, line, malformed_samples, max_samples)
                stats['malformed_lines'] += 1
                stats['skipped_lines'] += 1
                continue
            
            stripped = line.strip()
            
            if not stripped:
                stats['blank_lines'] += 1
                continue
            
            if len(stripped) < 5:
                _record_malformed(line_num, line, malformed_samples, max_samples)
                stats['malformed_lines'] += 1
                stats['skipped_lines'] += 1
                continue
            
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
            
        except re.error:
            _record_malformed(line_num, line, malformed_samples, max_samples)
            stats['malformed_lines'] += 1
            stats['skipped_lines'] += 1
        except (AttributeError, IndexError, TypeError, ValueError):
            _record_malformed(line_num, line, malformed_samples, max_samples)
            stats['malformed_lines'] += 1
            stats['skipped_lines'] += 1
        except Exception:
            _record_malformed(line_num, line, malformed_samples, max_samples)
            stats['malformed_lines'] += 1
            stats['skipped_lines'] += 1
    
    return error_counts, stats, malformed_samples


def _record_malformed(line_num: int, line, samples: list, max_samples: int) -> None:
    """Record a malformed line sample if we haven't hit the cap."""
    if len(samples) < max_samples:
        try:
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
    """Normalize an error message. Returns empty string on failure."""
    if not isinstance(message, str):
        return ''
    
    try:
        normalized = message
        for pattern, replacement in patterns:
            try:
                normalized = pattern.sub(replacement, normalized)
            except (re.error, TypeError):
                continue
        
        normalized = ' '.join(normalized.split())
        return normalized
    except Exception:
        return ''


# ============ Example usage ============
if __name__ == "__main__":
    sample_log = (
        "[2024-01-15 10:23:45] INFO: Server started on port 8080\n"
        "[2024-01-15 10:23:46] ERROR: Database connection failed for user 'john' at 192.168.1.1:5432\n"
        "\n"
        "   \t   \n"
        "[2024-01-15 10:23:47] WARNING: High memory\n"
        "\x00\x01\x02corrupted binary junk\xff\xfe\n"
        "ERR\n"
        "[2024-01-15 10:23:48] ERROR: Database connection failed for user 'jane' at 192.168.1.2:5432\n"
        "random noise that is not a log entry at all\n"
        "[2024-01-15 10:23:49] ERROR: File not found: /var/log/app.log\n"
        "[malformed timestamp ERROR:\n"
        "[2024-01-15 10:23:51] ERROR: Database connection failed for user 'bob' at 10.0.0.1:3306\n"
        "[2024-01-15 10:23:52] ERROR: File not found: /etc/config/settings.json\n"
        "[2024-01-15 10:23:53] ERROR: Authentication failed for user ID: abc123def456\n"
        "[2024-01-15 10:23:54] ERROR: Authentication failed for user ID: xyz789uvw012\n"
    )
    
    test_path = '/tmp/sample_topn.log'
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(sample_log)
    
    print("=== Top 2 errors ===")
    for msg, count in analyze_error_log(test_path, top_n=2).items():
        print(f"  {count:3d} x {msg}")
    
    print("\n=== All errors (top_n=None) ===")
    for msg, count in analyze_error_log(test_path).items():
        print(f"  {count:3d} x {msg}")
    
    print("\n=== Top 2 with stats ===")
    result = analyze_error_log_with_stats(test_path, top_n=2)
    print("Errors (top 2 of {} total unique):".format(
        result['stats']['unique_signatures']))
    for msg, count in result['errors'].items():
        print(f"  {count:3d} x {msg}")
    print(f"Stats: {result['stats']}")
    
    # Error cases
    print("\n=== Validation ===")
    for bad_value in [0, -1, "3", 1.5, True]:
        try:
            analyze_error_log(test_path, top_n=bad_value)
            print(f"  top_n={bad_value!r}: OK (unexpected)")
        except ValueError as e:
            print(f"  top_n={bad_value!r}: ValueError -> {e}")
    
    os.remove(test_path)