from app.repositories.student_degree import StudentDegreeRepository


class StudentDegreeService:
    def __init__(self, student_degree_repo: StudentDegreeRepository):
        self.student_degree_repo = student_degree_repo

    def get_degree_cards(self, user_id: int):
        return self.student_degree_repo.get_degree_cards_for_user(user_id)

    def get_degree_for_user(self, user_id: int, degree_id: int):
        return self.student_degree_repo.get_degree_for_user(user_id, degree_id)