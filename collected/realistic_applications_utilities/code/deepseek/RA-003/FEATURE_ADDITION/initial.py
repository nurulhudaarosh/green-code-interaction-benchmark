import json
import math
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 1. VALIDATION LAYER
# ============================================================
class ValidationError(ValueError):
    """Raised when a score, weight, name, or subject fails validation."""


def validate_score(value, *, label: str = "Score") -> float:
    """Score must be a finite real number in [0, 100]."""
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
    """Weight must be a finite real number in (0, 1]."""
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
        if not isinstance(weights, dict):
            raise ValidationError(f"weights must be a dict, got {type(weights).__name__}")
        clean: Dict[str, float] = {}
        for subj, w in weights.items():
            clean[validate_nonempty_str(subj, label="Subject")] = validate_weight(w)
        validate_weights_sum(clean)
        self.weights = clean

    def has_complete_weights(self) -> bool:
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

    # -------- deterministic keys --------
    def min_score(self) -> float:
        return min(self.scores.values()) if self.scores else 0.0

    def max_score(self) -> float:
        return max(self.scores.values()) if self.scores else 0.0

    def subject_count(self) -> int:
        return len(self.scores)

    def sorted_scores_desc(self) -> Tuple[float, ...]:
        """Lexicographically comparable score signature (descending)."""
        return tuple(sorted(self.scores.values(), reverse=True))

    def rank_key(self) -> Tuple:
        """Deterministic ranking key (all components resolve ties).

        Priority (higher = better):
          1. average
          2. min score            (rewards a student with no weak subject)
          3. number of subjects   (rewards broader coverage)
          4. sorted score vector  (lexicographic comparison, descending)
          5. student_id           (final absolute tiebreaker — unique)
        All sort directions are uniform so we can just reverse-sort the tuple.
        """
        return (
            round(self.average(), 6),   # rounding to 6dp keeps float ties stable
            self.min_score(),
            self.subject_count(),
            self.sorted_scores_desc(),
            # Final tiebreaker: invert id ordering by using a *negative* key?
            # We can't negate a string — instead we sort ascending on id later.
        )


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

    # ---------- Deterministic ranking ----------
    def _ranking_sorted(self) -> List[Student]:
        """Return students sorted deterministically, best → worst.

        Sort direction:
          * average, min_score, subject_count, sorted_scores_desc → DESCENDING
          * student_id                                            → ASCENDING
        Achieved by sorting on the negative of numeric keys is ugly; instead
        we do a two-pass stable sort: first ascending by id, then descending
        by the composite key. Python's sort is stable, so the id order is
        preserved for the exact ties that survive the composite key.
        """
        by_id = sorted(self.students.values(), key=lambda s: s.student_id)
        return sorted(by_id, key=lambda s: s.rank_key(), reverse=True)

    def rank_students(self) -> List[Tuple[int, str, str, float, str]]:
        """Returns (rank, student_id, name, average, letter) with dense ranks.

        Ties receive the SAME rank; the next distinct rank is incremented by 1
        per distinct key (dense ranking). Because the composite key is unique
        only when student_id differs, we treat students with identical
        composites as tied for the *reported* rank, but they remain in a
        deterministic order thanks to the id tiebreaker.
        """
        ordered = self._ranking_sorted()
        result: List[Tuple[int, str, str, float, str]] = []
        prev_key: Optional[Tuple] = None
        prev_rank = 0
        for idx, s in enumerate(ordered, start=1):
            key = s.rank_key()
            if prev_key is None or key != prev_key:
                prev_rank = idx        # dense rank: first of a new key group
            prev_key = key
            result.append((prev_rank, s.student_id, s.name,
                           round(s.average(), 2), s.letter_grade()))
        return result

    def top_performers(self, n: int = 3) -> List[Tuple[str, float]]:
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            raise ValidationError(f"n must be a non-negative int, got {n!r}")
        return [(s.name, round(s.average(), 2)) for s in self._ranking_sorted()[:n]]

    def at_risk_students(self, threshold: float = 60.0) -> List[Tuple[str, float]]:
        t = validate_score(threshold, label="threshold")
        ordered = self._ranking_sorted()  # deterministic order even for at-risk list
        return [(s.name, round(s.average(), 2)) for s in ordered if s.average() < t]

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

        L.append("--- Rankings (deterministic; ties broken by min, count, "
                 "score vector, then student_id) ---")
        for rank, sid, name, avg, grade in self.rank_students():
            L.append(f"  {rank:>2}. [{sid}] {name:<20} Avg: {avg:>6.2f}  Grade: {grade}")

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
            json.dump(payload, f, indent=2, sort_keys=True)  # deterministic file

    def load(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        new_students: Dict[str, Student] = {}
        for sid, info in data.items():
            s = Student(validate_nonempty_str(sid, label="student_id"),
                        validate_nonempty_str(info["name"], label="name"))
            for subj, sc in info.get("scores", {}).items():
                s.add_score(subj, sc)
            if info.get("weights"):
                s.set_weights(info["weights"])
            new_students[s.student_id] = s
        self.students = new_students


# ============================================================
# 5. DETERMINISM TESTS
# ============================================================
def run_determinism_tests() -> None:
    print("=" * 60)
    print("DETERMINISTIC RANKING TESTS")
    print("=" * 60)

    # Helper: build a fresh analyzer with a given set of students.
    def build(entries: List[Tuple[str, str, Dict[str, float]]]) -> StudentPerformanceAnalyzer:
        a = StudentPerformanceAnalyzer()
        for sid, name, scores in entries:
            a.add_student(sid, name)
            for subj, sc in scores.items():
                a.record_score(sid, subj, sc)
        return a

    # ---- Test 1: exact ties, insertion order varies → same result ----
    print("\n[1] Insertion order must not affect ranking")
    rows = [
        ("S010", "Zoe",   {"Math": 80, "Sci": 80}),
        ("S002", "Anna",  {"Math": 80, "Sci": 80}),
        ("S005", "Mike",  {"Math": 80, "Sci": 80}),
    ]
    a1 = build(rows)
    a2 = build(list(reversed(rows)))
    assert a1.rank_students() == a2.rank_students()
    print("  ✅ identical output for both insertion orders")
    for r in a1.rank_students():
        print(f"     rank {r[0]} → id={r[1]} name={r[2]} avg={r[3]}")

    # ---- Test 2: same average, different min → min wins ----
    print("\n[2] Same average → higher minimum score ranks first")
    a = build([
        ("S1", "Low-Min",  {"Math": 100, "Sci": 60}),   # avg 80, min 60
        ("S2", "High-Min", {"Math": 80,  "Sci": 80}),   # avg 80, min 80
    ])
    order = [sid for _, sid, *_ in a.rank_students()]
    assert order == ["S2", "S1"], order
    print(f"  ✅ order = {order}  (High-Min before Low-Min)")

    # ---- Test 3: same avg & same min, more subjects ranks first ----
    print("\n[3] Same avg & min → more subjects ranks first")
    a = build([
        ("S1", "TwoSubj",   {"Math": 80, "Sci": 80}),                    # 2 subj
        ("S2", "ThreeSubj", {"Math": 80, "Sci": 80, "Eng": 80}),         # 3 subj
    ])
    order = [sid for _, sid, *_ in a.rank_students()]
    assert order == ["S2", "S1"], order
    print(f"  ✅ order = {order}  (ThreeSubj before TwoSubj)")

    # ---- Test 4: same avg/min/count → lexicographic score vector ----
    print("\n[4] Same avg/min/count → descending score vector decides")
    a = build([
        ("S1", "Flat",  {"A": 80, "B": 80, "C": 80}),   # (80,80,80)
        ("S2", "Peaked",{"A": 90, "B": 80, "C": 70}),   # (90,80,70) avg 80, min 70
    ])
    # Note: Peaked has min 70 < Flat's min 80 → Flat wins by rule #2
    order = [sid for _, sid, *_ in a.rank_students()]
    assert order == ["S1", "S2"], order
    print(f"  ✅ order = {order}  (min rule dominates before vector rule)")

    # ---- Test 5: absolutely identical students → id tiebreaker ----
    print("\n[5] Fully identical metrics → student_id ascending decides order")
    a = build([
        ("S9", "Twin9", {"Math": 70, "Sci": 70}),
        ("S1", "Twin1", {"Math": 70, "Sci": 70}),
        ("S5", "Twin5", {"Math": 70, "Sci": 70}),
    ])
    order = [sid for _, sid, *_ in a.rank_students()]
    assert order == ["S1", "S5", "S9"], order
    print(f"  ✅ order = {order}  (ids ascending on exact ties)")

    # ---- Test 6: dense ranks for exact ties ----
    print("\n[6] Exact ties share the same rank (dense ranking)")
    a = build([
        ("S1", "Top",   {"Math": 90, "Sci": 90}),
        ("S2", "TieA",  {"Math": 70, "Sci": 70}),
        ("S3", "TieB",  {"Math": 70, "Sci": 70}),
        ("S4", "Last",  {"Math": 50, "Sci": 50}),
    ])
    ranks = [(sid, rank) for rank, sid, *_ in a.rank_students()]
    assert ranks == [("S1", 1), ("S2", 2), ("S3", 2), ("S4", 4)], ranks
    print(f"  ✅ ranks = {ranks}")

    # ---- Test 7: repeat runs give byte-identical report ----
    print("\n[7] Repeated runs produce identical reports")
    a = build([
        ("S1", "A", {"Math": 88, "Sci": 92, "Eng": 85}),
        ("S2", "B", {"Math": 88, "Sci": 92, "Eng": 85}),
        ("S3", "C", {"Math": 60, "Sci": 70, "Eng": 80}),
        ("S4", "D", {"Math": 90, "Sci": 90, "Eng": 90}),
    ])
    reports = {a.generate_report() for _ in range(5)}
    assert len(reports) == 1
    print("  ✅ 5 runs → 1 unique report string")

    print("\nAll determinism tests passed ✅")


# ============================================================
# 6. DEMO
# ============================================================
def run_demo() -> None:
    print("\n" + "=" * 60)
    print("FULL DEMO")
    print("=" * 60)

    analyzer = StudentPerformanceAnalyzer()
    weights = {"Math": 0.30, "Science": 0.30, "English": 0.25, "History": 0.15}

    sample = [
        ("S001", "Alice Johnson", {"Math": 95, "Science": 92, "English": 88, "History": 90}),
        ("S002", "Bob Smith",     {"Math": 72, "Science": 68, "English": 75, "History": 70}),
        ("S003", "Carol White",   {"Math": 88, "Science": 91, "English": 85, "History": 89}),
        ("S004", "David Brown",   {"Math": 55, "Science": 58, "English": 62, "History": 50}),
        ("S005", "Eva Green",     {"Math": 78, "Science": 82, "English": 80, "History": 76}),
        ("S006", "Frank Miller",  {"Math": 45, "Science": 52, "English": 48, "History": 55}),
        # Two deliberately identical students to show deterministic tiebreaking
        ("S007", "Twin Alpha",    {"Math": 85, "Science": 85, "English": 85, "History": 85}),
        ("S008", "Twin Beta",     {"Math": 85, "Science": 85, "English": 85, "History": 85}),
    ]

    for sid, name, scores in sample:
        analyzer.add_student(sid, name)
        for subj, sc in scores.items():
            analyzer.record_score(sid, subj, sc)
        analyzer.set_weights(sid, weights)

    print(analyzer.generate_report())

    analyzer.save("students.json")
    print("\nSaved → students.json")

    reloaded = StudentPerformanceAnalyzer()
    reloaded.load("students.json")
    print(f"Reloaded {len(reloaded.students)} students; class avg = "
          f"{reloaded.class_average():.2f}")

    # Prove reload preserves ranking
    assert reloaded.rank_students() == analyzer.rank_students()
    print("✅ Ranking identical after save/load round-trip")


if __name__ == "__main__":
    run_determinism_tests()
    run_demo()