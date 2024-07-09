from fastapi import APIRouter, requests, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from services.challenge import ChallengeService

challenge_view = APIRouter()
templates = Jinja2Templates(directory="views/templates")


@challenge_view.get("/{id}")
async def index(
    id: int,
    request: requests.Request,
    service: ChallengeService = Depends(ChallengeService),
):
    if not service._user:
        return RedirectResponse("/login")
    chall = service.get_challenge(id)
    if not chall["joined"]:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        "challenge.html",
        {
            "request": request,
            "challenge": chall,
            "user": service._user,
        },
    )
