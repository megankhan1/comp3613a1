from sqlmodel import Session

from app.models.student import Student


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_profile(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        email: str,
        current_year: int,
    ) -> Student:
        student = Student(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            current_year=current_year,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student