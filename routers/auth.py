from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from auth import AuthManager

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/github")
async def github_login(request: Request):
    auth_url = await AuthManager.get_github_auth_url(request)
    return RedirectResponse(auth_url)

@router.get("/callback")
async def github_callback(request: Request):
    try:
        user = await AuthManager.handle_github_callback(request)
        AuthManager.create_session(request, user)
        return RedirectResponse("/dashboard", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(request: Request):
    AuthManager.logout(request)
    return RedirectResponse("/", status_code=302)