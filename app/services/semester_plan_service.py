from datetime import date
from math import ceil

from app.repositories.semester_plan import SemesterPlanRepository


class SemesterPlanService:
    def __init__(self, repository: SemesterPlanRepository):
        self.repository = repository

    def get_plan_for_student(self, user_id: int, degree_id: int):
        plan = self.repository.get_plan_for_student(user_id, degree_id)
        if plan is None:
            return None

        semesters = plan["semesters"]
        selections_by_semester = {}
        for semester, selection, course in plan["selections"]:
            selections_by_semester.setdefault(semester.semester_id, []).append(
                (course, selection)
            )

        calendar_years = sorted({semester.semester_year for semester in semesters})
        duration_years = max(1, ceil(plan["degree"].total_credits_required / 30))
        year_count = max(
            duration_years,
            len(calendar_years),
            plan["student"].current_year,
        )
        if not calendar_years:
            first_calendar_year = date.today().year
            calendar_years = [first_calendar_year + offset for offset in range(year_count)]

        academic_years = []
        for year_number in range(1, year_count + 1):
            if year_number <= len(calendar_years):
                calendar_year = calendar_years[year_number - 1]
            else:
                calendar_year = calendar_years[-1] + year_number - len(calendar_years)

            semester_slots = []
            for semester_number in (1, 2, 3):
                semester = next(
                    (
                        item
                        for item in semesters
                        if item.semester_year == calendar_year
                        and (item.start_date.month - 1) // 4 + 1 == semester_number
                    ),
                    None,
                )
                courses = (
                    selections_by_semester.get(semester.semester_id, [])
                    if semester is not None
                    else []
                )
                statuses = {selection.status for _course, selection in courses}
                state = (
                    "pending"
                    if "pending" in statuses
                    else "selected"
                    if "selected" in statuses
                    else "approved"
                    if "approved" in statuses
                    else "denied"
                    if "denied" in statuses
                    else "empty"
                )
                semester_slots.append(
                    {
                        "semester_number": semester_number,
                        "calendar_year": calendar_year,
                        "semester": semester,
                        "semester_id": semester.semester_id if semester else None,
                        "courses": courses,
                        "status": state,
                        "can_edit": state != "pending",
                        "has_editable_courses": any(
                            selection.status in ("selected", "denied")
                            for _course, selection in courses
                        ),
                        "has_completable_courses": any(
                            selection.status in ("selected", "approved")
                            for _course, selection in courses
                        ),
                    }
                )
            academic_years.append(
                {"year_number": year_number, "semesters": semester_slots}
            )

        plan["academic_years"] = academic_years
        plan["current_year_number"] = plan["student"].current_year
        return plan

    def add_course_to_semester(
        self,
        user_id: int,
        degree_id: int,
        academic_year_number: int,
        semester_number: int,
        course_code: str,
        course_name: str,
        description: str,
        credits: int,
    ):
        plan = self.get_plan_for_student(user_id, degree_id)
        if plan is None:
            return "degree_missing"
        slot = self._get_slot(plan, academic_year_number, semester_number)
        if slot is None:
            return "semester_missing"
        if not slot["can_edit"]:
            return "pending"
        if credits <= 0:
            return "invalid_credits"
        if not course_code.strip() or not course_name.strip():
            return "invalid_course"
        semester = self.repository.get_or_create_semester_slot(
            slot["calendar_year"], semester_number
        )
        return self.repository.add_course_to_semester(
            user_id,
            semester.semester_id,
            course_code.strip().upper(),
            course_name.strip(),
            description.strip(),
            credits,
        )

    def submit_semester_for_approval(
        self,
        user_id: int,
        degree_id: int,
        academic_year_number: int,
        semester_number: int,
    ):
        plan = self.get_plan_for_student(user_id, degree_id)
        if plan is None:
            return "degree_missing"
        slot = self._get_slot(plan, academic_year_number, semester_number)
        if slot is None:
            return "semester_missing"
        if not slot["can_edit"]:
            return "pending"
        if slot["semester_id"] is None:
            return "empty"
        return self.repository.submit_semester_for_approval(user_id, slot["semester_id"])

    def complete_semester_for_history(
        self,
        user_id: int,
        degree_id: int,
        academic_year_number: int,
        semester_number: int,
    ):
        plan = self.get_plan_for_student(user_id, degree_id)
        if plan is None:
            return "degree_missing"
        slot = self._get_slot(plan, academic_year_number, semester_number)
        if slot is None or slot["semester_id"] is None:
            return "semester_missing"
        if not slot["can_edit"]:
            return "pending"
        flipped = self.repository.complete_semester(
            user_id,
            slot["semester_id"],
            degree_id,
            academic_year_number,
            semester_number,
        )
        if not flipped:
            return "empty"
        return "completed"

    def update_course_selection(
        self,
        user_id: int,
        degree_id: int,
        academic_year_number: int,
        semester_number: int,
        selection_id: int,
        course_code: str,
        course_name: str,
        description: str,
        credits: int,
    ):
        plan = self.get_plan_for_student(user_id, degree_id)
        if plan is None:
            return "degree_missing"
        slot = self._get_slot(plan, academic_year_number, semester_number)
        if slot is None or slot["semester_id"] is None:
            return "semester_missing"
        if not slot["can_edit"]:
            return "pending"
        if credits <= 0:
            return "invalid_credits"
        if not course_code.strip() or not course_name.strip():
            return "invalid_course"
        return self.repository.update_course_selection(
            user_id,
            selection_id,
            course_code.strip().upper(),
            course_name.strip(),
            description.strip(),
            credits,
        )

    def delete_course_selection(
        self,
        user_id: int,
        degree_id: int,
        academic_year_number: int,
        semester_number: int,
        selection_id: int,
    ):
        plan = self.get_plan_for_student(user_id, degree_id)
        if plan is None:
            return "degree_missing"
        slot = self._get_slot(plan, academic_year_number, semester_number)
        if slot is None or slot["semester_id"] is None:
            return "semester_missing"
        if not slot["can_edit"]:
            return "pending"
        return self.repository.delete_course_selection(user_id, selection_id)

    @staticmethod
    def _get_slot(plan, academic_year_number: int, semester_number: int):
        if semester_number not in (1, 2, 3):
            return None
        year = next(
            (
                item
                for item in plan["academic_years"]
                if item["year_number"] == academic_year_number
            ),
            None,
        )
        if year is None:
            return None
        return year["semesters"][semester_number - 1]