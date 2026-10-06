from typing import Optional

from sqlmodel import Field, SQLModel


class Student(SQLModel, table=True):
    student_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    first_name: str
    last_name: str
    email: str
    current_year: int = Field(default=1, ge=1, le=8)