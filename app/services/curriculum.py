from sqlalchemy import select
from sqlalchemy.orm import Session
from app.exceptions import AppError
from app.models import Category, CurriculumCourse, User

FREE_ELECTIVE = "Elective"   # courses not listed in the curriculum count here


def require_curriculum(student: User) -> int:
    if student.curriculum_id is None:
        raise AppError("Student is not assigned to a curriculum yet")
    return student.curriculum_id


def get_categories(db: Session, curriculum_id: int) -> list[Category]:
    stmt = (select(Category).where(Category.curriculum_id == curriculum_id)
            .order_by(Category.id))
    return list(db.scalars(stmt).all())


def get_eligible_map(db: Session, curriculum_id: int) -> dict[str, list[int]]:
    """{course_code: [category_id, ...]} for one curriculum."""
    stmt = (select(CurriculumCourse.course_code, CurriculumCourse.category_id)
            .where(CurriculumCourse.curriculum_id == curriculum_id)
            .order_by(CurriculumCourse.category_id))
    mapping: dict[str, list[int]] = {}
    for code, cat_id in db.execute(stmt).all():
        mapping.setdefault(code, []).append(cat_id)
    return mapping


def eligible_ids(mapping: dict[str, list[int]], course_code: str,
                 categories: list[Category]) -> list[int]:
    """Categories this course may count toward."""
    if course_code in mapping:
        return mapping[course_code]
    free = next((c.id for c in categories if c.name == FREE_ELECTIVE), None)
    return [free] if free is not None else []


def effective_category(chosen_id: int | None, allowed: list[int]) -> int | None:
    """The student's choice if it's valid (FR-04), otherwise the first allowed category."""
    if chosen_id in allowed:
        return chosen_id
    return allowed[0] if allowed else None