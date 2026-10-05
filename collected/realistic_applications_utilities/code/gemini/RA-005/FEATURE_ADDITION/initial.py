def summarize_logs(logs, repeated_error_threshold=2):
    """
    Complete log summarizer with robust malformed-line handling.

    Valid log format:
        LEVEL: message

    Supported levels:
        INFO, WARNING, ERROR

    Malformed entries are ignored.
    Repeated ERROR messages are detected using an inclusive threshold.
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "repeated_errors": {}
    }

    # Safely handle invalid thresholds.
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
        # Only strings can be valid log entries.
        if not isinstance(raw_line, str):
            continue

        line = raw_line.strip()

        # Ignore empty or whitespace-only lines.
        if not line:
            continue

        # A valid line must contain a separator.
        if ":" not in line:
            continue

        level_text, message = line.split(":", 1)

        level = level_text.strip().upper()
        message = message.strip()

        # Reject missing level or message.
        if not level or not message:
            continue

        # Reject levels containing internal whitespace.
        if any(char.isspace() for char in level):
            continue

        # Only these levels are valid.
        if level not in {"INFO", "WARNING", "ERROR"}:
            continue

        summary[level] += 1

        if level == "ERROR":
            # Normalize message case and whitespace so:
            # "Database Failed"
            # " database   failed "
            # "DATABASE FAILED"
            # are treated as the same error.
            normalized_message = " ".join(message.split()).casefold()

            error_counts[normalized_message] = (
                error_counts.get(normalized_message, 0) + 1
            )

    # Threshold boundary is inclusive.
    summary["repeated_errors"] = {
        message: count
        for message, count in error_counts.items()
        if count >= repeated_error_threshold
    }

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        " error : Database connection failed ",
        "ERROR: database   connection failed",
        "ERROR: Database connection failed",
        "WARNING: High memory usage",
        "ERROR: Request failed: timeout",

        # Malformed entries
        "",
        "   ",
        "INFO",
        "ERROR",
        ": Missing level",
        "ERROR:",
        "ERROR:   ",
        "DEBUG: Unknown level",
        "INFO Server started",
        "INFO:: malformed message",
        None,
        123
    ]

    result = summarize_logs(
        logs,
        repeated_error_threshold=3
    )

    print(result)