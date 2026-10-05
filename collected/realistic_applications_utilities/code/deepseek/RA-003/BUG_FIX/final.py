import json
import math
import statistics
from typing import Dict, List, Tuple, Optional, Iterable
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 1. VALIDATION LAYER (corrected)
# ============================================================
class ValidationError(ValueError):
    """Raised when a score, weight, name, or subject fails validation."""


def validate_score(value, *, label: str = "Score") -> float:
    """Score must be a finite real number in [0, 100].

    Rejects: bool, non-numerics, None, NaN, +Inf, -Inf, values < 0 or > 100.
    """
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be numeric, not bool: {value!r}")
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{label} must be int or float, got {type(value).__name__}: {value!r}"
        )
    v = float(value)
    if math.isnan(v) or math.isinf(v):
        raise ValidationError(f"{label} must be finite, got {value!r}")
    if not (0.0 <= v <= 100.0):
        raise ValidationError(f"{label} must be within [0, 100], got {v}")
    return v


def validate_weight(value, *, label: str = "Weight") -> float:
    """Weight must be a finite real number in (0, 1].

    Rejects: bool, non-numerics, None, NaN, Inf, 0, negatives, > 1.
    """
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be numeric, not bool: {value!r}")
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{label} must be int or float, got {type(value).__name__}: {value!r}"
        )
    v = float(value)
    if math.isnan(v) or math.isinf(v):
        raise ValidationError(f"{label} must be finite, got {value!r}")
    if not (0.0 < v <= 1.0):
        raise ValidationError(f"{label} must be within (0, 1], got {v}")
    return v


def validate_nonempty_str(value, *, label: str = "Value") -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a string, got {type(value).__name__}: {value!r}")
    s = value.strip()
    if not s:
        raise ValidationError(f"{label} must be a non-empty string")
    return s


def validate_weights_sum(weights: Dict[str, float], *, tol: float = 1e-6) -> None:
    """Weights across all subjects must sum to 1.0 within tolerance."""
    if not weights:
        raise ValidationError("Weights cannot be empty; at least one subject is required.")
    total = sum(weights.values())
    if abs(total - 1.0) > tol:
        pretty = {k: round(v, 6) for k, v in weights.items()}
        raise ValidationError(
            f"Subject weights must sum to 1.0, got {total:.6f}. Weights: {pretty}"
        )


# ============================================================
# 2. GRADE SCALE
# ============================================================
class GradeScale(Enum):
    A_PLUS = 90
    A = 85
    B_PLUS = 80
    B = 75
    C_PLUS = 70
    C = 65
    D_PLUS = 60
    D = 55
    F = 0


def letter_for(avg: float) -> str:
    for grade in GradeScale:
        if avg >= grade.value:
            return grade.name.replace("_PLUS", "+")
    return "F"


# ============================================================
# 3. STUDENT MODEL
# ============================================================
@dataclass
class Student:
    student_id: str
    name: str
    scores: Dict[str, float] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)

    def add_score(self, subject: str, score) -> None:
        subj = validate_nonempty_str(subject, label="Subject")
        sc = validate_score(score)
        self.scores[subj] = sc

    def set_weight(self, subject: str, weight) -> None:
        subj = validate_nonempty_str(subject, label="Subject")
        w = validate_weight(weight)
        self.weights[subj] = w

    def set_weights(self, weights: Dict[str, float]) -> None:
        """Replace all weights after validating each and their sum == 1.0."""
        if not isinstance(weights, dict):
            raise ValidationError(f"weights must be a dict, got {type(weights).__name__}")
        clean: Dict[str, float] = {}
        for subj, w in weights.items():
            clean[validate_nonempty_str(subj, label="Subject")] = validate_weight(w)
        validate_weights_sum(clean)
        self.weights = clean

    def has_complete_weights(self) -> bool:
        """True iff every scored subject has a weight and they sum to 1.0."""
        if not self.scores or set(self.scores) != set(self.weights):
            return False
        try:
            validate_weights_sum(self.weights)
            return True
        except ValidationError:
            return False

    def average(self) -> float:
        if not self.scores:
            return 0.0
        if self.has_complete_weights():
            return sum(self.scores[s] * self.weights[s] for s in self.scores)
        return sum(self.scores.values()) / len(self.scores)

    def letter_grade(self) -> str:
        return letter_for(self.average())


# ============================================================
# 4. ANALYZER
# ============================================================
class StudentPerformanceAnalyzer:
    def __init__(self) -> None:
        self.students: Dict[str, Student] = {}

    # ---------- CRUD ----------
    def add_student(self, student_id: str, name: str) -> Student:
        sid = validate_nonempty_str(student_id, label="student_id")
        nm = validate_nonempty_str(name, label="name")
        if sid in self.students:
            raise ValidationError(f"Student {sid!r} already exists")
        s = Student(sid, nm)
        self.students[sid] = s
        return s

    def remove_student(self, student_id: str) -> None:
        sid = validate_nonempty_str(student_id, label="student_id")
        if sid not in self.students:
            raise KeyError(f"Student {sid!r} not found")
        del self.students[sid]

    def get_student(self, student_id: str) -> Student:
        sid = validate_nonempty_str(student_id, label="student_id")
        if sid not in self.students:
            raise KeyError(f"Student {sid!r} not found")
        return self.students[sid]

    def record_score(self, student_id: str, subject: str, score) -> None:
        self.get_student(student_id).add_score(subject, score)

    def set_weights(self, student_id: str, weights: Dict[str, float]) -> None:
        self.get_student(student_id).set_weights(weights)

    # ---------- Analytics ----------
    def class_average(self, subject: Optional[str] = None) -> float:
        if not self.students:
            return 0.0
        if subject is not None:
            subj = validate_nonempty_str(subject, label="Subject")
            vals = [s.scores[subj] for s in self.students.values() if subj in s.scores]
            return statistics.mean(vals) if vals else 0.0
        return statistics.mean([s.average() for s in self.students.values()])

    def subject_statistics(self) -> Dict[str, Dict[str, float]]:
        subjects = {subj for s in self.students.values() for subj in s.scores}
        out: Dict[str, Dict[str, float]] = {}
        for subj in sorted(subjects):
            vals = [s.scores[subj] for s in self.students.values() if subj in s.scores]
            if vals:
                out[subj] = {
                    "mean": statistics.mean(vals),
                    "median": statistics.median(vals),
                    "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
                    "min": min(vals),
                    "max": max(vals),
                    "count": len(vals),
                }
        return out

    def rank_students(self) -> List[Tuple[int, str, float, str]]:
        ranked = sorted(self.students.values(), key=lambda s: s.average(), reverse=True)
        return [(i + 1, s.name, round(s.average(), 2), s.letter_grade())
                for i, s in enumerate(ranked)]

    def top_performers(self, n: int = 3) -> List[Tuple[str, float]]:
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            raise ValidationError(f"n must be a non-negative int, got {n!r}")
        return [(name, avg) for _, name, avg, _ in self.rank_students()[:n]]

    def at_risk_students(self, threshold: float = 60.0) -> List[Tuple[str, float]]:
        t = validate_score(threshold, label="threshold")
        return [(s.name, round(s.average(), 2))
                for s in self.students.values() if s.average() < t]

    def grade_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for s in self.students.values():
            g = s.letter_grade()
            dist[g] = dist.get(g, 0) + 1
        return dist

    # ---------- Report ----------
    def generate_report(self) -> str:
        L: List[str] = ["=" * 60, "STUDENT PERFORMANCE REPORT", "=" * 60]
        L.append(f"Total Students: {len(self.students)}\n")

        L.append("--- Rankings ---")
        for rank, name, avg, grade in self.rank_students():
            L.append(f"  {rank}. {name:<20} Avg: {avg:>6.2f}  Grade: {grade}")

        L.append("\n--- Subject Statistics ---")
        for subj, st in self.subject_statistics().items():
            L.append(f"  {subj}:")
            L.append(f"    Mean: {st['mean']:.2f} | Median: {st['median']:.2f} | "
                     f"StDev: {st['stdev']:.2f}")
            L.append(f"    Min: {st['min']:.2f} | Max: {st['max']:.2f} | "
                     f"Count: {st['count']}")

        L.append("\n--- Grade Distribution ---")
        for grade, count in sorted(self.grade_distribution().items()):
            L.append(f"  {grade}: {'*' * count} ({count})")

        L.append("\n--- Top Performers ---")
        for name, avg in self.top_performers(3):
            L.append(f"  {name}: {avg}")

        L.append("\n--- At-Risk Students (avg < 60) ---")
        at_risk = self.at_risk_students()
        L.append("  None 🎉" if not at_risk else "\n".join(f"  {n}: {a}" for n, a in at_risk))

        L.append(f"\nClass Average: {self.class_average():.2f}")
        L.append("=" * 60)
        return "\n".join(L)

    # ---------- Persistence ----------
    def save(self, path: str) -> None:
        payload = {
            sid: {"name": s.name, "scores": s.scores, "weights": s.weights}
            for sid, s in self.students.items()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Build a fresh dict so a partial failure doesn't corrupt state
        new_students: Dict[str, Student] = {}
        for sid, info in data.items():
            s = Student(validate_nonempty_str(sid, label="student_id"),
                        validate_nonempty_str(info["name"], label="name"))
            for subj, sc in info.get("scores", {}).items():
                s.add_score(subj, sc)          # re-validates every score
            if info.get("weights"):
                s.set_weights(info["weights"])  # re-validates every weight + sum
            new_students[s.student_id] = s
        self.students = new_students


# ============================================================
# 5. VALIDATION TEST SUITE
# ============================================================
def _t(desc: str, fn, should_pass: bool) -> None:
    try:
        fn()
        ok = should_pass
    except (ValidationError, KeyError, TypeError, ValueError):
        ok = not should_pass
    print(f"  {'✅' if ok else '❌ FAIL'} {desc}")


def run_validation_tests() -> None:
    print("=" * 60)
    print("VALIDATION TESTS")
    print("=" * 60)

    print("\n[Score] invalid inputs must be rejected:")
    for bad in [-1, -0.01, 100.01, 101, 150, "85", None, True, False,
                float("nan"), float("inf"), float("-inf"), [90], {"v": 90}, complex(1, 0)]:
        _t(f"reject score {bad!r}", lambda b=bad: validate_score(b), should_pass=False)

    print("\n[Score] boundary / valid inputs must be accepted:")
    for good in [0, 0.0, 55, 60, 99.99, 100, 100.0]:
        _t(f"accept score {good!r}", lambda g=good: validate_score(g), should_pass=True)

    print("\n[Weight] invalid inputs must be rejected:")
    for bad in [-1, -0.001, 0, 0.0, 1.0001, 1.5, 2, "0.5", None, True, False,
                float("nan"), float("inf"), float("-inf"), [0.5], {"w": 0.5}]:
        _t(f"reject weight {bad!r}", lambda b=bad: validate_weight(b), should_pass=False)

    print("\n[Weight] boundary / valid inputs must be accepted:")
    for good in [0.0001, 0.25, 0.5, 0.9999, 1, 1.0]:
        _t(f"accept weight {good!r}", lambda g=good: validate_weight(g), should_pass=True)

    print("\n[Weight sum] enforcement:")
    sum_cases = [
        ({"Math": 0.5, "Sci": 0.5}, True),
        ({"Math": 0.3, "Sci": 0.3, "Eng": 0.4}, True),
        ({"Math": 0.25, "Sci": 0.25, "Eng": 0.25, "Hist": 0.25}, True),
        ({"Math": 0.3, "Sci": 0.3}, False),                 # 0.6
        ({"Math": 0.5, "Sci": 0.6}, False),                 # 1.1
        ({"Math": 1.0}, True),
        ({}, False),
        ({"Math": 0.333333, "Sci": 0.333333, "Eng": 0.333334}, True),
    ]
    for wts, should_pass in sum_cases:
        _t(f"weights {wts} → {'accept' if should_pass else 'reject'}",
           lambda w=wts: validate_weights_sum(w), should_pass=should_pass)

    print("\n[End-to-end] analyzer rejects bad input:")
    a = StudentPerformanceAnalyzer()
    a.add_student("X1", "Test")
    for bad in [-5, 105, "90", None, True, float("nan"), float("inf")]:
        _t(f"record_score rejects {bad!r}",
           lambda b=bad: a.record_score("X1", "Math", b), should_pass=False)
    _t("set_weights rejects sum=0.8",
       lambda: a.set_weights("X1", {"Math": 0.4, "Sci": 0.4}), should_pass=False)
    _t("set_weights rejects sum=1.1",
       lambda: a.set_weights("X1", {"Math": 0.6, "Sci": 0.5}), should_pass=False)
    _t("set_weights rejects weight=0",
       lambda: a.set_weights("X1", {"Math": 0.0, "Sci": 1.0}), should_pass=False)
    _t("set_weights rejects weight=1.5",
       lambda: a.set_weights("X1", {"Math": 1.5, "Sci": -0.5}), should_pass=False)

    print("\n[End-to-end] analyzer accepts valid input:")
    _t("set_weights {0.6, 0.4} accepted",
       lambda: a.set_weights("X1", {"Math": 0.6, "Sci": 0.4}), should_pass=True)
    _t("record_score 90 accepted",
       lambda: a.record_score("X1", "Math", 90), should_pass=True)
    _t("record_score 80 accepted",
       lambda: a.record_score("X1", "Sci", 80), should_pass=True)

    s = a.get_student("X1")
    assert math.isclose(s.average(), 90 * 0.6 + 80 * 0.4, rel_tol=1e-9)
    assert s.letter_grade() == "A"
    print(f"\n  ✅ weighted avg = {s.average():.2f} (expected 86.00), grade = {s.letter_grade()}")


# ============================================================
# 6. DEMO
# ============================================================
def run_demo() -> None:
    print("\n" + "=" * 60)
    print("FULL DEMO")
    print("=" * 60)

    analyzer = StudentPerformanceAnalyzer()
    weights = {"Math": 0.30, "Science": 0.30, "English": 0.25, "History": 0.15}  # sums to 1.0

    sample = [
        ("S001", "Alice Johnson", {"Math": 95, "Science": 92, "English": 88, "History": 90}),
        ("S002", "Bob Smith",     {"Math": 72, "Science": 68, "English": 75, "History": 70}),
        ("S003", "Carol White",   {"Math": 88, "Science": 91, "English": 85, "History": 89}),
        ("S004", "David Brown",   {"Math": 55, "Science": 58, "English": 62, "History": 50}),
        ("S005", "Eva Green",     {"Math": 78, "Science": 82, "English": 80, "History": 76}),
        ("S006", "Frank Miller",  {"Math": 45, "Science": 52, "English": 48, "History": 55}),
    ]

    for sid, name, scores in sample:
        analyzer.add_student(sid, name)
        for subj, sc in scores.items():
            analyzer.record_score(sid, subj, sc)
        analyzer.set_weights(sid, weights)  # validated: sums to 1.0

    print(analyzer.generate_report())

    analyzer.save("students.json")
    print("\nSaved → students.json")

    reloaded = StudentPerformanceAnalyzer()
    reloaded.load("students.json")
    print(f"Reloaded {len(reloaded.students)} students; class avg = {reloaded.class_average():.2f}")


if __name__ == "__main__":
    run_validation_tests()
    run_demo()