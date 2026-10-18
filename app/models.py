import enum
from datetime import datetime, time, timezone
from sqlalchemy import (Column, DateTime, Enum, ForeignKey, String, Table, Time,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Role(str, enum.Enum):
    student = "student"
    advisor = "advisor"
    admin = "admin"


def now_utc():
    return datetime.now(timezone.utc)


# ---------- Users (FR-01, FR-02, FR-12, FR-17) ----------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[Role] = mapped_column(Enum(Role))
    token: Mapped[str | None] = mapped_column(String(64), unique=True)
    # Student-only fields (empty for advisors/admins)
    student_code: Mapped[str | None] = mapped_column(String(20), unique=True)
    curriculum_id: Mapped[int | None] = mapped_column(ForeignKey("curricula.id"))
    advisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


# ---------- Curriculum structure (FR-03, FR-15) ----------
class Curriculum(Base):
    __tablename__ = "curricula"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    major: Mapped[str] = mapped_column(String(100))   # "Computer Science", "Mathematics"
    year: Mapped[int]                                  # curriculum revision, e.g. 2566
    categories: Mapped[list["Category"]] = relationship(
        back_populates="curriculum", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"))
    name: Mapped[str] = mapped_column(String(100))    # Core, Elective, Major Elective, ...
    required_credits: Mapped[int]
    curriculum: Mapped["Curriculum"] = relationship(back_populates="categories")


# ---------- Courses + prereq/coreq rules (FR-05, FR-08, FR-09, FR-14) ----------
prerequisite_table = Table(
    "prerequisites", Base.metadata,
    Column("course_code", ForeignKey("courses.code"), primary_key=True),
    Column("required_code", ForeignKey("courses.code"), primary_key=True),
)

corequisite_table = Table(
    "corequisites", Base.metadata,
    Column("course_code", ForeignKey("courses.code"), primary_key=True),
    Column("coreq_code", ForeignKey("courses.code"), primary_key=True),
)


class Course(Base):
    __tablename__ = "courses"
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    credits: Mapped[int]
    prerequisites: Mapped[list["Course"]] = relationship(
        secondary=prerequisite_table,
        primaryjoin=lambda: Course.code == prerequisite_table.c.course_code,
        secondaryjoin=lambda: Course.code == prerequisite_table.c.required_code,
    )
    corequisites: Mapped[list["Course"]] = relationship(
        secondary=corequisite_table,
        primaryjoin=lambda: Course.code == corequisite_table.c.course_code,
        secondaryjoin=lambda: Course.code == corequisite_table.c.coreq_code,
    )


class CurriculumCourse(Base):
    """Which category a course counts toward in a curriculum.
    A course with several rows here qualifies for several categories (FR-04)."""
    __tablename__ = "curriculum_courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"))
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.code"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    __table_args__ = (UniqueConstraint("curriculum_id", "course_code", "category_id"),)


# ---------- Semesters & sections (FR-10, FR-16) ----------
class Semester(Base):
    __tablename__ = "semesters"
    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year: Mapped[int]                         # e.g. 2568
    term: Mapped[int]                                  # 1, 2, 3 (summer)
    registration_open: Mapped[bool] = mapped_column(default=False)


class Section(Base):
    __tablename__ = "sections"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.code"))
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"))
    section_no: Mapped[int]
    instructor: Mapped[str | None] = mapped_column(String(100))
    capacity: Mapped[int] = mapped_column(default=40)
    times: Mapped[list["SectionTime"]] = relationship(cascade="all, delete-orphan")


class SectionTime(Base):
    __tablename__ = "section_times"
    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"))
    day: Mapped[str] = mapped_column(String(3))        # MON, TUE, WED, THU, FRI, SAT
    start: Mapped[time] = mapped_column(Time)
    end: Mapped[time] = mapped_column(Time)
    kind: Mapped[str] = mapped_column(String(10), default="lecture")  # lecture / lab


# ---------- Student academic history (FR-03, FR-04, FR-06) ----------
class GradeRecord(Base):
    __tablename__ = "grade_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.code"))
    academic_year: Mapped[int]
    term: Mapped[int]
    grade: Mapped[str] = mapped_column(String(2))      # A, B+, ..., F, W, S, U, V
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))  # FR-04 choice
    __table_args__ = (UniqueConstraint("student_id", "course_code", "academic_year", "term"),)


# ---------- Plans (FR-07, FR-10) ----------
class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"))
    name: Mapped[str] = mapped_column(String(100), default="My Plan")
    is_shared: Mapped[bool] = mapped_column(default=False)
    items: Mapped[list["PlanItem"]] = relationship(cascade="all, delete-orphan")


class PlanItem(Base):
    __tablename__ = "plan_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"))
    section: Mapped["Section"] = relationship()
    __table_args__ = (UniqueConstraint("plan_id", "section_id"),)


# ---------- Advisor linking & notifications (FR-11, FR-12) ----------
class InviteCode(Base):
    __tablename__ = "invite_codes"
    code: Mapped[str] = mapped_column(String(12), primary_key=True)
    advisor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(20), default="info")  # info / warning / error
    message: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)