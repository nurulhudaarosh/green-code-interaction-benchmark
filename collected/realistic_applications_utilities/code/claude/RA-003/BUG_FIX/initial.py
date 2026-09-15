class ValidationError(ValueError):
    """Raised when scores or weights fail validation."""
    pass


def compute_weighted_score(scores, weights, score_range=(0, 100)):
    """
    Compute a weighted average score.

    scores: dict[str, float] -- name -> raw score
    weights: dict[str, float] -- name -> weight (must cover same keys as scores)
    score_range: (min, max) valid inclusive range for each score

    Returns the weighted average score.
    Raises ValidationError on any invalid score or weight.
    """
    lo, hi = score_range

    # --- Key consistency check ---
    score_keys = set(scores.keys())
    weight_keys = set(weights.keys())
    if score_keys != weight_keys:
        missing_weights = score_keys - weight_keys
        missing_scores = weight_keys - score_keys
        msg_parts = []
        if missing_weights:
            msg_parts.append(f"missing weights for: {sorted(missing_weights)}")
        if missing_scores:
            msg_parts.append(f"missing scores for: {sorted(missing_scores)}")
        raise ValidationError("Score/weight key mismatch — " + "; ".join(msg_parts))

    # --- Score validation ---
    invalid_scores = {}
    for name, value in scores.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            invalid_scores[name] = f"not numeric ({value!r})"
        elif not (lo <= value <= hi):
            invalid_scores[name] = f"out of range [{lo}, {hi}] ({value})"

    if invalid_scores:
        details = "; ".join(f"{k}: {v}" for k, v in invalid_scores.items())
        raise ValidationError(f"Invalid score(s) — {details}")

    # --- Weight validation ---
    invalid_weights = {}
    for name, value in weights.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            invalid_weights[name] = f"not numeric ({value!r})"
        elif value < 0:
            invalid_weights[name] = f"negative weight ({value})"

    if invalid_weights:
        details = "; ".join(f"{k}: {v}" for k, v in invalid_weights.items())
        raise ValidationError(f"Invalid weight(s) — {details}")

    total_weight = sum(weights.values())
    if total_weight <= 0:
        raise ValidationError("Sum of weights must be greater than 0")

    # --- Weighted average (normalized, so weights need not sum to 1) ---
    weighted_sum = sum(scores[name] * weights[name] for name in scores)
    return weighted_sum / total_weight


if __name__ == "__main__":
    # Example: valid input
    scores = {"math": 85, "writing": 92, "science": 78}
    weights = {"math": 0.4, "writing": 0.3, "science": 0.3}
    print("Weighted score:", compute_weighted_score(scores, weights))

    # Example: invalid score (out of range)
    try:
        compute_weighted_score({"math": 150}, {"math": 1.0})
    except ValidationError as e:
        print("Caught:", e)

    # Example: invalid weight (negative)
    try:
        compute_weighted_score({"math": 90}, {"math": -0.5})
    except ValidationError as e:
        print("Caught:", e)