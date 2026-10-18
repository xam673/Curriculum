from datetime import time
from app.database import Base, SessionLocal, engine
from app.models import (Category, Course, Curriculum, CurriculumCourse, GradeRecord,
                        Role, Section, SectionTime, Semester, User)


def run():
    Base.metadata.drop_all(engine)     # WARNING: wipes everything
    Base.metadata.create_all(engine)
    db = SessionLocal()

    # --- Curriculum + categories (FR-03, FR-15) ---
    cs = Curriculum(name="B.Sc. Computer Science", major="Computer Science", year=2566)
    cats = {name: Category(name=name, required_credits=cr) for name, cr in [
        ("General Education", 30), ("Core", 60), ("Major Elective", 18),
        ("Minor/Faculty Elective", 12), ("Elective", 6)]}
    cs.categories = list(cats.values())
    db.add(cs)

    # --- Courses + prereq/coreq ---
    c = {x.code: x for x in [
        Course(code="2301107", name="Calculus I", credits=3),
        Course(code="2301108", name="Calculus II", credits=3),
        Course(code="2301170", name="Computer Programming", credits=3),
        Course(code="2301171", name="Computer Programming Lab", credits=1),
        Course(code="2301260", name="Data Structures", credits=3),
        Course(code="2301365", name="Database Systems", credits=3),
        Course(code="2301377", name="Machine Learning", credits=3),
        Course(code="5500111", name="Experiential English I", credits=3),
        Course(code="2603284", name="Statistics for Science", credits=3),
    ]}
    c["2301108"].prerequisites = [c["2301107"]]
    c["2301171"].corequisites = [c["2301170"]]
    c["2301260"].prerequisites = [c["2301170"]]
    c["2301365"].prerequisites = [c["2301260"]]
    c["2301377"].prerequisites = [c["2301260"], c["2301108"]]
    db.add_all(c.values())
    db.flush()  # assigns IDs

    # Which category each course counts toward (several rows = multi-category, FR-04)
    for code, cat in [
        ("2301107", "Core"), ("2301108", "Core"), ("2301170", "Core"),
        ("2301171", "Core"), ("2301260", "Core"),
        ("2301365", "Major Elective"),
        ("2301377", "Major Elective"), ("2301377", "Minor/Faculty Elective"),
        ("5500111", "General Education"),
        ("2603284", "Minor/Faculty Elective"), ("2603284", "Elective"),
    ]:
        db.add(CurriculumCourse(curriculum_id=cs.id, course_code=code, category_id=cats[cat].id))

    # --- Users ---
    admin = User(name="Admin Staff", email="admin@cu.ac.th", role=Role.admin)
    advisor = User(name="Dr. Somchai", email="somchai@cu.ac.th", role=Role.advisor)
    db.add_all([admin, advisor])
    db.flush()
    s1 = User(name="Nattapong", email="6630000121@student.chula.ac.th", role=Role.student,
              student_code="6630000121", curriculum_id=cs.id, advisor_id=advisor.id)
    s2 = User(name="Pim", email="6630000221@student.chula.ac.th", role=Role.student,
              student_code="6630000221", curriculum_id=cs.id)  # no advisor yet -> test FR-12
    db.add_all([s1, s2])
    db.flush()

    # --- Grades for s1 (FR-06) ---
    for code, y, t, g in [("2301107", 2567, 1, "A"), ("2301170", 2567, 1, "B+"),
                          ("2301171", 2567, 1, "A"), ("5500111", 2567, 1, "B"),
                          ("2301108", 2567, 2, "C+")]:
        db.add(GradeRecord(student_id=s1.id, course_code=code,
                           academic_year=y, term=t, grade=g))

    # --- Semester + sections (FR-16). 2301260 and 2301365 overlap on purpose (FR-10 demo) ---
    sem = Semester(academic_year=2568, term=1, registration_open=True)
    db.add(sem)
    db.flush()
    for code, day, start, end, kind in [
        ("2301260", "MON", time(9), time(12), "lecture"),
        ("2301365", "MON", time(10), time(12), "lecture"),
        ("2301377", "WED", time(13), time(16), "lecture"),
        ("2301170", "TUE", time(9), time(12), "lecture"),
        ("2301171", "TUE", time(13), time(16), "lab"),
        ("2603284", "THU", time(9), time(12), "lecture"),
    ]:
        sec = Section(course_code=code, semester_id=sem.id, section_no=1, instructor="TBA")
        sec.times = [SectionTime(day=day, start=start, end=end, kind=kind)]
        db.add(sec)

    db.commit()
    db.close()
    print("Database seeded!")


if __name__ == "__main__":
    run()