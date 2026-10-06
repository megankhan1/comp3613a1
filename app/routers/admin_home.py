from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.repositories.advisor_review import AdvisorReviewRepository
from app.services.advisor_review_service import AdvisorReviewService
from . import router, templates


@router.get("/admin", response_class=HTMLResponse, name="admin_home_view")
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    advisor_service = AdvisorReviewService(AdvisorReviewRepository(db))
    search_query = request.query_params.get("q", "").strip()
    faculties = advisor_service.get_faculty_cards()
    if search_query:
        faculties = [
            faculty
            for faculty in faculties
            if search_query.lower() in faculty.lower()
        ]
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "faculties": faculties,
            "search_query": search_query,
        },
    )


@router.get("/admin/faculties/{faculty_name}", response_class=HTMLResponse, name="admin_faculty_view")
async def admin_faculty_view(
    faculty_name: str,
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    advisor_service = AdvisorReviewService(AdvisorReviewRepository(db))
    degrees = advisor_service.get_degree_cards_for_faculty(faculty_name)
    search_query = request.query_params.get("q", "").strip()
    if search_query:
        degrees = [
            degree
            for degree in degrees
            if search_query.lower() in degree.degree_name.lower()
            or search_query.lower() in degree.faculty_name.lower()
        ]
    return templates.TemplateResponse(
        request=request,
        name="admin-faculty.html",
        context={
            "user": user,
            "faculty_name": faculty_name,
            "degrees": degrees,
            "search_query": search_query,
        },
    )


@router.get(
    "/admin/faculties/{faculty_name}/{degree_id}",
    response_class=HTMLResponse,
    name="admin_degree_reviews_view",
)
async def admin_degree_reviews_view(
    faculty_name: str,
    degree_id: int,
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    advisor_service = AdvisorReviewService(AdvisorReviewRepository(db))
    degree = next(
        (
            item
            for item in advisor_service.get_degree_cards_for_faculty(faculty_name)
            if item.degree_id == degree_id
        ),
        None,
    )
    if degree is None:
        raise HTTPException(status_code=404, detail="Degree not found")

    students = advisor_service.get_pending_students_for_degree(degree_id)
    search_query = request.query_params.get("q", "").strip()
    if search_query:
        students = [
            entry
            for entry in students
            if search_query.lower() in entry["student"].first_name.lower()
            or search_query.lower() in entry["student"].last_name.lower()
            or search_query.lower() in entry["student"].email.lower()
        ]

    return templates.TemplateResponse(
        request=request,
        name="admin-degree-reviews.html",
        context={
            "user": user,
            "faculty_name": faculty_name,
            "degree": degree,
            "students": students,
            "search_query": search_query,
        },
    )


@router.get(
    "/admin/faculties/{faculty_name}/{degree_id}/students/{student_id}",
    response_class=HTMLResponse,
    name="admin_student_review_view",
)
async def admin_student_review_view(
    faculty_name: str,
    degree_id: int,
    student_id: int,
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    advisor_service = AdvisorReviewService(AdvisorReviewRepository(db))
    review = advisor_service.get_pending_review_for_student_degree(student_id, degree_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Student review not found")

    advisor_notice = request.session.pop("advisor_notice", None)
    advisor_error = request.session.pop("advisor_error", None)

    return templates.TemplateResponse(
        request=request,
        name="admin-student-review.html",
        context={
            "user": user,
            "faculty_name": faculty_name,
            "degree": review["degree"],
            "student": review["student"],
            "semesters": review["semesters"],
            "advisor_notice": advisor_notice,
            "advisor_error": advisor_error,
        },
    )
