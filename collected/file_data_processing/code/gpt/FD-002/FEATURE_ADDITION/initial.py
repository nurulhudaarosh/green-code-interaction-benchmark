import json
import argparse


def analyze_ndjson(input_file, output_file):
    users = {}
    endpoint_counts = {}
    malformed_lines = 0

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed_lines += 1
                continue

            user = record.get("user", {})
            request = record.get("request", {})

            user_id = user.get("id")
            endpoint = request.get("endpoint")
            latency = request.get("latency", 0)
            status = request.get("status")

            if user_id is None:
                continue

            user_id = str(user_id)

            if user_id not in users:
                users[user_id] = {
                    "request_count": 0,
                    "error_count": 0,
                    "total_latency": 0.0
                }

            users[user_id]["request_count"] += 1

            try:
                users[user_id]["total_latency"] += float(latency)
            except (TypeError, ValueError):
                pass

            if isinstance(status, int) and status >= 400:
                users[user_id]["error_count"] += 1
            elif isinstance(status, str) and status.isdigit():
                if int(status) >= 400:
                    users[user_id]["error_count"] += 1

            if endpoint is not None:
                endpoint = str(endpoint)
                endpoint_counts[endpoint] = (
                    endpoint_counts.get(endpoint, 0) + 1
                )

    # ---------------------------------------------------------
    # 1. Find the most-requested endpoint.
    #    Lexically smallest endpoint wins in case of a tie.
    # ---------------------------------------------------------
    most_requested_endpoint = None

    if endpoint_counts:
        most_requested_endpoint = min(
            endpoint_counts,
            key=lambda endpoint: (
                -endpoint_counts[endpoint],
                endpoint
            )
        )

    # ---------------------------------------------------------
    # 2. Create deterministic JSON sorted by user ID.
    # ---------------------------------------------------------
    result = {
        "malformed_lines": malformed_lines,
        "most_requested_endpoint": most_requested_endpoint,
        "users": {}
    }

    for user_id in sorted(users):
        user_data = users[user_id]
        request_count = user_data["request_count"]

        average_latency = (
            user_data["total_latency"] / request_count
            if request_count > 0
            else 0.0
        )

        result["users"][user_id] = {
            "request_count": request_count,
            "error_count": user_data["error_count"],
            "average_latency": round(average_latency, 2)
        }

    # ---------------------------------------------------------
    # 3. Write the deterministic JSON output.
    # ---------------------------------------------------------
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze NDJSON request logs."
    )

    parser.add_argument(
        "input",
        help="Input NDJSON file"
    )

    parser.add_argument(
        "output",
        help="Output JSON file"
    )

    args = parser.parse_args()

    analyze_ndjson(
        args.input,
        args.output
    )


if __name__ == "__main__":
    main()