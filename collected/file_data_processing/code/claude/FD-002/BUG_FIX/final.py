for raw in lines:
    raw = raw.strip()
    if not raw:
        continue

    try:
        record = json.loads(raw)
        user = record["user"]
        request = record["request"]
        user_id = user["id"]
        endpoint = request["endpoint"]
        status = request["status"]
        latency = request["latency_ms"]

        if not isinstance(user_id, str) or not isinstance(endpoint, str):
            raise ValueError("bad field type")
        if not isinstance(status, (int, float)) or not isinstance(latency, (int, float)):
            raise ValueError("bad field type")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        malformed += 1
        continue   # <-- skips this line, run keeps going

    # only reached for valid records — stats update here
    total_requests += 1
    ...