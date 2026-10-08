from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.advisor_review import AdvisorReviewRepository
from app.services.advisor_review_service import AdvisorReviewService
from . import router, templates


@router.get("/admin/advising", response_class=HTMLResponse, name="advisor_reviews_view")
async def advisor_reviews_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    advisor_repository = AdvisorReviewRepository(db)
    advisor_service = AdvisorReviewService(advisor_repository)
    pending_reviews = advisor_service.get_pending_semesters()
    advisor_error = request.session.pop("advisor_error", None)
    advisor_notice = request.session.pop("advisor_notice", None)
    return templates.TemplateResponse(
        request=request,
        name="advisor-reviews.html",
        context={
            "user": user,
            "pending_reviews": pending_reviews,
            "advisor_error": advisor_error,
            "advisor_notice": advisor_notice,
        },
    )


@router.post("/admin/advising/{student_id}/{semester_id}/decision", name="advisor_decide_semester_action")
async def advisor_decide_semester_action(
    student_id: int,
    semester_id: int,
    request: Request,
    user: AdminDep,
    db: SessionDep,
    decision: str = Form(),
    notes: str = Form(default=""),
    redirect_to: str = Form(default=""),
):
    advisor_repository = AdvisorReviewRepository(db)
    advisor_service = AdvisorReviewService(advisor_repository)
    result = advisor_service.decide_semester(
        user.id,
        student_id,
        semester_id,
        decision,
        notes,
    )
    if result == "notes_required":
        request.session["advisor_error"] = "Enter a reason before denying this semester."
    elif result == "decided":
        request.session["advisor_notice"] = (
            "Semester approved." if decision == "approved" else "Semester denied."
        )
    elif result == "review_missing":
        raise HTTPException(status_code=404, detail="Pending review not found")
    elif result == "advisor_missing":
        raise HTTPException(status_code=403, detail="Advisor profile not found")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid decision")

    target = redirect_to or request.url_for("advisor_reviews_view")
    return RedirectResponse(
        url=target,
        status_code=status.HTTP_303_SEE_OTHER,
    )