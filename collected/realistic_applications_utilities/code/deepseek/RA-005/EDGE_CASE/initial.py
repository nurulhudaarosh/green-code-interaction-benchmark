def process_logs(logs, separator="|", threshold=5, case_sensitive=False):
    """
    Process logs with handling for empty logs, extra separators, 
    case differences, and exact threshold matching.
    
    Args:
        logs: List of log strings (or a single string)
        separator: Character used to split log entries
        threshold: Exact count threshold for filtering
        case_sensitive: Whether comparison should be case-sensitive
    
    Returns:
        Dictionary of {normalized_key: count} where count == threshold
    """
    # Handle empty logs input
    if not logs:
        return {}
    
    # Normalize input to a list
    if isinstance(logs, str):
        logs = [logs]
    
    counts = {}
    
    for log in logs:
        # Skip None or empty/whitespace-only logs
        if log is None or not str(log).strip():
            continue
        
        log = str(log)
        
        # Split by separator
        parts = log.split(separator)
        
        # Remove empty parts caused by extra separators (leading/trailing/double)
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            continue
        
        # Use first non-empty part as the key (adjust as needed)
        key = separator.join(parts)
        
        # Normalize case if not case-sensitive
        if not case_sensitive:
            key = key.lower()
        
        counts[key] = counts.get(key, 0) + 1
    
    # Return only entries matching the exact threshold
    return {k: v for k, v in counts.items() if v == threshold}


# ---------- Demo / Test ----------
if __name__ == "__main__":
    sample_logs = [
        "",                       # empty log
        "   ",                    # whitespace only
        None,                     # None
        "ERROR|login failed",     # normal
        "ERROR|login failed||",   # extra trailing separators
        "||ERROR|login failed",   # extra leading separators
        "error|login failed",     # case difference
        "ERROR|||login failed",   # extra separators inside
        "ERROR|login failed",     # duplicate -> exact threshold
        "ERROR|login failed",     # duplicate -> exact threshold
        "INFO|page loaded",       # only 1 occurrence (below threshold)
    ]
    
    result = process_logs(sample_logs, separator="|", threshold=5, case_sensitive=False)
    print("Exact threshold matches:", result)
    # Expected: {'error|login failed': 5}