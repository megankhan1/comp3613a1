from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.repositories.student_degree import StudentDegreeRepository
from app.services.student_degree_service import StudentDegreeService


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    student_degree_repo = StudentDegreeRepository(db)
    student_degree_service = StudentDegreeService(student_degree_repo)
    degree_cards = student_degree_service.get_degree_cards(user.id)

    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "degree_cards": degree_cards,
        }
    )


@router.get("/app/degrees/{degree_id}", response_class=HTMLResponse, name="degree_actions_view")
async def degree_actions_view(
    degree_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    student_degree_repo = StudentDegreeRepository(db)
    student_degree_service = StudentDegreeService(student_degree_repo)
    degree_cards = student_degree_service.get_degree_cards(user.id)
    selected_degree = next(
        (
            (degree, program_type)
            for degree, program_type in degree_cards
            if degree.degree_id == degree_id
        ),
        None,
    )
    if selected_degree is None:
        raise HTTPException(status_code=404, detail="Degree not found")

    degree, program_type = selected_degree
    return templates.TemplateResponse(
        request=request,
        name="degree-actions.html",
        context={"user": user, "degree": degree, "program_type": program_type},
    )