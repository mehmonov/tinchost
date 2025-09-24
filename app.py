from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from config import config
from auth import AuthManager
from routers import auth, upload, subdomain, dashboard, admin

app = FastAPI(
    title="TincHost",
    description="Static Site Deployment Platform",
    version="1.0.0"
)

app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(subdomain.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = AuthManager.get_current_user(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user.to_dict() if user else None
    })

@app.get("/health") # just check 
async def health_check():
    return {"status": "healthy", "service": "tinchost"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
