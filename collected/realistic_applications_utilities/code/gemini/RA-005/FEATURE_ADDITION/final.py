def summarize_logs(logs, repeated_error_threshold=2):
    """
    Complete robust log summarizer with repeated-error detection.

    Valid format:
        LEVEL: message

    Supported levels:
        INFO, WARNING, ERROR

    Malformed entries are ignored.
    Repeated ERROR messages are detected when their count
    is greater than or equal to repeated_error_threshold.
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "repeated_errors": {}
    }

    # Validate threshold.
    if isinstance(repeated_error_threshold, bool):
        repeated_error_threshold = 2
    elif not isinstance(repeated_error_threshold, (int, float)):
        repeated_error_threshold = 2

    if repeated_error_threshold < 1:
        repeated_error_threshold = 1

    if not isinstance(logs, (list, tuple)):
        return summary

    error_counts = {}

    for raw_line in logs:
        # Ignore non-string records.
        if not isinstance(raw_line, str):
            continue

        line = raw_line.strip()

        # Ignore empty or whitespace-only lines.
        if not line:
            continue

        # A valid record requires a colon.
        if ":" not in line:
            continue

        # Split only at the first colon so messages may contain colons.
        level_text, message = line.split(":", 1)

        level = level_text.strip().upper()
        message = message.strip()

        # Reject missing fields.
        if not level or not message:
            continue

        # Reject levels containing whitespace.
        if any(char.isspace() for char in level):
            continue

        # Reject unsupported levels.
        if level not in {"INFO", "WARNING", "ERROR"}:
            continue

        summary[level] += 1

        if level == "ERROR":
            # Normalize case and whitespace for repeated-error detection.
            normalized_message = " ".join(message.split()).casefold()

            error_counts[normalized_message] = (
                error_counts.get(normalized_message, 0) + 1
            )

    # Inclusive threshold: exactly the threshold count qualifies.
    summary["repeated_errors"] = {
        message: count
        for message, count in error_counts.items()
        if count >= repeated_error_threshold
    }

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        "ERROR: Database connection failed",
        "error: database connection failed",
        " ERROR : Database   connection failed ",
        "WARNING: High memory usage",
        "ERROR: Request failed: timeout",
        "INFO: User logged in",

        # Malformed lines
        "",
        "   ",
        "INFO",
        "ERROR",
        ": Missing level",
        "ERROR:",
        "DEBUG: Unknown level",
        "INFO Server started",
        None,
        123
    ]

    result = summarize_logs(
        logs,
        repeated_error_threshold=3
    )

    print(result)