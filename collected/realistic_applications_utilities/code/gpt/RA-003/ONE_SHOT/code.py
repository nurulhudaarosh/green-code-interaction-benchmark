from collections import defaultdict
from statistics import mean

class StudentPerformanceAnalyzer:
    def __init__(self, students=None):
        self.students = students or []

    def _valid_student(self, student):
        return (
            isinstance(student, dict)
            and student.get("id") is not None
            and isinstance(student.get("scores", {}), dict)
        )

    def add_student(self, student_id, name, scores):
        if student_id is None or not isinstance(scores, dict):
            return False
        if any(s.get("id") == student_id for s in self.students):
            return False

        valid_scores = {}
        for subject, score in scores.items():
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                if 0 <= score <= 100:
                    valid_scores[subject] = score

        self.students.append({
            "id": student_id,
            "name": name,
            "scores": valid_scores
        })
        return True

    def remove_duplicate_students(self):
        seen = set()
        unique = []

        for student in self.students:
            if not self._valid_student(student):
                continue

            sid = student["id"]
            if sid not in seen:
                seen.add(sid)
                unique.append(student)

        self.students = unique
        return self.students

    def average_score(self, student_id):
        student = self.get_student(student_id)
        if not student or not student["scores"]:
            return 0.0

        return mean(student["scores"].values())

    def get_student(self, student_id):
        for student in self.students:
            if self._valid_student(student) and student["id"] == student_id:
                return student
        return None

    def grade(self, score):
        if score >= 80:
            return "A+"
        elif score >= 70:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 40:
            return "D"
        return "F"

    def performance_report(self, student_id):
        student = self.get_student(student_id)
        if not student:
            return None

        scores = student["scores"]
        average = self.average_score(student_id)

        return {
            "id": student["id"],
            "name": student.get("name", ""),
            "average": round(average, 2),
            "grade": self.grade(average),
            "subjects": dict(scores),
            "highest_subject": max(scores, key=scores.get) if scores else None,
            "lowest_subject": min(scores, key=scores.get) if scores else None,
            "passed": all(score >= 40 for score in scores.values()) if scores else False
        }

    def all_reports(self):
        self.remove_duplicate_students()
        return [
            self.performance_report(student["id"])
            for student in self.students
            if self._valid_student(student)
        ]

    def class_average(self):
        averages = [
            self.average_score(student["id"])
            for student in self.students
            if self._valid_student(student) and student["scores"]
        ]
        return round(mean(averages), 2) if averages else 0.0

    def subject_averages(self):
        subject_scores = defaultdict(list)

        for student in self.students:
            if not self._valid_student(student):
                continue
            for subject, score in student["scores"].items():
                if isinstance(score, (int, float)) and 0 <= score <= 100:
                    subject_scores[subject].append(score)

        return {
            subject: round(mean(scores), 2)
            for subject, scores in subject_scores.items()
        }

    def top_students(self, n=3):
        if n <= 0:
            return []

        ranked = []
        for student in self.students:
            if not self._valid_student(student) or not student["scores"]:
                continue
            ranked.append(
                (student["id"], student.get("name", ""), self.average_score(student["id"]))
            )

        ranked.sort(key=lambda x: (-x[2], str(x[0])))
        return [
            {
                "id": sid,
                "name": name,
                "average": round(avg, 2)
            }
            for sid, name, avg in ranked[:n]
        ]

    def low_performers(self, threshold=40):
        if threshold < 0:
            threshold = 0
        if threshold > 100:
            threshold = 100

        result = []
        for student in self.students:
            if not self._valid_student(student):
                continue

            weak_subjects = {
                subject: score
                for subject, score in student["scores"].items()
                if score < threshold
            }

            if weak_subjects:
                result.append({
                    "id": student["id"],
                    "name": student.get("name", ""),
                    "subjects": weak_subjects,
                    "average": round(self.average_score(student["id"]), 2)
                })

        return result

    def subject_topper(self, subject):
        candidates = []

        for student in self.students:
            if not self._valid_student(student):
                continue

            score = student["scores"].get(subject)
            if isinstance(score, (int, float)):
                candidates.append((
                    score,
                    student["id"],
                    student.get("name", "")
                ))

        if not candidates:
            return None

        score, sid, name = max(candidates, key=lambda x: (x[0], str(x[1])))
        return {
            "id": sid,
            "name": name,
            "subject": subject,
            "score": score
        }

    def class_summary(self):
        self.remove_duplicate_students()

        valid_students = [
            s for s in self.students
            if self._valid_student(s)
        ]

        averages = [
            self.average_score(s["id"])
            for s in valid_students
            if s["scores"]
        ]

        passed = sum(
            1 for s in valid_students
            if s["scores"] and all(score >= 40 for score in s["scores"].values())
        )

        failed = sum(
            1 for s in valid_students
            if s["scores"] and any(score < 40 for score in s["scores"].values())
        )

        return {
            "total_students": len(valid_students),
            "students_with_scores": len(averages),
            "class_average": round(mean(averages), 2) if averages else 0.0,
            "highest_average": round(max(averages), 2) if averages else 0.0,
            "lowest_average": round(min(averages), 2) if averages else 0.0,
            "passed_students": passed,
            "failed_students": failed,
            "subject_averages": self.subject_averages()
        }


# Example usage
students = [
    {
        "id": 1,
        "name": "Alice",
        "scores": {"Math": 85, "English": 78, "Science": 92}
    },
    {
        "id": 2,
        "name": "Bob",
        "scores": {"Math": 55, "English": 62, "Science": 48}
    },
    {
        "id": 3,
        "name": "Charlie",
        "scores": {"Math": 95, "English": 88, "Science": 91}
    },
    {
        "id": 2,  # duplicate ID; will be removed
        "name": "Duplicate Bob",
        "scores": {"Math": 70}
    }
]

analyzer = StudentPerformanceAnalyzer(students)

print("Reports:", analyzer.all_reports())
print("Class summary:", analyzer.class_summary())
print("Top students:", analyzer.top_students(3))
print("Low performers:", analyzer.low_performers(50))
print("Math topper:", analyzer.subject_topper("Math"))