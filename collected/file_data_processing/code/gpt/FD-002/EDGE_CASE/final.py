import json
import sys
from collections import defaultdict


def analyze_ndjson(input_file, output_file):
    users = defaultdict(lambda: {
        "request_count": 0,
        "error_count": 0,
        "total_latency": 0.0,
        "latency_count": 0,
        "endpoints": defaultdict(int)
    })

    malformed_lines = 0

    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                malformed_lines += 1
                continue

            if not isinstance(record, dict):
                malformed_lines += 1
                continue

            user = record.get("user")
            request = record.get("request")

            if not isinstance(user, dict) or not isinstance(request, dict):
                continue

            user_id = user.get("id")

            if user_id is None:
                continue

            user_id = str(user_id)

            stats = users[user_id]

            stats["request_count"] += 1

            status = request.get("status")

            if isinstance(status, int) and status >= 400:
                stats["error_count"] += 1

            latency = request.get("latency")

            if isinstance(latency, (int, float)) and not isinstance(latency, bool):
                stats["total_latency"] += latency
                stats["latency_count"] += 1

            endpoint = request.get("endpoint")

            if endpoint is not None:
                endpoint = str(endpoint)
                stats["endpoints"][endpoint] += 1

    results = []

    for user_id in sorted(users):
        stats = users[user_id]

        if stats["latency_count"] > 0:
            average_latency = (
                stats["total_latency"] / stats["latency_count"]
            )
        else:
            average_latency = 0

        if stats["endpoints"]:
            most_requested_endpoint = min(
                stats["endpoints"],
                key=lambda endpoint: (
                    -stats["endpoints"][endpoint],
                    endpoint
                )
            )
        else:
            most_requested_endpoint = None

        results.append({
            "user_id": user_id,
            "request_count": stats["request_count"],
            "error_count": stats["error_count"],
            "average_latency": average_latency,
            "most_requested_endpoint": most_requested_endpoint
        })

    output = {
        "malformed_lines": malformed_lines,
        "users": results
    }

    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(
            output,
            outfile,
            indent=2,
            ensure_ascii=False,
            sort_keys=False
        )
        outfile.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzer.py input.ndjson output.json")
        sys.exit(1)

    analyze_ndjson(sys.argv[1], sys.argv[2])