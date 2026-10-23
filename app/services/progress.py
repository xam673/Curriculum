from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Course, Curriculum, GradeRecord, User
from app.services.curriculum import (effective_category, eligible_ids, get_categories,
                                     get_eligible_map, require_curriculum)
from app.services.grade_rules import calculate_gpax, is_passing


@dataclass
class PassedCourse:
    code: str
    credits: int
    category_id: int | None


def _percent(part: int, whole: int) -> float:
    if whole == 0:
        return 100.0
    return round(part / whole * 100, 1)


def calculate_progress(categories, passed_courses: list[PassedCourse]) -> dict:
    """Pure calculation. Extra credits in a category don't spill into overall progress."""
    earned = {c.id: 0 for c in categories}
    course_lists = {c.id: [] for c in categories}
    unassigned = []

    for pc in passed_courses:
        if pc.category_id in earned:
            earned[pc.category_id] += pc.credits
            course_lists[pc.category_id].append(pc.code)
        else:
            unassigned.append(pc.code)

    rows, total_required, total_counted = [], 0, 0
    for cat in categories:
        counted = min(earned[cat.id], cat.required_credits)
        total_required += cat.required_credits
        total_counted += counted
        rows.append({
            "category_id": cat.id,
            "name": cat.name,
            "required_credits": cat.required_credits,
            "earned_credits": earned[cat.id],
            "percent": _percent(counted, cat.required_credits),
            "courses": course_lists[cat.id],
        })

    return {
        "total_required": total_required,
        "total_earned": sum(pc.credits for pc in passed_courses),
        "overall_percent": _percent(total_counted, total_required),
        "categories": rows,
        "unassigned_courses": unassigned,
    }


def get_student_progress(db: Session, student: User) -> dict:
    """FR-03: overall + per-category progress, plus GPAX."""
    cur_id = require_curriculum(student)
    curriculum = db.get(Curriculum, cur_id)
    categories = get_categories(db, cur_id)
    mapping = get_eligible_map(db, cur_id)

    stmt = (select(GradeRecord.grade, GradeRecord.category_id, Course.code, Course.credits)
            .join(Course, GradeRecord.course_code == Course.code)
            .where(GradeRecord.student_id == student.id)
            .order_by(GradeRecord.academic_year, GradeRecord.term))
    rows = db.execute(stmt).all()

    # A retaken course earns credits only once
    passed: dict[str, PassedCourse] = {}
    for grade, chosen, code, credits in rows:
        if is_passing(grade):
            cat_id = effective_category(chosen, eligible_ids(mapping, code, categories))
            passed[code] = PassedCourse(code, credits, cat_id)

    result = calculate_progress(categories, list(passed.values()))
    result["curriculum_name"] = curriculum.name
    result["gpax"] = calculate_gpax([(g, cr) for g, _, _, cr in rows])
    return result