def summarize_logs(lines):
    """
    Summarize log entries and detect repeated errors.

    Expected format:
        LEVEL: message

    Valid levels:
        INFO, WARNING, ERROR

    Repeated errors are errors with the same normalized message
    appearing more than once.
    """
    summary = {
        "info": 0,
        "warning": 0,
        "error": 0,
        "errors": [],
        "repeated_errors": []
    }

    if not isinstance(lines, list):
        return summary

    error_counts = {}

    for line in lines:
        # Ignore non-string and empty lines
        if not isinstance(line, str) or not line.strip():
            continue

        # Split only on the first colon
        parts = line.split(":", 1)

        # Ignore malformed lines
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

            # Normalize message for repeated-error detection
            normalized_message = " ".join(message.lower().split())
            error_counts[normalized_message] = (
                error_counts.get(normalized_message, 0) + 1
            )

    # Include only errors that occurred more than once
    summary["repeated_errors"] = [
        message
        for message, count in error_counts.items()
        if count > 1
    ]

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        "ERROR: Database connection failed",
        "WARNING: Low disk space",
        "ERROR: Database connection failed",
        "ERROR:  Database   Connection Failed  ",
        "INFO: User logged in",
        "MALFORMED LINE",
        "",
        "ERROR:",
        ": Missing level"
    ]

    result = summarize_logs(logs)
    print(result)