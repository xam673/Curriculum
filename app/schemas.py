from pydantic import BaseModel, ConfigDict, Field
from app.models import Role
from typing import Literal

COURSE_CODE = r"^\d{7}$"   # Chula course codes are 7 digits


# ----- Auth -----
class LoginRequest(BaseModel):
    user_id: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    role: Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: Role
    student_code: str | None = None
    curriculum_id: int | None = None
    advisor_id: int | None = None


# ----- Courses -----
class CourseBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    credits: int = Field(ge=0, le=12)
    prerequisites: list[str] = []
    corequisites: list[str] = []


class CourseCreate(CourseBase):
    code: str = Field(pattern=COURSE_CODE)


class CourseUpdate(CourseBase):
    pass


class CourseOut(BaseModel):
    code: str
    name: str
    credits: int
    prerequisites: list[str]
    corequisites: list[str]


# ----- Grades (FR-06) -----
GradeLetter = Literal["A", "B+", "B", "C+", "C", "D+", "D", "F", "W", "S", "U", "V"]


class GradeCreate(BaseModel):
    course_code: str = Field(pattern=COURSE_CODE)
    academic_year: int = Field(ge=2500, le=2700)   # Buddhist year, e.g. 2567
    term: int = Field(ge=1, le=3)
    grade: GradeLetter


class GradeUpdate(BaseModel):
    grade: GradeLetter


class GradeOut(BaseModel):
    id: int
    course_code: str
    course_name: str
    credits: int
    academic_year: int
    term: int
    grade: str
    category_id: int | None
    category_name: str | None


# ----- Categories & progress (FR-03, FR-04) -----
class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    required_credits: int


class CategoryAssign(BaseModel):
    category_id: int


class CategoryProgress(BaseModel):
    category_id: int
    name: str
    required_credits: int
    earned_credits: int
    percent: float
    courses: list[str]


class ProgressOut(BaseModel):
    curriculum_name: str
    gpax: float | None
    total_required: int
    total_earned: int
    overall_percent: float
    categories: list[CategoryProgress]
    unassigned_courses: list[str]