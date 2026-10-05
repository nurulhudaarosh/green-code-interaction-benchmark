def summarize_logs(logs, repeated_error_threshold=2):
    """
    Summarize logs and detect repeated errors.

    Expected format:
        LEVEL: message

    Repeated errors are detected when the same ERROR message occurs
    at least repeated_error_threshold times.

    Malformed, empty, and unknown-level lines are ignored.
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "DEBUG": 0,
        "repeated_errors": []
    }

    if not logs:
        return summary

    # Keep the threshold boundary exact.
    if not isinstance(repeated_error_threshold, int):
        repeated_error_threshold = 2

    if repeated_error_threshold < 1:
        repeated_error_threshold = 1

    error_messages = {}

    for log in logs:
        # Ignore non-string and empty/malformed records.
        if not isinstance(log, str):
            continue

        log = log.strip()
        if not log:
            continue

        # A valid line must contain exactly one meaningful separator
        # between the level and message. Split only once so the message
        # itself may contain colons.
        parts = log.split(":", 1)

        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()
        message = parts[1].strip()

        if not level or not message:
            continue

        if level not in {"INFO", "WARNING", "ERROR", "DEBUG"}:
            continue

        summary[level] += 1

        if level == "ERROR":
            error_messages[message] = error_messages.get(message, 0) + 1

    # Include errors occurring exactly at the threshold.
    summary["repeated_errors"] = [
        message
        for message, count in error_messages.items()
        if count >= repeated_error_threshold
    ]

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        "ERROR: Database connection failed",
        "error: Database connection failed",
        "ERROR: Request timeout",
        "WARNING: Low memory",
        "DEBUG: Processing request",
        "ERROR: Request timeout",
        "ERROR Database connection failed",  # malformed
        "ERROR:",                            # missing message
        ": Missing level",                   # missing level
        "",                                  # empty
        "UNKNOWN: Unknown level",            # invalid level
        "ERROR: Message: contains: colons"   # valid message
    ]

    print(summarize_logs(logs, repeated_error_threshold=2))