def summarize_logs(logs, repeated_error_threshold=2):
    """
    Complete robust log summarizer.

    Handles:
    - Empty logs
    - Malformed lines
    - Extra ':' separators inside messages
    - Case differences in levels/messages
    - Extra whitespace
    - Exact repetition-threshold boundaries
    """

    result = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "repeated_errors": {}
    }

    # Safe threshold handling.
    if isinstance(repeated_error_threshold, bool):
        repeated_error_threshold = 2
    elif not isinstance(repeated_error_threshold, (int, float)):
        repeated_error_threshold = 2

    if repeated_error_threshold < 1:
        repeated_error_threshold = 1

    # Empty or invalid logs.
    if logs is None:
        return result

    if not isinstance(logs, (list, tuple)):
        return result

    if len(logs) == 0:
        return result

    error_counts = {}

    for raw_line in logs:
        if not isinstance(raw_line, str):
            continue

        line = raw_line.strip()

        if not line:
            continue

        # Split ONLY on the first colon.
        # Therefore extra separators belong to the message.
        if ":" not in line:
            continue

        level_text, message = line.split(":", 1)

        level = level_text.strip().upper()
        message = message.strip()

        # Both fields must exist.
        if not level or not message:
            continue

        # Only supported levels are valid.
        if level not in {"INFO", "WARNING", "ERROR"}:
            continue

        result[level] += 1

        if level == "ERROR":
            # Normalize case and repeated whitespace so:
            # "Database Failed"
            # "database failed"
            # " DATABASE   FAILED "
            # are treated as the same error.
            normalized_message = " ".join(message.split()).casefold()

            error_counts[normalized_message] = (
                error_counts.get(normalized_message, 0) + 1
            )

    # Inclusive threshold:
    # count == threshold is considered repeated.
    result["repeated_errors"] = {
        message: count
        for message, count in error_counts.items()
        if count >= repeated_error_threshold
    }

    return result


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        "info: User logged in",
        "WARNING: High memory usage",
        "warning: Disk almost full",

        # Same error despite case/whitespace differences.
        "ERROR: Database connection failed",
        "error: database connection failed",
        " ERROR : DATABASE   CONNECTION FAILED ",

        # Extra separators inside the message.
        "ERROR: Request failed: timeout",
        "ERROR: Request failed: timeout",

        "INFO: Server: started: successfully",

        # Malformed records.
        "",
        "   ",
        "INFO",
        "ERROR:",
        ": Missing level",
        "DEBUG: Unknown level",
        None,
        123
    ]

    # Database error appears exactly 3 times.
    # Request timeout appears exactly 2 times.
    # With threshold=3, only the database error is repeated.
    print(summarize_logs(logs, repeated_error_threshold=3))

    # Empty logs return zero counts without errors.
    print(summarize_logs([]))

    # Exact threshold example.
    exact_threshold_logs = [
        "ERROR: Connection failed",
        "ERROR: connection failed"
    ]
    print(summarize_logs(exact_threshold_logs, repeated_error_threshold=2))