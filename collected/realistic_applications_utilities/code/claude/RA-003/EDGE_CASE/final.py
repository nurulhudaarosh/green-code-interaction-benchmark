from dataclasses import dataclass
from typing import Any, Optional
import math


@dataclass
class Assessment:
    name: str
    score: Optional[float]
    pass_mark: Optional[float]
    valid: bool = True
    reason: str = ""


def parse_assessments(raw: list[dict[str, Any]]) -> list[Assessment]:
    parsed = []
    for i, r in enumerate(raw or []):
        name = r.get("name", f"unnamed_{i}")
        score, pass_mark = r.get("score"), r.get("pass_mark")

        if score is None or pass_mark is None:
            parsed.append(Assessment(name, None, None, False, "missing score/pass_mark"))
            continue
        try:
            score, pass_mark = float(score), float(pass_mark)
        except (TypeError, ValueError):
            parsed.append(Assessment(name, None, None, False, "non-numeric value"))
            continue
        if not (math.isfinite(score) and math.isfinite(pass_mark)):
            parsed.append(Assessment(name, None, None, False, "NaN/infinite value"))
            continue
        if score < 0 or pass_mark < 0:
            parsed.append(Assessment(name, None, None, False, "negative value"))
            continue

        parsed.append(Assessment(name, score, pass_mark))
    return parsed


def evaluate(raw: list[dict[str, Any]]) -> dict[str, Any]:
    if not raw:
        return {"results": [], "invalid": [],
                "summary": {"total": 0, "passed": 0, "failed": 0, "invalid": 0}}

    parsed = parse_assessments(raw)
    valid = [a for a in parsed if a.valid]
    invalid = [a for a in parsed if not a.valid]

    results = [{
        "name": a.name, "score": a.score, "pass_mark": a.pass_mark,
        "passed": a.score >= a.pass_mark,                 # exact pass mark counts as PASS
        "exact_pass": math.isclose(a.score, a.pass_mark),
    } for a in valid]

    ranked = sorted(results, key=lambda x: x["score"], reverse=True)
    rank, prev = 0, None
    for i, r in enumerate(ranked, start=1):
        if r["score"] != prev:
            rank, prev = i, r["score"]
        r["rank"] = rank                                   # ties share a rank (1,2,2,4)

    passed_count = sum(r["passed"] for r in results)
    return {
        "results": ranked,
        "invalid": [{"name": a.name, "reason": a.reason} for a in invalid],
        "summary": {"total": len(raw), "passed": passed_count,
                    "failed": len(valid) - passed_count, "invalid": len(invalid)},
    }


# --- proof each case is handled ---
if __name__ == "__main__":
    empty = evaluate([])
    assert empty["summary"] == {"total": 0, "passed": 0, "failed": 0, "invalid": 0}

    exact = evaluate([{"name": "Bob", "score": 60, "pass_mark": 60}])
    assert exact["results"][0]["passed"] is True and exact["results"][0]["exact_pass"] is True

    tie = evaluate([
        {"name": "Alice", "score": 85, "pass_mark": 60},
        {"name": "Carl", "score": 85, "pass_mark": 60},
        {"name": "Dana", "score": 70, "pass_mark": 60},
    ])
    ranks = {r["name"]: r["rank"] for r in tie["results"]}
    assert ranks["Alice"] == ranks["Carl"] == 1 and ranks["Dana"] == 3  # skip to 3, not 2

    bad = evaluate([
        {"name": "Eve", "pass_mark": 60},          # missing score
        {"name": "Fay", "score": "n/a", "pass_mark": 60},  # non-numeric
        {"name": "Gus", "score": -5, "pass_mark": 60},     # negative
    ])
    assert bad["summary"]["invalid"] == 3 and bad["results"] == []

    print("all cases verified")