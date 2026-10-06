from sqlmodel import Session, select

from app.models.student import Student
from app.models.degree import Degree, StudentDegree


class StudentDegreeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_degree_cards_for_user(self, user_id: int):
        
        result = (
            select(Degree, StudentDegree.program_type)
            .join(StudentDegree, StudentDegree.degree_id == Degree.degree_id)
            .join(Student, Student.student_id == StudentDegree.student_id)
            .where(Student.user_id == user_id)
        )
        return self.db.exec(result).all()

    def get_degree_for_user(self, user_id: int, degree_id: int):
        statement = (
            select(Degree, StudentDegree.program_type)
            .join(StudentDegree, StudentDegree.degree_id == Degree.degree_id)
            .join(Student, Student.student_id == StudentDegree.student_id)
            .where(Student.user_id == user_id, Degree.degree_id == degree_id)
        )
        return self.db.exec(statement).one_or_none()