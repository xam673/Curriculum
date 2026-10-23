from app.models import Category
from app.services.grade_rules import calculate_gpax, is_passing
from app.services.progress import PassedCourse, calculate_progress


def test_passing_grades():
    assert is_passing("D") and is_passing("S")
    assert not is_passing("F") and not is_passing("W") and not is_passing("U")


def test_gpax_ignores_non_letter_grades():
    # A(3) + C(3) = (12 + 6) / 6 = 3.0 ; S and W are ignored
    assert calculate_gpax([("A", 3), ("C", 3), ("S", 1), ("W", 3)]) == 3.0


def test_gpax_none_without_letter_grades():
    assert calculate_gpax([("S", 1)]) is None


def test_progress_caps_extra_credits():
    cats = [Category(id=1, name="Core", required_credits=6),
            Category(id=2, name="Elective", required_credits=6)]
    passed = [PassedCourse("A", 3, 1), PassedCourse("B", 3, 1),
              PassedCourse("C", 3, 1), PassedCourse("D", 3, 2)]
    result = calculate_progress(cats, passed)
    core = result["categories"][0]
    assert core["earned_credits"] == 9
    assert core["percent"] == 100.0
    assert result["overall_percent"] == 75.0     # (6 + 3) / 12


def test_course_without_category_is_unassigned():
    cats = [Category(id=1, name="Core", required_credits=6)]
    result = calculate_progress(cats, [PassedCourse("X", 3, None)])
    assert result["unassigned_courses"] == ["X"]