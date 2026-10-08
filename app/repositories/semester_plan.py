from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from sqlmodel import Session, select
from datetime import date
from calendar import monthrange

from app.models.course import Course, DegreeRequirement, Semester
from app.models.degree import Degree, StudentDegree
from app.models.student import Student
from app.models.course_selection import CourseSelection


class SemesterPlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_plan_for_student(self, user_id: int, degree_id: int):
        degree_assignment = self.db.exec(
            select(Degree, StudentDegree.program_type)
            .join(StudentDegree, StudentDegree.degree_id == Degree.degree_id)
            .join(Student, Student.student_id == StudentDegree.student_id)
            .where(Student.user_id == user_id, Degree.degree_id == degree_id)
        ).one_or_none()
        if degree_assignment is None:
            return None

        student = self.db.exec(
            select(Student).where(Student.user_id == user_id)
        ).one_or_none()
        if student is None:
            return None
        student_id = student.student_id
        semesters = self.db.exec(
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
        ).all()
        courses = self.db.exec(
            select(Course)
            .join(DegreeRequirement, DegreeRequirement.course_code == Course.course_code)
            .where(DegreeRequirement.degree_id == degree_id)
            .distinct()
            .order_by(Course.course_code)
        ).all()
        selections = []
        if student_id is not None:
            selections = self.db.exec(
                select(Semester, CourseSelection, Course)
                .join(CourseSelection, CourseSelection.semester_id == Semester.semester_id)
                .join(Course, Course.course_code == CourseSelection.course_code)
                .where(CourseSelection.student_id == student_id)
                .order_by(Semester.start_date, Course.course_code)
            ).all()

        return {
            "degree": degree_assignment[0],
            "program_type": degree_assignment[1],
            "student": student,
            "semesters": semesters,
            "required_courses": courses,
            "selections": selections,
        }

    def get_or_create_semester_slot(self, calendar_year: int, semester_number: int) -> Semester:
        start_month = (semester_number - 1) * 4 + 1
        end_month = start_month + 3
        start_date = date(calendar_year, start_month, 1)
        end_date = date(
            calendar_year,
            end_month,
            monthrange(calendar_year, end_month)[1],
        )
        existing = self.db.exec(
            select(Semester).where(
                Semester.semester_year == calendar_year,
                Semester.start_date >= start_date,
                Semester.start_date <= end_date,
            )
        ).one_or_none()
        if existing is not None:
            return existing

        semester = Semester(
            semester_name=f"Semester {semester_number}",
            semester_year=calendar_year,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(semester)
        self.db.commit()
        self.db.refresh(semester)
        return semester

    def get_semester_selections(self, user_id: int, semester_id: int):
        student_id = self.db.exec(
            select(Student.student_id).where(Student.user_id == user_id)
        ).one_or_none()
        if student_id is None:
            return []
        return self.db.exec(
            select(CourseSelection).where(
                CourseSelection.student_id == student_id,
                CourseSelection.semester_id == semester_id,
            )
        ).all()

    def add_course_to_semester(
        self,
        user_id: int,
        semester_id: int,
        course_code: str,
        course_name: str,
        description: str,
        credits: int,
    ) -> str:
        student_id = self.db.exec(
            select(Student.student_id).where(Student.user_id == user_id)
        ).one_or_none()
        if student_id is None:
            return "student_missing"
        if self.db.get(Semester, semester_id) is None:
            return "semester_missing"

        duplicate = self.db.exec(
            select(CourseSelection.selection_id).where(
                CourseSelection.student_id == student_id,
                CourseSelection.course_code == course_code,
                CourseSelection.semester_id == semester_id,
            )
        ).first()
        if duplicate:
            return "duplicate"

        try:
            course = self.db.get(Course, course_code)
            if course is None:
                course = Course(
                    course_code=course_code,
                    course_name=course_name,
                    description=description,
                    credits=credits,
                )
                self.db.add(course)
                self.db.flush()
            self.db.add(
                CourseSelection(
                    student_id=student_id,
                    course_code=course_code,
                    semester_id=semester_id,
                    status="selected",
                )
            )
            self.db.commit()
            return "added"
        except IntegrityError:
            self.db.rollback()
            return "duplicate"
        except Exception:
            self.db.rollback()
            raise

    def submit_semester_for_approval(self, user_id: int, semester_id: int) -> str:
        selections = self.get_semester_selections(user_id, semester_id)
        if not selections:
            return "empty"
        if any(selection.status == "pending" for selection in selections):
            return "pending"

        editable_selections = [
            selection for selection in selections if selection.status in ("selected", "denied")
        ]
        if not editable_selections:
            return "empty"

        try:
            for selection in editable_selections:
                selection.status = "pending"
                self.db.add(selection)
            self.db.commit()
            return "submitted"
        except Exception:
            self.db.rollback()
            raise

    def update_course_selection(
        self,
        user_id: int,
        selection_id: int,
        course_code: str,
        course_name: str,
        description: str,
        credits: int,
    ) -> str:
        selection = self.db.exec(
            select(CourseSelection)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .where(
                Student.user_id == user_id,
                CourseSelection.selection_id == selection_id,
            )
        ).one_or_none()
        if selection is None:
            return "selection_missing"
        if selection.status == "pending":
            return "pending"

        course = self.db.get(Course, selection.course_code)
        if course is None:
            return "course_missing"
        duplicate = self.db.exec(
            select(CourseSelection.selection_id).where(
                CourseSelection.student_id == selection.student_id,
                CourseSelection.course_code == course_code,
                CourseSelection.semester_id == selection.semester_id,
                CourseSelection.selection_id != selection_id,
            )
        ).first()
        if duplicate:
            return "duplicate"

        try:
            if course_code != course.course_code:
                replacement = self.db.get(Course, course_code)
                if replacement is None:
                    replacement = Course(
                        course_code=course_code,
                        course_name=course_name,
                        description=description,
                        credits=credits,
                    )
                    self.db.add(replacement)
                    self.db.flush()
                selection.course_code = course_code
            else:
                course.course_name = course_name
                course.description = description
                course.credits = credits
                self.db.add(course)
            self.db.add(selection)
            self.db.commit()
            return "updated"
        except IntegrityError:
            self.db.rollback()
            return "duplicate"
        except Exception:
            self.db.rollback()
            raise

    def delete_course_selection(self, user_id: int, selection_id: int) -> str:
        selection = self.db.exec(
            select(CourseSelection)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .where(
                Student.user_id == user_id,
                CourseSelection.selection_id == selection_id,
            )
        ).one_or_none()
        if selection is None:
            return "selection_missing"
        if selection.status == "pending":
            return "pending"
        self.db.delete(selection)
        self.db.commit()
        return "deleted"