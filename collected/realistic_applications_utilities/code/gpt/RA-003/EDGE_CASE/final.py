class StudentPerformanceAnalyzer:
    PASS_MARK = 40

    def __init__(self, subjects):
        if not isinstance(subjects, list):
            raise ValueError("Subjects must be a list.")
        self.subjects = subjects

    def _validate_score(self, score):
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("Score must be a number.")
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100.")
        return float(score)

    def _validate_weight(self, weight):
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError("Weight must be a number.")
        if weight <= 0:
            raise ValueError("Weight must be greater than 0.")
        return float(weight)

    def calculate_weighted_average(self, assessments):
        if assessments is None or assessments == []:
            return 0.0

        if not isinstance(assessments, list):
            raise ValueError("Assessments must be a list.")

        if len(assessments) != len(self.subjects):
            raise ValueError("Number of assessments must match subjects.")

        total = 0.0
        total_weight = 0.0

        for assessment in assessments:
            # Reject malformed assessment structures.
            if isinstance(assessment, dict):
                if "score" not in assessment:
                    raise ValueError("Malformed assessment: missing score.")

                # Only score and optional weight are accepted.
                if any(key not in {"score", "weight"} for key in assessment):
                    raise ValueError("Malformed assessment.")

                score = assessment["score"]
                weight = assessment.get("weight", 1)
            elif isinstance(assessment, (int, float)) and not isinstance(assessment, bool):
                score = assessment
                weight = 1
            else:
                raise ValueError("Malformed assessment.")

            score = self._validate_score(score)
            weight = self._validate_weight(weight)

            total += score * weight
            total_weight += weight

        return total / total_weight

    def get_grade(self, average):
        average = self._validate_score(average)

        if average >= 80:
            return "A+"
        elif average >= 70:
            return "A"
        elif average >= 60:
            return "B"
        elif average >= 50:
            return "C"
        elif average >= self.PASS_MARK:
            return "D"
        return "F"

    def analyze(self, student_name, assessments):
        if not isinstance(student_name, str) or not student_name.strip():
            raise ValueError("Student name must be a non-empty string.")

        average = self.calculate_weighted_average(assessments)

        return {
            "name": student_name,
            "average": round(average, 2),
            "grade": self.get_grade(average),
            # Exactly 40 is a pass.
            "status": "Pass" if average >= self.PASS_MARK else "Fail"
        }

    def rank_students(self, students):
        if students is None or students == []:
            return []

        if not isinstance(students, list):
            raise ValueError("Students must be a list.")

        results = []

        for student in students:
            if not isinstance(student, dict):
                raise ValueError("Malformed student record.")

            if set(student.keys()) != {"name", "scores"}:
                raise ValueError(
                    "Each student must contain only name and scores."
                )

            result = self.analyze(student["name"], student["scores"])
            results.append(result)

        # Deterministic ranking:
        # 1. Higher average first.
        # 2. Alphabetical name breaks ties.
        results.sort(key=lambda x: (-x["average"], x["name"].casefold()))

        for rank, result in enumerate(results, start=1):
            result["rank"] = rank

        return results


# Example / edge-case tests
subjects = ["Math", "Physics", "English"]
analyzer = StudentPerformanceAnalyzer(subjects)

# Empty data
assert analyzer.rank_students([]) == []
assert analyzer.calculate_weighted_average([]) == 0.0

# Exact pass mark: 40 is PASS
result = analyzer.analyze("Alice", [40, 40, 40])
assert result["average"] == 40.0
assert result["status"] == "Pass"
assert result["grade"] == "D"

# Tie: same average -> alphabetical name determines order
students = [
    {"name": "Charlie", "scores": [80, 80, 80]},
    {"name": "Alice", "scores": [80, 80, 80]},
    {"name": "Bob", "scores": [80, 80, 80]}
]

ranked = analyzer.rank_students(students)

assert [s["name"] for s in ranked] == ["Alice", "Bob", "Charlie"]
assert [s["rank"] for s in ranked] == [1, 2, 3]

# Malformed assessments
invalid_cases = [
    [{"weight": 2}, 70, 80],              # missing score
    [{"score": 50, "foo": 2}, 70, 80],    # unknown field
    [{"score": "50"}, 70, 80],            # non-numeric score
    [{"score": -1}, 70, 80],              # invalid score
    [{"score": 101}, 70, 80],             # invalid score
    [{"score": 80, "weight": 0}, 70, 80], # invalid weight
    [{"score": 80, "weight": -1}, 70, 80],# invalid weight
    [None, 70, 80]                        # malformed assessment
]

for invalid in invalid_cases:
    try:
        analyzer.calculate_weighted_average(invalid)
        raise AssertionError("Expected ValueError was not raised.")
    except ValueError:
        pass