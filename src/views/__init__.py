from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from services.challenge import ChallengeService
from views.challenge import challenge_view

view = APIRouter()
templates = Jinja2Templates(directory="views/templates")


@view.get("/")
async def index(
    request: Request,
    page: int = Query(1),
    service: ChallengeService = Depends(ChallengeService),
):
    challs = {
        "data": None,
        "total": 0,
        "join": None,
    }
    if service._user:
        challs = service.list_challenges(page)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": service._user,
            "challenges": challs["data"],
            "page": page,
            "total_pages": challs["total"] // 50,
            "join": challs["join"],
        },
    )


@view.get("/signup")
async def signup(request: Request):
    return RedirectResponse("/signin")
    # return templates.TemplateResponse("signup.html", {"request": request})


@view.get("/signin")
async def login(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})


view.include_router(challenge_view, prefix="/challenge")
