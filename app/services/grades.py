from sqlalchemy import select
from sqlalchemy.orm import Session
from app.exceptions import AppError, ConflictError, NotFoundError
from app.models import Category, Course, GradeRecord, User
from app.services.curriculum import (effective_category, eligible_ids, get_categories,
                                     get_eligible_map, require_curriculum)


def _describe(db: Session, student: User, rows: list[tuple[GradeRecord, Course]]) -> list[dict]:
    """Adds course name, credits, and the category each record counts toward."""
    cur_id = require_curriculum(student)
    categories = get_categories(db, cur_id)
    names = {c.id: c.name for c in categories}
    mapping = get_eligible_map(db, cur_id)
    out = []
    for rec, course in rows:
        cat_id = effective_category(rec.category_id,
                                    eligible_ids(mapping, course.code, categories))
        out.append({
            "id": rec.id, "course_code": course.code, "course_name": course.name,
            "credits": course.credits, "academic_year": rec.academic_year,
            "term": rec.term, "grade": rec.grade,
            "category_id": cat_id, "category_name": names.get(cat_id),
        })
    return out


def _get_own_record(db: Session, student: User, record_id: int) -> GradeRecord:
    rec = db.get(GradeRecord, record_id)
    if not rec or rec.student_id != student.id:   # never reveal other students' data
        raise NotFoundError("Grade record not found")
    return rec


# ---------- FR-06 ----------
def list_grades(db: Session, student: User) -> list[dict]:
    stmt = (select(GradeRecord, Course)
            .join(Course, GradeRecord.course_code == Course.code)
            .where(GradeRecord.student_id == student.id)
            .order_by(GradeRecord.academic_year, GradeRecord.term, Course.code))
    return _describe(db, student, db.execute(stmt).all())


def add_grade(db: Session, student: User, course_code: str,
              academic_year: int, term: int, grade: str) -> dict:
    course = db.get(Course, course_code)   # course must exist in the central DB
    if not course:
        raise NotFoundError(f"Course {course_code} not found")

    duplicate = db.scalar(select(GradeRecord).where(
        GradeRecord.student_id == student.id, GradeRecord.course_code == course_code,
        GradeRecord.academic_year == academic_year, GradeRecord.term == term))
    if duplicate:
        raise ConflictError("This course is already recorded for that semester")

    # On a retake, keep the category the student chose before
    previous_choice = db.scalar(select(GradeRecord.category_id).where(
        GradeRecord.student_id == student.id, GradeRecord.course_code == course_code,
        GradeRecord.category_id.is_not(None)).limit(1))

    rec = GradeRecord(student_id=student.id, course_code=course_code,
                      academic_year=academic_year, term=term, grade=grade,
                      category_id=previous_choice)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _describe(db, student, [(rec, course)])[0]


def update_grade(db: Session, student: User, record_id: int, grade: str) -> dict:
    rec = _get_own_record(db, student, record_id)
    rec.grade = grade
    db.commit()
    return _describe(db, student, [(rec, db.get(Course, rec.course_code))])[0]


def delete_grade(db: Session, student: User, record_id: int) -> None:
    rec = _get_own_record(db, student, record_id)
    db.delete(rec)
    db.commit()


# ---------- FR-04 ----------
def get_eligible_categories(db: Session, student: User, course_code: str) -> list[Category]:
    cur_id = require_curriculum(student)
    categories = get_categories(db, cur_id)
    allowed = eligible_ids(get_eligible_map(db, cur_id), course_code, categories)
    return [c for c in categories if c.id in allowed]


def assign_category(db: Session, student: User, course_code: str, category_id: int) -> None:
    allowed = [c.id for c in get_eligible_categories(db, student, course_code)]
    if category_id not in allowed:
        raise AppError("This course cannot be counted toward that category")

    records = db.scalars(select(GradeRecord).where(
        GradeRecord.student_id == student.id,
        GradeRecord.course_code == course_code)).all()
    if not records:
        raise NotFoundError("You have no grade recorded for this course")

    for rec in records:          # single-category assignment: all attempts move together
        rec.category_id = category_id
    db.commit()