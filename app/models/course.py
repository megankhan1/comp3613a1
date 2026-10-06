from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    course_code: str = Field(primary_key=True)
    course_name: str
    description: str = ""
    credits: int


class Semester(SQLModel, table=True):
    semester_id: Optional[int] = Field(default=None, primary_key=True)
    semester_name: str
    semester_year: int
    start_date: date
    end_date: date


class DegreeRequirement(SQLModel, table=True):
    requirement_id: Optional[int] = Field(default=None, primary_key=True)
    degree_id: int = Field(foreign_key="degree.degree_id")
    course_code: str = Field(foreign_key="course.course_code")
    requirement_type: str
    minimum_grade: str
    expected_year: int = Field(default=1, ge=1, le=8)
    expected_semester: int = Field(default=1, ge=1, le=3)


class Advisor(SQLModel, table=True):
    advisor_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    first_name: str
    last_name: str
    email: str