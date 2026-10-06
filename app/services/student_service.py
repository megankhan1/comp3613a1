from app.models.student import Student
from app.repositories.student import StudentRepository


class StudentService:
    def __init__(self, repository: StudentRepository):
        self.repository = repository

    def create_profile(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        email: str,
        current_year: int,
    ) -> Student:
        if not 1 <= current_year <= 8:
            raise ValueError("Current year must be between Year 1 and Year 8")
        return self.repository.create_profile(
            user_id,
            first_name.strip(),
            last_name.strip(),
            email,
            current_year,
        )