from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Category, Course, CurriculumCourse, Role, User
from app.schemas import CourseCreate, CourseOut, CourseUpdate

router = APIRouter(tags=["Courses"])


def to_out(c: Course) -> CourseOut:
    return CourseOut(code=c.code, name=c.name, credits=c.credits,
                     prerequisites=[p.code for p in c.prerequisites],
                     corequisites=[p.code for p in c.corequisites])


def resolve_codes(db: Session, codes: list[str]) -> list[Course]:
    """Turn ['2301107', ...] into Course objects; error if any code doesn't exist (FR-19)."""
    if not codes:
        return []
    found = db.scalars(select(Course).where(Course.code.in_(codes))).all()
    missing = set(codes) - {c.code for c in found}
    if missing:
        raise HTTPException(400, f"Unknown course code(s): {', '.join(sorted(missing))}")
    return list(found)


# ----- FR-05: search & filter (any logged-in user) -----
@router.get("/courses", response_model=list[CourseOut])
def search_courses(q: str | None = None, category: str | None = None,
                   db: Session = Depends(get_db),
                   _user: User = Depends(get_current_user)):
    stmt = select(Course).options(selectinload(Course.prerequisites),
                                  selectinload(Course.corequisites))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Course.code.ilike(like), Course.name.ilike(like)))
    if category:
        stmt = (stmt.join(CurriculumCourse, CurriculumCourse.course_code == Course.code)
                    .join(Category, Category.id == CurriculumCourse.category_id)
                    .where(Category.name == category))
    stmt = stmt.distinct().order_by(Course.code).limit(100)
    return [to_out(c) for c in db.scalars(stmt).all()]


@router.get("/courses/{code}", response_model=CourseOut)
def get_course(code: str, db: Session = Depends(get_db),
               _user: User = Depends(get_current_user)):
    course = db.get(Course, code)
    if not course:
        raise HTTPException(404, "Course not found")
    return to_out(course)


# ----- FR-14: admin course management -----
@router.post("/admin/courses", response_model=CourseOut, status_code=201)
def create_course(body: CourseCreate, db: Session = Depends(get_db),
                  _admin: User = Depends(require_role(Role.admin))):
    if db.get(Course, body.code):
        raise HTTPException(409, "Course code already exists")
    if body.code in body.prerequisites + body.corequisites:
        raise HTTPException(400, "A course cannot require itself")
    course = Course(code=body.code, name=body.name, credits=body.credits)
    course.prerequisites = resolve_codes(db, body.prerequisites)
    course.corequisites = resolve_codes(db, body.corequisites)
    db.add(course)
    db.commit()
    return to_out(course)


@router.put("/admin/courses/{code}", response_model=CourseOut)
def update_course(code: str, body: CourseUpdate, db: Session = Depends(get_db),
                  _admin: User = Depends(require_role(Role.admin))):
    course = db.get(Course, code)
    if not course:
        raise HTTPException(404, "Course not found")
    if code in body.prerequisites + body.corequisites:
        raise HTTPException(400, "A course cannot require itself")
    course.name = body.name
    course.credits = body.credits
    course.prerequisites = resolve_codes(db, body.prerequisites)
    course.corequisites = resolve_codes(db, body.corequisites)
    db.commit()
    return to_out(course)


@router.delete("/admin/courses/{code}", status_code=204)
def delete_course(code: str, db: Session = Depends(get_db),
                  _admin: User = Depends(require_role(Role.admin))):
    course = db.get(Course, code)
    if not course:
        raise HTTPException(404, "Course not found")
    try:
        db.delete(course)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Course is in use (sections/grades) and cannot be deleted")
    return Response(status_code=204)