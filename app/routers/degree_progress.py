from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from . import router, templates
from app.repositories.student_degree import StudentDegreeRepository
from app.repositories.course_progress import CourseProgressRepository
from app.services.student_degree_service import StudentDegreeService
from app.services.course_progress_service import CourseProgressService
from app.utilities.flash import flash


def _degree_services(db, user_id: int, degree_id: int):
    student_degree_service = StudentDegreeService(StudentDegreeRepository(db))
    degree_assignment = student_degree_service.get_degree_for_user(user_id, degree_id)
    if degree_assignment is None:
        raise HTTPException(status_code=404, detail="Degree not found")
    return degree_assignment


@router.get("/app/degrees/{degree_id}/track", response_class=HTMLResponse)
async def degree_progress_view(
    degree_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    degree, program_type = _degree_services(db, user.id, degree_id)
    return templates.TemplateResponse(
        request=request,
        name="degree-progress.html",
        context={"user": user, "degree": degree, "program_type": program_type},
    )


@router.get("/app/degrees/{degree_id}/completed", response_class=HTMLResponse)
async def completed_courses_view(
    degree_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    degree, program_type = _degree_services(db, user.id, degree_id)
    course_progress_service = CourseProgressService(CourseProgressRepository(db))
    semester_groups = course_progress_service.get_completed_courses(user.id, degree_id)
    return templates.TemplateResponse(
        request=request,
        name="completed-courses.html",
        context={
            "user": user,
            "degree": degree,
            "program_type": program_type,
            "semester_groups": semester_groups,
        },
    )


@router.post(
    "/app/degrees/{degree_id}/completed/semesters/{semester_id}/courses",
    response_class=HTMLResponse,
)
async def add_completed_course_action(
    degree_id: int,
    semester_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    course_code: str = Form(),
    course_name: str = Form(),
    description: str = Form(default=""),
    credits: int = Form(),
):
    _degree_services(db, user.id, degree_id)
    course_progress_service = CourseProgressService(CourseProgressRepository(db))
    try:
        added = course_progress_service.add_completed_course(
            user.id,
            semester_id,
            course_code.strip().upper(),
            course_name.strip(),
            description.strip(),
            credits,
            degree_id,
        )
        if added:
            flash(request, "Completed course added.")
        else:
            flash(request, "That course is already recorded for this semester.", "warning")
    except ValueError as exc:
        flash(request, str(exc), "warning")
    return RedirectResponse(
        url=request.url_for("completed_courses_view", degree_id=degree_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/app/degrees/{degree_id}/completed/semesters", response_class=HTMLResponse)
async def add_completed_semester_action(
    degree_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    academic_year_label: str = Form(),
    semester_number: int = Form(),
):
    _degree_services(db, user.id, degree_id)
    course_progress_service = CourseProgressService(CourseProgressRepository(db))
    try:
        added = course_progress_service.add_academic_semester(
            user.id,
            academic_year_label,
            semester_number,
            degree_id,
        )
        if added:
            flash(request, "Semester added.")
        else:
            flash(request, "That semester already exists.", "warning")
    except (ValueError, OverflowError) as exc:
        flash(request, str(exc), "warning")
    return RedirectResponse(
        url=request.url_for("completed_courses_view", degree_id=degree_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/degrees/{degree_id}/completed/selections/{selection_id}/delete",
    response_class=HTMLResponse,
)
async def delete_completed_course_action(
    degree_id: int,
    selection_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    _degree_services(db, user.id, degree_id)
    course_progress_service = CourseProgressService(CourseProgressRepository(db))
    deleted = course_progress_service.delete_completed_course(user.id, selection_id)
    if deleted:
        flash(request, "Completed course removed from your history.")
    else:
        flash(request, "Completed course not found.", "warning")
    return RedirectResponse(
        url=request.url_for("completed_courses_view", degree_id=degree_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/degrees/{degree_id}/completed/semesters/{semester_id}/delete",
    response_class=HTMLResponse,
)
async def delete_completed_semester_action(
    degree_id: int,
    semester_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    _degree_services(db, user.id, degree_id)
    course_progress_service = CourseProgressService(CourseProgressRepository(db))
    deleted = course_progress_service.delete_semester_history(user.id, semester_id)
    if deleted:
        flash(request, "Semester removed from your completed-course history.")
    else:
        flash(request, "Semester not found.", "warning")
    return RedirectResponse(
        url=request.url_for("completed_courses_view", degree_id=degree_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/app/degrees/{degree_id}/remaining", response_class=HTMLResponse)
async def remaining_courses_view(
    degree_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    degree, program_type = _degree_services(db, user.id, degree_id)
    course_progress_service = CourseProgressService(CourseProgressRepository(db))
    remaining_years = course_progress_service.get_remaining_courses(user.id, degree_id)
    return templates.TemplateResponse(
        request=request,
        name="remaining-courses.html",
        context={
            "user": user,
            "degree": degree,
            "program_type": program_type,
            "remaining_years": remaining_years,
        },
    )