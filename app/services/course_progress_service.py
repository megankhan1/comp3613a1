from calendar import monthrange
from datetime import date
import re

from app.repositories.course_progress import CourseProgressRepository


class CourseProgressService:
    def __init__(self, repository: CourseProgressRepository):
        self.repository = repository

    def get_completed_courses(self, user_id: int, degree_id: int):
        completed_courses = self.repository.get_completed_courses(user_id, degree_id)
        courses_by_semester = {}
        semesters_by_id = {}
        for course, semester, selection in completed_courses:
            courses_by_semester.setdefault(semester.semester_id, []).append(
                (course, selection)
            )
            semesters_by_id[semester.semester_id] = semester
        for semester in self.repository.get_empty_semesters():
            semesters_by_id.setdefault(semester.semester_id, semester)

        semesters_by_year = {}
        for semester in semesters_by_id.values():
            semesters_by_year.setdefault(semester.semester_year, []).append(semester)

        return [
            {
            "year_number": year_number,
                "semesters": [
                    {
                        "semester": semester,
                        "semester_number": (semester.start_date.month - 1) // 4 + 1,
                        "courses": courses_by_semester.get(semester.semester_id, []),
                    }
                    for semester in sorted(year_semesters, key=lambda item: item.start_date)
                ],
            }
            for year_number, (_calendar_year, year_semesters) in enumerate(
                sorted(semesters_by_year.items()),
                start=1,
            )
        ]

    def get_remaining_courses(self, user_id: int, degree_id: int):
        remaining_courses = self.repository.get_remaining_courses(user_id, degree_id)
        expected_years = self.repository.get_degree_expected_years(degree_id)
        if expected_years is None:
            return []

        years = [
            {
                "year_number": year_number,
                "semesters": [
                    {
                        "semester_number": semester_number,
                        "is_optional": semester_number == 3,
                        "core_courses": [],
                        "elective_courses": [],
                    }
                    for semester_number in (1, 2, 3)
                ],
            }
            for year_number in range(1, expected_years + 1)
        ]

        for course, requirement in remaining_courses:
            year_number = requirement.expected_year
            semester_number = requirement.expected_semester
            if not 1 <= year_number <= expected_years or semester_number not in (1, 2, 3):
                continue
            year = years[year_number - 1]
            semester = year["semesters"][semester_number - 1]
            entry = {"course": course, "requirement": requirement}
            if requirement.requirement_type.strip().lower() == "elective":
                semester["elective_courses"].append(entry)
            else:
                semester["core_courses"].append(entry)

        return years

    def add_completed_course(
        self,
        user_id: int,
        semester_id: int,
        course_code: str,
        course_name: str,
        description: str,
        credits: int,
        degree_id: int,
    ) -> bool:
        if credits <= 0:
            raise ValueError("Course credits must be greater than zero")
        if not course_code.strip() or not course_name.strip():
            raise ValueError("Course code and course name are required")
        added = self.repository.add_completed_course(
            user_id,
            semester_id,
            course_code,
            course_name,
            description,
            credits,
        )
        if added:
            semester = self.repository.get_semester(semester_id)
            if semester is not None:
                semester_number = (semester.start_date.month - 1) // 4 + 1
                calendar_years = sorted(
                    {item.semester_year for item in self.repository.get_semesters(user_id)}
                )
                if semester.semester_year in calendar_years:
                    academic_year_number = calendar_years.index(semester.semester_year) + 1
                elif calendar_years:
                    academic_year_number = len(calendar_years) + 1
                else:
                    academic_year_number = 1
                self.repository.ensure_degree_requirement(
                    degree_id,
                    course_code.strip().upper(),
                    academic_year_number,
                    semester_number,
                )
        return added

    def add_semester(
        self,
        semester_name: str,
        semester_year: int,
        start_date: date,
        end_date: date,
    ) -> bool:
        if start_date > end_date:
            raise ValueError("Semester end date must be on or after its start date")
        if not semester_name.strip():
            raise ValueError("Semester name is required")
        return self.repository.add_semester(
            semester_name,
            semester_year,
            start_date,
            end_date,
        )

    def add_academic_semester(
        self,
        user_id: int,
        academic_year_label: str,
        semester_number: int,
        degree_id: int,
    ) -> bool:
        match = re.fullmatch(r"year\s+([1-9][0-9]*)", academic_year_label.strip(), re.IGNORECASE)
        if match is None:
            raise ValueError("Enter a year label such as Year 1")
        if semester_number not in (1, 2, 3):
            raise ValueError("Choose Semester 1, 2, or 3")

        academic_year_number = int(match.group(1))
        completed = self.repository.get_completed_courses(user_id, degree_id)
        calendar_years = {
            semester.semester_year for _course, semester, _selection in completed
        }
        calendar_years.update(
            semester.semester_year
            for semester in self.repository.get_empty_semesters()
        )
        calendar_years = sorted(calendar_years)
        if academic_year_number <= len(calendar_years):
            calendar_year = calendar_years[academic_year_number - 1]
        elif calendar_years:
            calendar_year = calendar_years[-1] + academic_year_number - len(calendar_years)
        else:
            calendar_year = date.today().year + academic_year_number - 1

        start_month = (semester_number - 1) * 4 + 1
        end_month = start_month + 3
        start_date = date(calendar_year, start_month, 1)
        end_date = date(
            calendar_year,
            end_month,
            monthrange(calendar_year, end_month)[1],
        )
        if self.add_semester(
            f"Semester {semester_number}",
            calendar_year,
            start_date,
            end_date,
        ):
            return "added"
        semester = self.repository.find_semester(calendar_year, semester_number)
        if semester is None:
            return "exists"
        if self.repository.student_has_visible_completed(
            user_id, semester.semester_id, degree_id
        ):
            return "exists"
        if self.repository.student_has_selections_in_semester(
            user_id, semester.semester_id
        ):
            return "in_use"
        return "added"

    def delete_completed_course(self, user_id: int, selection_id: int) -> bool:
        return self.repository.delete_completed_course(user_id, selection_id)

    def delete_semester_history(self, user_id: int, semester_id: int) -> bool:
        return self.repository.delete_semester_history(user_id, semester_id)