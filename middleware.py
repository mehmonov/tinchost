from fastapi import Request, HTTPException, status
from functools import wraps
from auth import AuthManager


def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = AuthManager.get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login required"
            )
        return await func(request, *args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = AuthManager.get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login required"
            )
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return await func(request, *args, **kwargs)
    return wrapper

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            if request.url.path.startswith("/admin"):
                user = AuthManager.get_current_user(request)
                if not user or not user.is_admin:
                    response = HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admin access required"
                    )
                    await response(scope, receive, send)
                    return
            
            elif request.url.path.startswith("/dashboard"):
                user = AuthManager.get_current_user(request)
                if not user:
                    response = HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Login required"
                    )
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
