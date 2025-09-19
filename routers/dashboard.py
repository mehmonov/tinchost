from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from auth import AuthManager

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = AuthManager.require_auth(request)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user.to_dict()
    })