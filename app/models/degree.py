from typing import Literal, Optional

from sqlmodel import Field, SQLModel

ProgramType = Literal["Major", "Minor", "Special"]


class Degree(SQLModel, table=True):
    degree_id: Optional[int] = Field(default=None, primary_key=True)
    degree_name: str
    total_credits_required: int
    faculty_name: str
    expected_years: int = Field(default=3, ge=1, le=8)


class StudentDegree(SQLModel, table=True):
    student_id: int = Field(foreign_key="student.student_id", primary_key=True)
    degree_id: int = Field(foreign_key="degree.degree_id", primary_key=True)
    program_type: str = Field(regex="^(Major|Minor|Special)$")