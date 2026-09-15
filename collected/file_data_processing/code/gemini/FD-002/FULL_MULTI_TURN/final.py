import json
import sys


def analyze_ndjson(input_stream, output_stream):
    """Parses NDJSON data, deterministically handling malformed lines anywhere in

    the input stream and breaking endpoint frequency ties lexically.
    """
    user_stats = {}
    malformed_lines_count = 0

    for line in input_stream:
        line = line.strip()
        if not line:
            continue

        # Catch syntax/formatting errors for malformed JSON lines
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            malformed_lines_count += 1
            continue

        # Ensure top-level structure contains expected nested dictionaries
        if not isinstance(data, dict):
            malformed_lines_count += 1
            continue

        user_info = data.get("user")
        req_info = data.get("request")

        if not isinstance(user_info, dict) or not isinstance(req_info, dict):
            malformed_lines_count += 1
            continue

        user_id = user_info.get("id")
        latency = req_info.get("latency")
        status_code = req_info.get("status")
        endpoint = req_info.get("endpoint")

        # Validate types to ensure schema integrity regardless of line order
        if (
            user_id is None
            or not isinstance(latency, (int, float))
            or isinstance(latency, bool)
            or not isinstance(status_code, int)
            or isinstance(status_code, bool)
            or not isinstance(endpoint, str)
        ):
            malformed_lines_count += 1
            continue

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

        if 400 <= status_code <= 599:
            stats["error_count"] += 1

        stats["endpoints"][endpoint] = stats["endpoints"].get(endpoint, 0) + 1

    processed_users = {}

    # Sort user keys deterministically (handles mixed types via string conversion sorting)
    sorted_user_ids = sorted(user_stats.keys(), key=lambda uid: str(uid))

    for user_id in sorted_user_ids:
        stats = user_stats[user_id]
        req_count = stats["request_count"]

        avg_latency = (
            round(stats["total_latency"] / req_count, 2) if req_count > 0 else 0.0
        )

        # Deterministic tie-breaking:
        # 1. Primary sort: -count (highest frequency first)
        # 2. Secondary sort: endpoint string (lexically smallest first for ties)
        most_requested = sorted(
            stats["endpoints"].items(), key=lambda item: (-item[1], item[0])
        )[0][0]

        processed_users[str(user_id)] = {
            "request_count": req_count,
            "error_count": stats["error_count"],
            "avg_latency_ms": avg_latency,
            "most_requested_endpoint": most_requested,
        }

    # Deterministic final JSON report
    final_report = {
        "summary": {
            "total_users_processed": len(processed_users),
            "malformed_lines_skipped": malformed_lines_count,
        },
        "users": processed_users,
    }

    json.dump(final_report, output_stream, indent=2, sort_keys=False)


if __name__ == "__main__":
    analyze_ndjson(sys.stdin, sys.stdout)