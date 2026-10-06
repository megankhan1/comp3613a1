from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class CourseSelection(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_code",
            "semester_id",
            name="uq_student_course_semester",
        ),
    )
    selection_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id")
    course_code: str = Field(foreign_key="course.course_code")
    semester_id: int = Field(foreign_key="semester.semester_id")
    status: str
    reviewed_by: Optional[int] = Field(default=None, foreign_key="advisor.advisor_id")
    notes: Optional[str] = None