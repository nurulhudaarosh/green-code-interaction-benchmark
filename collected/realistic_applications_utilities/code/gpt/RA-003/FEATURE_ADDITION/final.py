class StudentPerformanceAnalyzer:
    def __init__(self, subjects):
        self.subjects = subjects

    def _validate_score(self, score):
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError("Score must be a number.")
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100.")
        return float(score)

    def _validate_weight(self, weight):
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ValueError("Weight must be a number.")
        if weight <= 0:
            raise ValueError("Weight must be greater than 0.")
        return float(weight)

    def calculate_weighted_average(self, scores):
        if not scores:
            return 0.0

        if len(scores) != len(self.subjects):
            raise ValueError("Scores and subjects must have the same length.")

        weighted_total = 0.0
        total_weight = 0.0

        for score_data in scores:
            if isinstance(score_data, dict):
                score = score_data.get("score")
                weight = score_data.get("weight", 1)
            else:
                score = score_data
                weight = 1

            score = self._validate_score(score)
            weight = self._validate_weight(weight)

            weighted_total += score * weight
            total_weight += weight

        return weighted_total / total_weight

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
        elif average >= 40:
            return "D"
        return "F"

    def analyze(self, student_name, scores):
        average = self.calculate_weighted_average(scores)

        return {
            "name": student_name,
            "average": round(average, 2),
            "grade": self.get_grade(average),
            "status": "Pass" if average >= 40 else "Fail"
        }

    def rank_students(self, students):
        """
        students = [
            {"name": "Alice", "scores": [...]},
            {"name": "Bob", "scores": [...]},
            ...
        ]

        Ranking rules:
        1. Higher average ranks higher.
        2. If averages are equal, names are used alphabetically.
        3. Ranking is therefore deterministic.
        """

        results = []

        for student in students:
            if not isinstance(student, dict):
                raise ValueError("Each student must be a dictionary.")

            if "name" not in student or "scores" not in student:
                raise ValueError("Each student must contain name and scores.")

            result = self.analyze(student["name"], student["scores"])
            results.append(result)

        # Higher average first; alphabetical name breaks ties.
        results.sort(key=lambda x: (-x["average"], x["name"].casefold()))

        # Assign deterministic ranks.
        for position, result in enumerate(results, start=1):
            result["rank"] = position

        return results


# Example
subjects = ["Math", "Physics", "English"]

analyzer = StudentPerformanceAnalyzer(subjects)

students = [
    {
        "name": "Bob",
        "scores": [
            {"score": 80, "weight": 2},
            {"score": 70, "weight": 1},
            {"score": 90, "weight": 1}
        ]
    },
    {
        "name": "Alice",
        "scores": [
            {"score": 85, "weight": 2},
            {"score": 75, "weight": 1},
            {"score": 80, "weight": 1}
        ]
    },
    {
        "name": "Charlie",
        "scores": [
            {"score": 90, "weight": 2},
            {"score": 70, "weight": 1},
            {"score": 80, "weight": 1}
        ]
    }
]

ranked = analyzer.rank_students(students)

for student in ranked:
    print(
        f"Rank {student['rank']}: "
        f"{student['name']} - "
        f"{student['average']} ({student['grade']})"
    )