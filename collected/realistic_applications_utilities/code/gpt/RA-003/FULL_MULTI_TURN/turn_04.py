# Turn 4: Handle empty and boundary cases

def add_ranking(results):
    """Safely rank students, including empty and boundary inputs."""
    if results is None or len(results) == 0:
        return []

    # Preserve exact scores, including 0 and the pass boundary (40).
    for student in results:
        if "score" not in student:
            student["score"] = 0.0
        student["score"] = float(student["score"])

    # Higher score first; names provide deterministic tie-breaking.
    results.sort(key=lambda x: (-x["score"], str(x.get("name", ""))))

    for rank, student in enumerate(results, start=1):
        student["rank"] = rank

    return results


def analyze_students(students, assessments):
    """Handle empty data and boundary values safely."""
    if not students:
        return []

    if not assessments:
        return [
            {"name": student.get("name", ""), "score": 0.0,
             "passed": False, "rank": 1}
            for student in students
        ]

    results = []

    for student in students:
        total = 0.0

        for assessment in assessments:
            max_score = float(assessment["max_score"])
            score = float(student.get(assessment["name"], 0))

            # Boundary-safe score handling.
            score = max(0.0, min(score, max_score))

            total += (score / max_score) * float(assessment["weight"])

        total = round(total, 2)

        results.append({
            "name": student.get("name", ""),
            "score": total,
            "passed": total >= 40.0
        })

    return add_ranking(results)