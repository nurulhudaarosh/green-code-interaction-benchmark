import json
import sys


def analyze_ndjson(input_stream, output_stream):
    """Parses NDJSON data from input_stream, calculates per-user metrics,

    and writes sorted JSON results to output_stream while ignoring malformed
    lines.
    """
    user_stats = {}
    malformed_lines_count = 0

    for line in input_stream:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            malformed_lines_count += 1
            continue

        # Extract nested structures safely
        user_info = data.get("user")
        req_info = data.get("request")

        if not isinstance(user_info, dict) or not isinstance(req_info, dict):
            malformed_lines_count += 1
            continue

        user_id = user_info.get("id")
        latency = req_info.get("latency")
        status_code = req_info.get("status")
        endpoint = req_info.get("endpoint")

        # Basic schema validation for essential metrics
        if (
            user_id is None
            or not isinstance(latency, (int, float))
            or not isinstance(status_code, int)
            or not isinstance(endpoint, str)
        ):
            malformed_lines_count += 1
            continue

        # Initialize user metrics tracking
        if user_id not in user_stats:
            user_stats[user_id] = {
                "request_count": 0,
                "error_count": 0,
                "total_latency": 0.0,
                "endpoints": {},
            }

        stats = user_stats[user_id]
        stats["request_count"] += 1
        stats["total_latency"] += float(latency)

        # Track HTTP error statuses (4xx and 5xx)
        if 400 <= status_code <= 599:
            stats["error_count"] += 1

        # Track endpoint frequency
        stats["endpoints"][endpoint] = stats["endpoints"].get(endpoint, 0) + 1

    # Compile final metrics sorted deterministically by User ID
    processed_users = {}
    for user_id in sorted(user_stats.keys()):
        stats = user_stats[user_id]
        req_count = stats["request_count"]

        # Calculate average latency rounded to 2 decimal places
        avg_latency = (
            round(stats["total_latency"] / req_count, 2) if req_count > 0 else 0.0
        )

        # Determine most requested endpoint with lexical tie-breaking:
        # Sort key prioritizes highest count (-count), then alphabetical order (endpoint name)
        most_requested = sorted(
            stats["endpoints"].items(), key=lambda item: (-item[1], item[0])
        )[0][0]

        processed_users[str(user_id)] = {
            "request_count": req_count,
            "error_count": stats["error_count"],
            "avg_latency_ms": avg_latency,
            "most_requested_endpoint": most_requested,
        }

    final_report = {
        "summary": {
            "total_users_processed": len(processed_users),
            "malformed_lines_skipped": malformed_lines_count,
        },
        "users": processed_users,
    }

    json.dump(final_report, output_stream, indent=2, sort_keys=False)


if __name__ == "__main__":
    # Reads from standard input and outputs deterministically to standard output
    analyze_ndjson(sys.stdin, sys.stdout)