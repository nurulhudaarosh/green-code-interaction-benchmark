class ValidationError(ValueError):
    """Raised when scores or weights fail validation."""
    pass


def validate_scores(scores, score_range=(0, 100)):
    """Validate a dict of {name: score}. Raises ValidationError if invalid."""
    if not isinstance(scores, dict) or not scores:
        raise ValidationError("Scores must be a non-empty dict")

    lo, hi = score_range
    errors = {}
    for name, value in scores.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors[name] = f"not numeric ({value!r})"
        elif value != value:  # NaN check
            errors[name] = "score is NaN"
        elif not (lo <= value <= hi):
            errors[name] = f"out of range [{lo}, {hi}] (got {value})"

    if errors:
        details = "; ".join(f"{k}: {v}" for k, v in errors.items())
        raise ValidationError(f"Invalid score(s) — {details}")


def validate_weights(weights):
    """Validate a dict of {name: weight}. Raises ValidationError if invalid."""
    if not isinstance(weights, dict) or not weights:
        raise ValidationError("Weights must be a non-empty dict")

    errors = {}
    for name, value in weights.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors[name] = f"not numeric ({value!r})"
        elif value != value:  # NaN check
            errors[name] = "weight is NaN"
        elif value < 0:
            errors[name] = f"negative weight ({value})"

    if errors:
        details = "; ".join(f"{k}: {v}" for k, v in errors.items())
        raise ValidationError(f"Invalid weight(s) — {details}")

    if sum(weights.values()) <= 0:
        raise ValidationError("Sum of weights must be greater than 0")


def compute_weighted_score(scores, weights, score_range=(0, 100)):
    """
    Compute a weighted average score.

    scores:  dict[str, float] -- name -> raw score
    weights: dict[str, float] -- name -> weight (same keys as scores)
    score_range: (min, max) inclusive valid range for each score

    Returns the weighted average. Raises ValidationError on bad input.
    """
    # Key-consistency check happens before value validation so mismatches
    # are reported clearly rather than surfacing as a confusing KeyError.
    score_keys, weight_keys = set(scores), set(weights)
    if score_keys != weight_keys:
        missing_weights = score_keys - weight_keys
        missing_scores = weight_keys - score_keys
        parts = []
        if missing_weights:
            parts.append(f"missing weights for: {sorted(missing_weights)}")
        if missing_scores:
            parts.append(f"missing scores for: {sorted(missing_scores)}")
        raise ValidationError("Score/weight key mismatch — " + "; ".join(parts))

    validate_scores(scores, score_range)
    validate_weights(weights)

    total_weight = sum(weights.values())
    weighted_sum = sum(scores[name] * weights[name] for name in scores)
    return weighted_sum / total_weight


if __name__ == "__main__":
    # Valid case
    scores = {"math": 85, "writing": 92, "science": 78}
    weights = {"math": 0.4, "writing": 0.3, "science": 0.3}
    print("Weighted score:", compute_weighted_score(scores, weights))

    # Invalid score: out of range
    try:
        compute_weighted_score({"math": 150}, {"math": 1.0})
    except ValidationError as e:
        print("Caught:", e)

    # Invalid score: wrong type
    try:
        compute_weighted_score({"math": "90"}, {"math": 1.0})
    except ValidationError as e:
        print("Caught:", e)

    # Invalid weight: negative
    try:
        compute_weighted_score({"math": 90}, {"math": -0.5})
    except ValidationError as e:
        print("Caught:", e)

    # Invalid weight: all zero
    try:
        compute_weighted_score({"math": 90, "sci": 80}, {"math": 0, "sci": 0})
    except ValidationError as e:
        print("Caught:", e)

    # Key mismatch
    try:
        compute_weighted_score({"math": 90}, {"science": 1.0})
    except ValidationError as e:
        print("Caught:", e)