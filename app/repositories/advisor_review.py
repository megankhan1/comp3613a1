from sqlmodel import Session, select

from app.models.course import Advisor, Course, Semester
from app.models.course_selection import CourseSelection
from app.models.degree import Degree, StudentDegree
from app.models.student import Student


class AdvisorReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_faculty_cards(self):
        statement = (
            select(Degree.faculty_name)
            .distinct()
            .where(Degree.faculty_name.isnot(None))
            .order_by(Degree.faculty_name)
        )
        rows = self.db.exec(statement).all()
        return [
            row[0] if isinstance(row, tuple) else row
            for row in rows
        ]

    def get_degree_cards_for_faculty(self, faculty_name: str):
        statement = (
            select(Degree)
            .where(Degree.faculty_name == faculty_name)
            .order_by(Degree.degree_name)
        )
        return self.db.exec(statement).all()

    def get_primary_degree_id(self, student_id: int):
        rows = self.db.exec(
            select(StudentDegree).where(StudentDegree.student_id == student_id)
        ).all()
        if not rows:
            return None
        preference = {"Major": 0, "Minor": 1, "Special": 2}
        ordered = sorted(
            rows,
            key=lambda assignment: (
                preference.get(assignment.program_type, 9),
                assignment.degree_id,
            ),
        )
        return ordered[0].degree_id

    def get_pending_students_for_degree(self, degree_id: int):
        statement = (
            select(Student, StudentDegree.program_type)
            .join(StudentDegree, StudentDegree.student_id == Student.student_id)
            .join(CourseSelection, CourseSelection.student_id == Student.student_id)
            .where(
                StudentDegree.degree_id == degree_id,
                CourseSelection.status == "pending",
            )
            .distinct()
            .order_by(Student.last_name, Student.first_name)
        )
        rows = self.db.exec(statement).all()
        return [
            {"student": student, "program_type": program_type}
            for student, program_type in rows
            if self.get_primary_degree_id(student.student_id) == degree_id
        ]

    def get_pending_review_for_student_degree(self, student_id: int, degree_id: int):
        student = self.db.get(Student, student_id)
        degree = self.db.get(Degree, degree_id)
        if student is None or degree is None:
            return None

        statement = (
            select(CourseSelection, Semester, Course)
            .join(Semester, Semester.semester_id == CourseSelection.semester_id)
            .join(Course, Course.course_code == CourseSelection.course_code)
            .where(
                CourseSelection.student_id == student_id,
                CourseSelection.status == "pending",
            )
            .order_by(Semester.start_date, Course.course_code)
        )
        rows = self.db.exec(statement).all()

        grouped = {}
        for selection, semester, course in rows:
            grouped.setdefault(
                semester.semester_id,
                {"semester": semester, "courses": []},
            )
            grouped[semester.semester_id]["courses"].append((course, selection))

        return {
            "student": student,
            "degree": degree,
            "semesters": list(grouped.values()),
        }

    def get_pending_semesters(self):
        statement = (
            select(CourseSelection, Student, Semester, Course)
            .join(Student, Student.student_id == CourseSelection.student_id)
            .join(Semester, Semester.semester_id == CourseSelection.semester_id)
            .join(Course, Course.course_code == CourseSelection.course_code)
            .where(CourseSelection.status == "pending")
            .order_by(Student.last_name, Student.first_name, Semester.start_date, Course.course_code)
        )
        rows = self.db.exec(statement).all()

        reviews_by_key = {}
        for selection, student, semester, course in rows:
            key = (student.student_id, semester.semester_id)
            review = reviews_by_key.setdefault(
                key,
                {"student": student, "semester": semester, "courses": []},
            )
            review["courses"].append((course, selection))
        return list(reviews_by_key.values())

    def decide_semester(
        self,
        advisor_user_id: int,
        student_id: int,
        semester_id: int,
        decision: str,
        notes: str,
    ) -> str:
        advisor = self.db.exec(
            select(Advisor).where(Advisor.user_id == advisor_user_id)
        ).one_or_none()
        if advisor is None:
            return "advisor_missing"

        selections = self.db.exec(
            select(CourseSelection).where(
                CourseSelection.student_id == student_id,
                CourseSelection.semester_id == semester_id,
                CourseSelection.status == "pending",
            )
        ).all()
        if not selections:
            return "review_missing"

        try:
            for selection in selections:
                selection.status = decision
                selection.reviewed_by = advisor.advisor_id
                selection.notes = notes.strip() or None
                self.db.add(selection)
            self.db.commit()
            return "decided"
        except Exception:
            self.db.rollback()
            raise