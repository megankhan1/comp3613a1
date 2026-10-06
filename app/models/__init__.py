"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.course import Advisor, Course, DegreeRequirement, Semester
from app.models.course_selection import CourseSelection
from app.models.degree import Degree, StudentDegree
from app.models.student import Student
from app.models.user import User

__all__ = [
	"Advisor",
	"Course",
	"CourseSelection",
	"Degree",
	"DegreeRequirement",
	"Semester",
	"Student",
	"StudentDegree",
	"User",
]
