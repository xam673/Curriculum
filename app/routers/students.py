from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.auth import require_role
from app.database import get_db
from app.models import Role, User
from app.schemas import (CategoryAssign, CategoryOut, GradeCreate, GradeOut,
                         GradeUpdate, ProgressOut)
from app.services import grades as grade_service
from app.services import progress as progress_service

router = APIRouter(prefix="/me", tags=["Student"])
student_only = require_role(Role.student)


# ----- FR-06: grade records -----
@router.get("/grades", response_model=list[GradeOut])
def my_grades(db: Session = Depends(get_db), user: User = Depends(student_only)):
    return grade_service.list_grades(db, user)


@router.post("/grades", response_model=GradeOut, status_code=201)
def add_my_grade(body: GradeCreate, db: Session = Depends(get_db),
                 user: User = Depends(student_only)):
    return grade_service.add_grade(db, user, body.course_code,
                                   body.academic_year, body.term, body.grade)


@router.put("/grades/{record_id}", response_model=GradeOut)
def update_my_grade(record_id: int, body: GradeUpdate, db: Session = Depends(get_db),
                    user: User = Depends(student_only)):
    return grade_service.update_grade(db, user, record_id, body.grade)


@router.delete("/grades/{record_id}", status_code=204)
def delete_my_grade(record_id: int, db: Session = Depends(get_db),
                    user: User = Depends(student_only)):
    grade_service.delete_grade(db, user, record_id)
    return Response(status_code=204)


# ----- FR-03: credit tracker -----
@router.get("/progress", response_model=ProgressOut)
def my_progress(db: Session = Depends(get_db), user: User = Depends(student_only)):
    return progress_service.get_student_progress(db, user)


# ----- FR-04: category selection -----
@router.get("/courses/{code}/categories", response_model=list[CategoryOut])
def eligible_categories(code: str, db: Session = Depends(get_db),
                        user: User = Depends(student_only)):
    """For the frontend dropdown: which categories this course may count toward."""
    return grade_service.get_eligible_categories(db, user, code)


@router.put("/courses/{code}/category", response_model=ProgressOut)
def choose_category(code: str, body: CategoryAssign, db: Session = Depends(get_db),
                    user: User = Depends(student_only)):
    """Returns the updated progress so the dashboard refreshes immediately."""
    grade_service.assign_category(db, user, code, body.category_id)
    return progress_service.get_student_progress(db, user)