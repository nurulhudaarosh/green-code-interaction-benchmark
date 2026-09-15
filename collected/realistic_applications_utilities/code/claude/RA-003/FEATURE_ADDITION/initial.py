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


def rank_entities(entities, score_range=(0, 100), reverse=True, round_to=6):
    """
    Compute deterministic rankings for multiple entities.

    entities: dict[str, dict] mapping entity_name -> {
        "scores": {criterion: value, ...},
        "weights": {criterion: value, ...},
    }
    score_range: inclusive valid range applied to every entity's scores
    reverse: True for highest-score-first (descending), False for ascending
    round_to: decimal places to round the weighted score to before ranking,
              so floating-point noise doesn't create spurious tie-breaks

    Returns a list of dicts, each: {"rank", "name", "score"}.
    Rank is 1-based. Ties (equal rounded score) share the same rank
    (standard competition ranking: 1, 2, 2, 4). Entities are always
    ordered by (score, then name) so the result is fully deterministic
    regardless of input dict order.

    Raises ValidationError if `entities` is empty/malformed, or if any
    entity's scores/weights are invalid.
    """
    if not isinstance(entities, dict) or not entities:
        raise ValidationError("Entities must be a non-empty dict")

    computed = []
    for name, data in entities.items():
        if not isinstance(data, dict) or "scores" not in data or "weights" not in data:
            raise ValidationError(
                f"Entity '{name}' must be a dict with 'scores' and 'weights' keys"
            )
        try:
            raw_score = compute_weighted_score(
                data["scores"], data["weights"], score_range
            )
        except ValidationError as e:
            # Re-raise with entity context so the source is unambiguous
            raise ValidationError(f"Entity '{name}': {e}") from e

        computed.append((name, round(raw_score, round_to)))

    # Deterministic ordering: primary key = score (per `reverse`),
    # secondary key = name ascending, always ascending regardless of
    # `reverse` so tie order doesn't flip depending on sort direction.
    computed.sort(key=lambda item: item[0])              # name asc first (stable base)
    computed.sort(key=lambda item: item[1], reverse=reverse)  # then score

    ranked = []
    current_rank = 0
    seen = 0
    prev_score = None
    for name, score in computed:
        seen += 1
        if score != prev_score:
            current_rank = seen  # competition ranking: skips after ties
            prev_score = score
        ranked.append({"rank": current_rank, "name": name, "score": score})

    return ranked


if __name__ == "__main__":
    # --- Validation examples ---
    try:
        compute_weighted_score({"math": 150}, {"math": 1.0})
    except ValidationError as e:
        print("Caught:", e)

    try:
        compute_weighted_score({"math": 90, "sci": 80}, {"math": 0, "sci": 0})
    except ValidationError as e:
        print("Caught:", e)

    # --- Ranking example ---
    entities = {
        "Alice": {
            "scores": {"math": 85, "writing": 92, "science": 78},
            "weights": {"math": 0.4, "writing": 0.3, "science": 0.3},
        },
        "Bob": {
            "scores": {"math": 90, "writing": 80, "science": 85},
            "weights": {"math": 0.4, "writing": 0.3, "science": 0.3},
        },
        "Carol": {
            "scores": {"math": 85, "writing": 92, "science": 78},  # ties Alice
            "weights": {"math": 0.4, "writing": 0.3, "science": 0.3},
        },
    }

    for entry in rank_entities(entities):
        print(f"#{entry['rank']} {entry['name']}: {entry['score']}")

    # Ranking with invalid entity data surfaces which entity failed
    bad_entities = {
        "Dan": {"scores": {"math": 999}, "weights": {"math": 1.0}},
    }
    try:
        rank_entities(bad_entities)
    except ValidationError as e:
        print("Caught:", e)