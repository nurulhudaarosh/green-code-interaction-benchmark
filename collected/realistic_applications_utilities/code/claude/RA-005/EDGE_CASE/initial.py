def summarize_logs(lines, repeat_threshold=2):
    """
    Summarize logs with robust parsing and repeated-error detection.

    Handles:
    - Empty logs
    - Malformed lines
    - Extra separators in messages
    - Case differences in log levels and error messages
    - Exact repeated-error thresholds

    Expected format:
        LEVEL: message
    """

    summary = {
        "info": 0,
        "warning": 0,
        "error": 0,
        "errors": [],
        "repeated_errors": []
    }

    if not isinstance(lines, list) or not lines:
        return summary

    # Threshold must be at least 2 for an error to be considered repeated.
    if not isinstance(repeat_threshold, int) or repeat_threshold < 2:
        repeat_threshold = 2

    error_counts = {}
    error_messages = {}

    for line in lines:
        # Ignore non-string and empty/whitespace-only lines
        if not isinstance(line, str) or not line.strip():
            continue

        # Split only on the first separator.
        # This allows extra ':' characters inside the message.
        parts = line.split(":", 1)

        if len(parts) != 2:
            continue

        level = parts[0].strip().lower()
        message = parts[1].strip()

        # Ignore missing level or message
        if not level or not message:
            continue

        if level == "info":
            summary["info"] += 1

        elif level == "warning":
            summary["warning"] += 1

        elif level == "error":
            summary["error"] += 1
            summary["errors"].append(message)

            # Normalize case and whitespace for comparison.
            normalized_message = " ".join(message.lower().split())

            error_counts[normalized_message] = (
                error_counts.get(normalized_message, 0) + 1
            )

            # Preserve the first valid original message.
            if normalized_message not in error_messages:
                error_messages[normalized_message] = message

    # Include errors whose count reaches the threshold exactly or exceeds it.
    for normalized_message, count in error_counts.items():
        if count >= repeat_threshold:
            summary["repeated_errors"].append(
                error_messages[normalized_message]
            )

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        "ERROR: Database connection failed",
        "error: database connection failed",
        "ERROR: Database connection failed: timeout",
        "WARNING: Low disk space",
        "Info: User logged in",
        "ERROR: Database connection failed",
        "MALFORMED LINE",
        "",
        "   ",
        "ERROR:",
        ": Missing level",
        "WARNING: Extra: separator: in message"
    ]

    # Exactly 3 occurrences are required to detect a repeated error.
    result = summarize_logs(logs, repeat_threshold=3)

    print(result)