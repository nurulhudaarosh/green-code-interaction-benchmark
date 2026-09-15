#!/usr/bin/env python3
"""
Offline NDJSON Analyzer

Reads newline-delimited JSON (NDJSON) log records of the form:

    {"user": {"id": "u1"}, "request": {"endpoint": "/api/x", "status": 200, "latency_ms": 123.4}}

For each user, computes:
  - request_count
  - error_count   (status >= 400)
  - avg_latency   (rounded to 3 decimals)
  - top_endpoint  (most requested; ties broken lexically, i.e. alphabetically smallest wins)

Malformed / unparseable lines are skipped and counted separately.
Output is deterministic JSON, sorted by user ID, written to stdout (or a file).

Usage:
    python ndjson_analyzer.py input.ndjson
    cat input.ndjson | python ndjson_analyzer.py
    python ndjson_analyzer.py input.ndjson -o output.json
"""

import sys
import json
import argparse
from collections import defaultdict, Counter


def parse_line(line):
    """Parse a single NDJSON line, returning (user_id, endpoint, status, latency) or None if invalid."""
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(record, dict):
        return None

    user = record.get("user")
    request = record.get("request")
    if not isinstance(user, dict) or not isinstance(request, dict):
        return None

    user_id = user.get("id")
    endpoint = request.get("endpoint")
    status = request.get("status")
    latency = request.get("latency_ms", request.get("latency"))

    # All required fields must be present and correctly typed
    if user_id is None or endpoint is None:
        return None
    if not isinstance(status, (int, float)) or isinstance(status, bool):
        return None
    if not isinstance(latency, (int, float)) or isinstance(latency, bool):
        return None

    return str(user_id), str(endpoint), int(status), float(latency)


def analyze(lines):
    stats = defaultdict(lambda: {
        "request_count": 0,
        "error_count": 0,
        "latency_sum": 0.0,
        "endpoints": Counter(),
    })
    malformed_count = 0

    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            malformed_count += 1
            continue

        user_id, endpoint, status, latency = parsed
        s = stats[user_id]
        s["request_count"] += 1
        s["latency_sum"] += latency
        s["endpoints"][endpoint] += 1
        if status >= 400:
            s["error_count"] += 1

    results = {}
    for user_id, s in stats.items():
        avg_latency = s["latency_sum"] / s["request_count"] if s["request_count"] else 0.0

        # Determine top endpoint: highest count, ties broken lexically (alphabetically smallest)
        top_endpoint = None
        if s["endpoints"]:
            max_count = max(s["endpoints"].values())
            candidates = [ep for ep, cnt in s["endpoints"].items() if cnt == max_count]
            top_endpoint = min(candidates)  # lexical tie-break

        results[user_id] = {
            "request_count": s["request_count"],
            "error_count": s["error_count"],
            "avg_latency": round(avg_latency, 3),
            "top_endpoint": top_endpoint,
        }

    output = {
        "users": dict(sorted(results.items(), key=lambda kv: kv[0])),
        "malformed_lines": malformed_count,
    }
    return output


def main():
    parser = argparse.ArgumentParser(description="Offline NDJSON log analyzer.")
    parser.add_argument("input", nargs="?", help="Path to NDJSON file (default: stdin)")
    parser.add_argument("-o", "--output", help="Path to write JSON output (default: stdout)")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    result = analyze(lines)
    output_json = json.dumps(result, indent=2, sort_keys=True)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
    else:
        print(output_json)


if __name__ == "__main__":
    main()