def summarize_logs(logs, repeated_error_threshold=2):
    """
    Complete robust log summarizer.

    Handles:
    - Empty logs
    - Malformed lines
    - Extra separators in messages
    - Case differences in levels and error messages
    - Whitespace differences
    - Exact repetition-threshold boundaries
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "repeated_errors": {}
    }

    # Use a safe default for invalid thresholds.
    if isinstance(repeated_error_threshold, bool):
        repeated_error_threshold = 2
    elif not isinstance(repeated_error_threshold, (int, float)):
        repeated_error_threshold = 2

    if repeated_error_threshold < 1:
        repeated_error_threshold = 1

    # Empty, None, or invalid log collections.
    if not logs or not isinstance(logs, (list, tuple)):
        return summary

    error_counts = {}

    for raw_line in logs:
        if not isinstance(raw_line, str):
            continue

        line = raw_line.strip()

        # Ignore empty/whitespace-only lines.
        if not line:
            continue

        # A valid line must contain a separator.
        if ":" not in line:
            continue

        # Split only at the FIRST separator.
        # This allows messages such as:
        # ERROR: Database: connection failed: timeout
        level_text, message = line.split(":", 1)

        level = level_text.strip().upper()
        message = message.strip()

        # Reject missing level or message.
        if not level or not message:
            continue

        # Only supported levels are counted.
        if level not in {"INFO", "WARNING", "ERROR"}:
            continue

        summary[level] += 1

        if level == "ERROR":
            # Normalize case and whitespace so different formatting
            # represents the same error.
            normalized_message = " ".join(message.split()).casefold()

            error_counts[normalized_message] = (
                error_counts.get(normalized_message, 0) + 1
            )

    # Exact threshold is included:
    # count == threshold -> repeated error
    summary["repeated_errors"] = {
        message: count
        for message, count in error_counts.items()
        if count >= repeated_error_threshold
    }

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        "info: User logged in",
        "WARNING: High memory usage",
        "warning: Disk almost full",
        "ERROR: Database connection failed",
        "error: database connection failed",
        " ERROR : Database   connection failed ",
        "ERROR: Request failed: timeout",
        "ERROR: Request failed: timeout",

        # Extra separators are allowed inside the message.
        "INFO: Server: started: successfully",
        "ERROR: API: request: timeout",

        # Malformed/empty records are ignored.
        "",
        "   ",
        "INFO",
        "ERROR:",
        ": Missing level",
        "DEBUG: Unknown level",
        None,
        123
    ]

    # Database error occurs exactly 3 times -> included.
    # Request timeout occurs exactly 2 times -> included.
    result = summarize_logs(logs, repeated_error_threshold=3)

    print(result)