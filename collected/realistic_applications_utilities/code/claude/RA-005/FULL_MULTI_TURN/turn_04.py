def summarize_logs(logs, repeated_error_threshold=2):
    """
    Robust log summarizer with repeated-error detection.

    Handles:
    - Empty or None logs
    - Non-string entries
    - Blank/malformed lines
    - Extra separators in messages
    - Case differences in log levels
    - Whitespace differences
    - Invalid thresholds
    - Exact threshold boundaries
    - Repeated ERROR messages

    Valid format:
        LEVEL: message

    Valid levels:
        INFO, WARNING, ERROR
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "repeated_errors": {}
    }

    # A threshold of 0 or a negative value is treated as 1,
    # because every valid error then qualifies as repeated.
    if not isinstance(repeated_error_threshold, (int, float)):
        repeated_error_threshold = 2

    if repeated_error_threshold < 1:
        repeated_error_threshold = 1

    if not logs:
        return summary

    error_messages = {}

    for line in logs:
        # Ignore non-string records.
        if not isinstance(line, str):
            continue

        line = line.strip()

        # Ignore empty/whitespace-only lines.
        if not line:
            continue

        # Split only on the first colon.
        # This allows messages such as:
        # ERROR: Connection failed: timeout
        parts = line.split(":", 1)

        # A valid log must contain exactly the required first separator.
        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()
        message = parts[1].strip()

        # Reject missing levels or messages.
        if not level or not message:
            continue

        # Ignore unknown levels.
        if level not in summary or level == "repeated_errors":
            continue

        summary[level] += 1

        if level == "ERROR":
            # Normalize case and repeated whitespace so these count
            # as the same error:
            # "ERROR: Database Failed"
            # "error:   database failed"
            normalized_message = " ".join(message.split()).casefold()

            error_messages[normalized_message] = (
                error_messages.get(normalized_message, 0) + 1
            )

    # Exact boundary is inclusive:
    # count == threshold qualifies as a repeated error.
    summary["repeated_errors"] = {
        message: count
        for message, count in error_messages.items()
        if count >= repeated_error_threshold
    }

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        " ERROR : Database connection failed ",
        "error: database connection failed",
        "ERROR: Database connection failed",
        "WARNING: High memory usage",
        "INFO: User logged in",
        "ERROR: Request failed: timeout",
        "ERROR",                       # malformed
        ": Missing level",             # malformed
        "ERROR:",                      # missing message
        "ERROR:   ",                   # blank message
        "DEBUG: Debug message",        # unsupported level
        "ERROR Database failed",       # missing separator
        "INFO: Message: with: separators",
        "",                            # empty
        "   ",                         # whitespace only
        None,                          # non-string
        123                            # non-string
    ]

    # Threshold = 3:
    # The database error occurs exactly 3 times, so it qualifies.
    result = summarize_logs(logs, repeated_error_threshold=3)

    print(result)