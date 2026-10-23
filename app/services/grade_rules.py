# Chula grade scale (FR-06). Only these letters count toward GPAX.
GRADE_POINTS = {"A": 4.0, "B+": 3.5, "B": 3.0, "C+": 2.5,
                "C": 2.0, "D+": 1.5, "D": 1.0, "F": 0.0}

# Grades that earn credits toward graduation
PASSING_GRADES = {"A", "B+", "B", "C+", "C", "D+", "D", "S"}


def is_passing(grade: str) -> bool:
    return grade in PASSING_GRADES


def calculate_gpax(records: list[tuple[str, int]]) -> float | None:
    """records = [(grade, credits), ...]. S/U/W/V are ignored.
    Returns None if the student has no letter-graded courses yet."""
    total_points = 0.0
    total_credits = 0
    for grade, credits in records:
        if grade in GRADE_POINTS:
            total_points += GRADE_POINTS[grade] * credits
            total_credits += credits
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)