def summarize_logs(lines):
    """
    Summarize log entries while safely handling malformed lines.

    Expected format:
        LEVEL: message

    Valid levels:
        INFO, WARNING, ERROR

    Returns:
        {
            "info": int,
            "warning": int,
            "error": int,
            "errors": list[str]
        }
    """
    summary = {
        "info": 0,
        "warning": 0,
        "error": 0,
        "errors": []
    }

    if not isinstance(lines, list):
        return summary

    for line in lines:
        # Ignore non-string and empty/whitespace-only lines
        if not isinstance(line, str) or not line.strip():
            continue

        # Split only once so colons inside the message are preserved
        parts = line.split(":", 1)

        # Malformed line: missing separator or empty level/message
        if len(parts) != 2:
            continue

        level = parts[0].strip().lower()
        message = parts[1].strip()

        if not level or not message:
            continue

        if level == "info":
            summary["info"] += 1
        elif level == "warning":
            summary["warning"] += 1
        elif level == "error":
            summary["error"] += 1
            summary["errors"].append(message)

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        "ERROR: Database connection failed",
        "WARNING: Low disk space",
        "ERROR: Timeout: request took too long",
        "MALFORMED LINE",
        "",
        "   ",
        ": Missing level",
        "ERROR:",
        "  INFO  : User logged in  "
    ]

    result = summarize_logs(logs)
    print(result)