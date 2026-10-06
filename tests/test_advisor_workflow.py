from datetime import date

from sqlmodel import Session, SQLModel, create_engine

from app.models.course import Advisor, Course, Semester
from app.models.course_selection import CourseSelection
from app.models.degree import Degree, StudentDegree
from app.models.student import Student
from app.models.user import User
from app.repositories.advisor_review import AdvisorReviewRepository


def test_advisor_review_repository_lists_faculties_and_pending_degree_students():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(username="advisor", email="advisor@example.com", password="pw", role="admin")
        session.add(user)
        session.commit()
        session.refresh(user)

        advisor = Advisor(user_id=user.id, first_name="Ada", last_name="Advisor", email="ada@example.com")
        session.add(advisor)
        session.commit()
        session.refresh(advisor)

        degree = Degree(degree_name="Computer Science", total_credits_required=120, faculty_name="Faculty of Science")
        session.add(degree)
        session.commit()
        session.refresh(degree)

        student = Student(user_id=user.id + 1, first_name="Bob", last_name="Student", email="bob@example.com")
        session.add(student)
        session.commit()
        session.refresh(student)

        session.add(StudentDegree(student_id=student.student_id, degree_id=degree.degree_id, program_type="Major"))

        semester = Semester(
            semester_name="Fall",
            semester_year=2025,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 12, 20),
        )
        session.add(semester)
        session.commit()
        session.refresh(semester)

        course = Course(course_code="CSCI110", course_name="Intro to Computing", description="", credits=3)
        session.add(course)
        session.commit()

        session.add(
            CourseSelection(
                student_id=student.student_id,
                course_code=course.course_code,
                semester_id=semester.semester_id,
                status="pending",
            )
        )
        session.commit()

        repo = AdvisorReviewRepository(session)

        assert repo.get_faculty_cards() == ["Faculty of Science"]
        degree_cards = repo.get_degree_cards_for_faculty("Faculty of Science")
        assert [d.degree_name for d in degree_cards] == ["Computer Science"]

        pending = repo.get_pending_students_for_degree(degree.degree_id)
        assert len(pending) == 1
        assert pending[0]["student"].first_name == "Bob"
