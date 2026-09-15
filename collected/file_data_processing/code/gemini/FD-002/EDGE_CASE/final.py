import json
import sys
from collections import defaultdict


def analyze_ndjson(input_stream):
    """Analyzes NDJSON stream containing user and request metadata.

    Handles malformed JSON lines anywhere in the stream while counting them.
    Tracks metrics per user and resolves most-requested endpoint ties deterministically
    via lexical comparison (alphabetical order). Returns a deterministic structure
    sorted by user ID.
    """
    user_metrics = defaultdict(
        lambda: {
            "request_count": 0,
            "error_count": 0,
            "total_latency": 0.0,
            "endpoints": defaultdict(int),
        }
    )

    malformed_lines_count = 0

    for line in input_stream:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                malformed_lines_count += 1
                continue

            user_data = data.get("user")
            request_data = data.get("request")

            if not isinstance(user_data, dict) or not isinstance(request_data, dict):
                malformed_lines_count += 1
                continue

            user_id = user_data.get("id")
            endpoint = request_data.get("endpoint")
            latency = request_data.get("latency")
            status = request_data.get("status")

            # Validate required fields, non-empty values, and appropriate data types
            if (
                user_id is None
                or endpoint is None
                or not isinstance(latency, (int, float))
                or isinstance(latency, bool)
                or not isinstance(status, int)
                or isinstance(status, bool)
            ):
                malformed_lines_count += 1
                continue

            stats = user_metrics[str(user_id)]
            stats["request_count"] += 1
            stats["total_latency"] += float(latency)
            stats["endpoints"][str(endpoint)] += 1

            if status >= 400:
                stats["error_count"] += 1

        except (json.JSONDecodeError, AttributeError, TypeError):
            malformed_lines_count += 1

    # Build final analysis structure sorted deterministically by user ID
    sorted_users = {}
    for user_id in sorted(user_metrics.keys()):
        stats = user_metrics[user_id]
        req_count = stats["request_count"]

        avg_latency = (
            round(stats["total_latency"] / req_count, 4) if req_count > 0 else 0.0
        )

        # Deterministic tie-breaking for most requested endpoint:
        # 1. Primary key: count (descending, via -x[1])
        # 2. Secondary key: endpoint string (ascending alphabetically, via x[0])
        most_requested_endpoint = None
        if stats["endpoints"]:
            most_requested_endpoint = min(
                stats["endpoints"].items(), key=lambda x: (-x[1], x[0])
            )[0]

        sorted_users[user_id] = {
            "request_count": req_count,
            "error_count": stats["error_count"],
            "average_latency": avg_latency,
            "most_requested_endpoint": most_requested_endpoint,
        }

    return {
        "malformed_lines_count": malformed_lines_count,
        "users": sorted_users,
    }


def process_ndjson_file(file_path):
    """Reads NDJSON file and returns formatted, sorted JSON string."""
    with open(file_path, "r", encoding="utf-8") as f:
        analysis_result = analyze_ndjson(f)

    return json.dumps(analysis_result, indent=2, sort_keys=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(process_ndjson_file(sys.argv[1]))
    else:
        from io import StringIO

        # Edge cases test: broken JSON lines interspersed, non-dict lines, and endpoint ties
        sample_ndjson = """NOT_VALID_JSON
{"user": {"id": "usr_2"}, "request": {"endpoint": "/beta", "latency": 100, "status": 200}}
{"user": {"id": "usr_1"}, "request": {"endpoint": "/zeta", "latency": 50, "status": 200}}
{"user": "invalid_user_structure", "request": {"endpoint": "/alpha", "latency": 50, "status": 200}}
{"user": {"id": "usr_1"}, "request": {"endpoint": "/alpha", "latency": 150, "status": 500}}
[1, 2, 3]
{"user": {"id": "usr_2"}, "request": {"endpoint": "/alpha", "latency": 200, "status": 200}}"""

        result = analyze_ndjson(StringIO(sample_ndjson))
        print(json.dumps(result, indent=2, sort_keys=True))