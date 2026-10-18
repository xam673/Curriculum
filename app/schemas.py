from pydantic import BaseModel, ConfigDict, Field
from app.models import Role

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