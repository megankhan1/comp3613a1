from app.repositories.advisor_review import AdvisorReviewRepository


class AdvisorReviewService:
    def __init__(self, repository: AdvisorReviewRepository):
        self.repository = repository

    def get_faculty_cards(self):
        return self.repository.get_faculty_cards()

    def get_degree_cards_for_faculty(self, faculty_name: str):
        return self.repository.get_degree_cards_for_faculty(faculty_name)

    def get_pending_students_for_degree(self, degree_id: int):
        return self.repository.get_pending_students_for_degree(degree_id)

    def get_pending_review_for_student_degree(self, student_id: int, degree_id: int):
        return self.repository.get_pending_review_for_student_degree(student_id, degree_id)

    def get_pending_semesters(self):
        return self.repository.get_pending_semesters()

    def decide_semester(
        self,
        advisor_user_id: int,
        student_id: int,
        semester_id: int,
        decision: str,
        notes: str,
    ) -> str:
        normalized_decision = decision.strip().lower()
        if normalized_decision not in {"approved", "denied"}:
            return "invalid_decision"
        if normalized_decision == "denied" and not notes.strip():
            return "notes_required"
        return self.repository.decide_semester(
            advisor_user_id,
            student_id,
            semester_id,
            normalized_decision,
            notes,
        )