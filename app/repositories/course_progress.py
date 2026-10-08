from datetime import date

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models.course import Course, DegreeRequirement, Semester
from app.models.course_selection import CourseSelection
from app.models.degree import StudentDegree
from app.models.degree import Degree
from app.models.student import Student


class CourseProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_completed_courses(self, user_id: int, degree_id: int):
        statement = (
            select(Course, Semester, CourseSelection)
            .join(CourseSelection, CourseSelection.course_code == Course.course_code)
            .join(Semester, Semester.semester_id == CourseSelection.semester_id)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .join(
                DegreeRequirement,
                DegreeRequirement.course_code == Course.course_code,
            )
            .where(
                Student.user_id == user_id,
                DegreeRequirement.degree_id == degree_id,
                CourseSelection.status == "completed",
            )
            .order_by(Semester.semester_year.desc(), Course.course_code)
        )
        return self.db.exec(statement).all()

    def get_empty_semesters(self):
        statement = (
            select(Semester)
            .outerjoin(
                CourseSelection,
                CourseSelection.semester_id == Semester.semester_id,
            )
            .where(CourseSelection.selection_id.is_(None))
            .order_by(Semester.start_date)
        )
        return self.db.exec(statement).all()

    def get_semester(self, semester_id: int):
        return self.db.get(Semester, semester_id)

    def find_semester(self, calendar_year: int, semester_number: int):
        start_month = (semester_number - 1) * 4 + 1
        return self.db.exec(
            select(Semester).where(
                Semester.semester_year == calendar_year,
                Semester.start_date == date(calendar_year, start_month, 1),
            )
        ).first()

    def student_has_selections_in_semester(self, user_id: int, semester_id: int) -> bool:
        statement = (
            select(CourseSelection.selection_id)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .where(
                Student.user_id == user_id,
                CourseSelection.semester_id == semester_id,
            )
        )
        return self.db.exec(statement).first() is not None

    def ensure_degree_requirement(
        self,
        degree_id: int,
        course_code: str,
        expected_year: int,
        expected_semester: int,
        requirement_type: str = "Core",
        minimum_grade: str = "C",
    ) -> None:
        existing = self.db.exec(
            select(DegreeRequirement).where(
                DegreeRequirement.degree_id == degree_id,
                DegreeRequirement.course_code == course_code,
            )
        ).first()
        if existing is None:
            self.db.add(
                DegreeRequirement(
                    degree_id=degree_id,
                    course_code=course_code,
                    requirement_type=requirement_type,
                    minimum_grade=minimum_grade,
                    expected_year=expected_year,
                    expected_semester=expected_semester,
                )
            )
            self.db.commit()

    def get_semesters(self, user_id: int):
        student_id = select(Student.student_id).where(Student.user_id == user_id).scalar_subquery()
        statement = (
            select(Semester)
            .outerjoin(CourseSelection, CourseSelection.semester_id == Semester.semester_id)
            .where(
                or_(
                    CourseSelection.student_id == student_id,
                    CourseSelection.selection_id.is_(None),
                )
            )
            .distinct()
            .order_by(Semester.start_date)
        )
        return self.db.exec(statement).all()

    def get_remaining_courses(self, user_id: int, degree_id: int):
        completed_codes = (
            select(CourseSelection.course_code)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .where(
                Student.user_id == user_id,
                CourseSelection.status == "completed",
            )
        )
        statement = (
            select(Course, DegreeRequirement)
            .join(DegreeRequirement, DegreeRequirement.course_code == Course.course_code)
            .join(Degree, Degree.degree_id == DegreeRequirement.degree_id)
            .join(StudentDegree, StudentDegree.degree_id == Degree.degree_id)
            .join(Student, Student.student_id == StudentDegree.student_id)
            .where(
                Student.user_id == user_id,
                DegreeRequirement.degree_id == degree_id,
                ~Course.course_code.in_(completed_codes),
            )
            .distinct()
            .order_by(
                DegreeRequirement.expected_year,
                DegreeRequirement.expected_semester,
                DegreeRequirement.requirement_type,
                Course.course_code,
            )
        )
        return self.db.exec(statement).all()

    def get_degree_expected_years(self, degree_id: int) -> int | None:
        degree = self.db.get(Degree, degree_id)
        return degree.expected_years if degree is not None else None

    def get_remaining_course_plan(self, user_id: int, degree_id: int):
        statement = (
            select(Course, Semester, CourseSelection)
            .join(CourseSelection, CourseSelection.course_code == Course.course_code)
            .join(Semester, Semester.semester_id == CourseSelection.semester_id)
            .join(DegreeRequirement, DegreeRequirement.course_code == Course.course_code)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .where(
                Student.user_id == user_id,
                DegreeRequirement.degree_id == degree_id,
                CourseSelection.status != "completed",
            )
            .order_by(Semester.start_date, Course.course_code)
        )
        return self.db.exec(statement).all()

    def add_completed_course(
        self,
        user_id: int,
        semester_id: int,
        course_code: str,
        course_name: str,
        description: str,
        credits: int,
    ) -> bool:
        student = self.db.exec(select(Student).where(Student.user_id == user_id)).one_or_none()
        semester = self.db.get(Semester, semester_id)
        if student is None or semester is None:
            return False

        course = self.db.get(Course, course_code)
        duplicate_statement = select(CourseSelection).where(
            CourseSelection.student_id == student.student_id,
            CourseSelection.course_code == course_code,
            CourseSelection.semester_id == semester_id,
            CourseSelection.status == "completed",
        )
        if self.db.exec(duplicate_statement).first():
            return False

        try:
            if course is None:
                course = Course(
                    course_code=course_code,
                    course_name=course_name,
                    description=description,
                    credits=credits,
                )
                self.db.add(course)

            self.db.add(
                CourseSelection(
                    student_id=student.student_id,
                    course_code=course_code,
                    semester_id=semester_id,
                    status="completed",
                )
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def add_semester(
        self,
        semester_name: str,
        semester_year: int,
        start_date: date,
        end_date: date,
    ) -> bool:
        existing = self.db.exec(
            select(Semester).where(
                Semester.semester_year == semester_year,
                Semester.start_date >= start_date,
                Semester.start_date <= end_date,
            )
        ).first()
        if existing:
            return False

        try:
            self.db.add(
                Semester(
                    semester_name=semester_name,
                    semester_year=semester_year,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def delete_completed_course(self, user_id: int, selection_id: int) -> bool:
        selection = self.db.get(CourseSelection, selection_id)
        student = (
            self.db.get(Student, selection.student_id)
            if selection is not None
            else None
        )
        if (
            selection is None
            or student is None
            or student.user_id != user_id
            or selection.status != "completed"
        ):
            return False

        self.db.delete(selection)
        self.db.commit()
        return True

    def delete_semester_history(self, user_id: int, semester_id: int) -> bool:
        student = self.db.exec(select(Student).where(Student.user_id == user_id)).one_or_none()
        semester = self.db.get(Semester, semester_id)
        if student is None or semester is None:
            return False

        try:
            student_selections = self.db.exec(
                select(CourseSelection).where(
                    CourseSelection.student_id == student.student_id,
                    CourseSelection.semester_id == semester_id,
                    CourseSelection.status == "completed",
                )
            ).all()
            for selection in student_selections:
                self.db.delete(selection)
            self.db.flush()

            remaining_selections = self.db.exec(
                select(CourseSelection.selection_id).where(
                    CourseSelection.semester_id == semester_id
                )
            ).first()
            if remaining_selections is None:
                self.db.delete(semester)

            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise