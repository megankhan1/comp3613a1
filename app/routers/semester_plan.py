from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.semester_plan import SemesterPlanRepository
from app.repositories.student_degree import StudentDegreeRepository
from app.services.semester_plan_service import SemesterPlanService
from app.services.student_degree_service import StudentDegreeService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app/degrees/{degree_id}/plan", response_class=HTMLResponse, name="plan_semester_view")
async def plan_semester_view(
    degree_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    student_degree_service = StudentDegreeService(StudentDegreeRepository(db))
    degree_assignment = student_degree_service.get_degree_for_user(user.id, degree_id)
    if degree_assignment is None:
        raise HTTPException(status_code=404, detail="Degree not found")

    semester_plan_service = SemesterPlanService(SemesterPlanRepository(db))
    plan_data = semester_plan_service.get_plan_for_student(user.id, degree_id)
    if plan_data is None:
        raise HTTPException(status_code=404, detail="Degree plan not found")
    degree, program_type = degree_assignment
    toast = request.session.pop("planner_toast", None)
    return templates.TemplateResponse(
        request=request,
        name="semester-picker.html",
        context={
            "user": user,
            "degree": degree,
            "program_type": program_type,
            "plan_data": plan_data,
            "toast": toast,
            "current_year_number": plan_data["current_year_number"],
            "current_year": next(
                year
                for year in plan_data["academic_years"]
                if year["year_number"] == plan_data["current_year_number"]
            ),
        },
    )


@router.get(
    "/app/degrees/{degree_id}/plan/years/{academic_year_number}/semesters/{semester_number}",
    response_class=HTMLResponse,
    name="plan_semester_detail_view",
)
async def plan_semester_detail_view(
    degree_id: int,
    academic_year_number: int,
    semester_number: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    student_degree_service = StudentDegreeService(StudentDegreeRepository(db))
    degree_assignment = student_degree_service.get_degree_for_user(user.id, degree_id)
    if degree_assignment is None:
        raise HTTPException(status_code=404, detail="Degree not found")
    plan_data = SemesterPlanService(SemesterPlanRepository(db)).get_plan_for_student(
        user.id,
        degree_id,
    )
    if plan_data is None:
        raise HTTPException(status_code=404, detail="Degree plan not found")
    year = next(
        (item for item in plan_data["academic_years"] if item["year_number"] == academic_year_number),
        None,
    )
    if (
        academic_year_number != plan_data["current_year_number"]
        or year is None
        or semester_number not in (1, 2, 3)
    ):
        raise HTTPException(status_code=404, detail="Semester not found")
    slot = year["semesters"][semester_number - 1]
    degree, program_type = degree_assignment
    toast = request.session.pop("planner_toast", None)
    return templates.TemplateResponse(
        request=request,
        name="semester-plan.html",
        context={
            "user": user,
            "degree": degree,
            "program_type": program_type,
            "slot": slot,
            "academic_year_number": academic_year_number,
            "toast": toast,
        },
    )


@router.post(
    "/app/degrees/{degree_id}/plan/years/{academic_year_number}/semesters/{semester_number}/courses",
    name="add_planned_course_action",
)
async def add_planned_course_action(
    degree_id: int,
    academic_year_number: int,
    semester_number: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    course_code: str = Form(),
    course_name: str = Form(),
    description: str = Form(default=""),
    credits: int = Form(),
):
    student_degree_service = StudentDegreeService(StudentDegreeRepository(db))
    if student_degree_service.get_degree_for_user(user.id, degree_id) is None:
        raise HTTPException(status_code=404, detail="Degree not found")

    plan_service = SemesterPlanService(SemesterPlanRepository(db))
    result = plan_service.add_course_to_semester(
        user.id,
        degree_id,
        academic_year_number,
        semester_number,
        course_code,
        course_name,
        description,
        credits,
    )
    toast_messages = {
        "added": ("Course added to semester.", "success"),
        "duplicate": ("This course is already in this semester.", "warning"),
        "pending": ("This semester is pending approval. You can add courses after approval or denial.", "warning"),
        "invalid_credits": ("Course credits must be greater than zero.", "warning"),
        "invalid_course": ("Enter a course code and course name.", "warning"),
        "semester_missing": ("That semester could not be found.", "warning"),
    }
    message, variant = toast_messages.get(result, ("Could not add this course.", "warning"))
    request.session["planner_toast"] = {"message": message, "variant": variant}
    return RedirectResponse(
        url=request.url_for(
            "plan_semester_detail_view",
            degree_id=degree_id,
            academic_year_number=academic_year_number,
            semester_number=semester_number,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/degrees/{degree_id}/plan/years/{academic_year_number}/semesters/{semester_number}/submit",
    name="submit_planned_semester_action",
)
async def submit_planned_semester_action(
    degree_id: int,
    academic_year_number: int,
    semester_number: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    student_degree_service = StudentDegreeService(StudentDegreeRepository(db))
    if student_degree_service.get_degree_for_user(user.id, degree_id) is None:
        raise HTTPException(status_code=404, detail="Degree not found")

    plan_service = SemesterPlanService(SemesterPlanRepository(db))
    result = plan_service.submit_semester_for_approval(
        user.id,
        degree_id,
        academic_year_number,
        semester_number,
    )
    toast_messages = {
        "submitted": ("Submitted. This semester is pending advisor approval.", "warning"),
        "pending": ("This semester is already pending approval.", "warning"),
        "empty": ("Add at least one course before submitting.", "warning"),
        "semester_missing": ("That semester could not be found.", "warning"),
    }
    message, variant = toast_messages.get(result, ("Could not submit this semester.", "warning"))
    request.session["planner_toast"] = {"message": message, "variant": variant}
    return RedirectResponse(
        url=request.url_for(
            "plan_semester_detail_view",
            degree_id=degree_id,
            academic_year_number=academic_year_number,
            semester_number=semester_number,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/degrees/{degree_id}/plan/years/{academic_year_number}/semesters/{semester_number}/complete",
    name="complete_planned_semester_action",
)
async def complete_planned_semester_action(
    degree_id: int,
    academic_year_number: int,
    semester_number: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    student_degree_service = StudentDegreeService(StudentDegreeRepository(db))
    if student_degree_service.get_degree_for_user(user.id, degree_id) is None:
        raise HTTPException(status_code=404, detail="Degree not found")

    plan_service = SemesterPlanService(SemesterPlanRepository(db))
    result = plan_service.complete_semester_for_history(
        user.id,
        degree_id,
        academic_year_number,
        semester_number,
    )
    toast_messages = {
        "completed": ("Semester marked as completed. See it under Track degree.", "success"),
        "pending": ("This semester is pending approval. Complete it after review.", "warning"),
        "empty": ("No planned or approved courses to complete.", "warning"),
        "semester_missing": ("That semester could not be found.", "warning"),
    }
    message, variant = toast_messages.get(result, ("Could not complete this semester.", "warning"))
    request.session["planner_toast"] = {"message": message, "variant": variant}
    return RedirectResponse(
        url=request.url_for(
            "plan_semester_detail_view",
            degree_id=degree_id,
            academic_year_number=academic_year_number,
            semester_number=semester_number,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/degrees/{degree_id}/plan/years/{academic_year_number}/semesters/{semester_number}/selections/{selection_id}/edit",
    name="edit_planned_course_action",
)
async def edit_planned_course_action(
    degree_id: int,
    academic_year_number: int,
    semester_number: int,
    selection_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    course_code: str = Form(),
    course_name: str = Form(),
    description: str = Form(default=""),
    credits: int = Form(),
):
    if StudentDegreeService(StudentDegreeRepository(db)).get_degree_for_user(user.id, degree_id) is None:
        raise HTTPException(status_code=404, detail="Degree not found")
    result = SemesterPlanService(SemesterPlanRepository(db)).update_course_selection(
        user.id,
        degree_id,
        academic_year_number,
        semester_number,
        selection_id,
        course_code,
        course_name,
        description,
        credits,
    )
    messages = {
        "updated": ("Course updated.", "success"),
        "duplicate": ("This course is already in this semester.", "warning"),
        "pending": ("This semester is pending approval. Editing is locked.", "warning"),
        "completed": ("This course is completed. Manage it under Track degree.", "warning"),
        "invalid_credits": ("Course credits must be greater than zero.", "warning"),
        "invalid_course": ("Enter a course code and course name.", "warning"),
        "selection_missing": ("Course selection not found.", "warning"),
    }
    message, variant = messages.get(result, ("Could not update this course.", "warning"))
    request.session["planner_toast"] = {"message": message, "variant": variant}
    return RedirectResponse(
        url=request.url_for(
            "plan_semester_detail_view",
            degree_id=degree_id,
            academic_year_number=academic_year_number,
            semester_number=semester_number,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/degrees/{degree_id}/plan/years/{academic_year_number}/semesters/{semester_number}/selections/{selection_id}/delete",
    name="delete_planned_course_action",
)
async def delete_planned_course_action(
    degree_id: int,
    academic_year_number: int,
    semester_number: int,
    selection_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if StudentDegreeService(StudentDegreeRepository(db)).get_degree_for_user(user.id, degree_id) is None:
        raise HTTPException(status_code=404, detail="Degree not found")
    result = SemesterPlanService(SemesterPlanRepository(db)).delete_course_selection(
        user.id,
        degree_id,
        academic_year_number,
        semester_number,
        selection_id,
    )
    messages = {
        "deleted": ("Course removed from this semester.", "success"),
        "pending": ("This semester is pending approval. Removing courses is locked.", "warning"),
        "completed": ("This course is completed. Manage it under Track degree.", "warning"),
        "selection_missing": ("Course selection not found.", "warning"),
    }
    message, variant = messages.get(result, ("Could not remove this course.", "warning"))
    request.session["planner_toast"] = {"message": message, "variant": variant}
    return RedirectResponse(
        url=request.url_for(
            "plan_semester_detail_view",
            degree_id=degree_id,
            academic_year_number=academic_year_number,
            semester_number=semester_number,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )