from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from auth import AuthManager
from models.subdomain import Subdomain
from models.user import User

router = APIRouter(prefix="/subdomain", tags=["subdomain"])

@router.post("/edit")
async def edit_subdomain(
    request: Request,
    subdomain_id: int = Form(...),
    new_name: str = Form(...)
):
    user = AuthManager.require_auth(request)
    
    subdomain = Subdomain.get_by_id(subdomain_id)
    if not subdomain:
        raise HTTPException(status_code=404, detail="Subdomain not found")
    
    if subdomain.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not new_name or len(new_name) < 3:
        raise HTTPException(status_code=400, detail="Subdomain name too short")
    
    if Subdomain.name_exists(new_name):
        raise HTTPException(status_code=409, detail="Subdomain name already exists")
    
    success = subdomain.update_name(new_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update subdomain")
    
    
    return JSONResponse({
        "success": True,
        "subdomain": new_name,
        "url": subdomain.get_url(),
        "message": "Subdomain updated successfully"
    })

@router.get("/list")
async def list_subdomains(request: Request):
    user = AuthManager.require_auth(request)
    
    subdomains = user.get_subdomains()
    return JSONResponse({
        "subdomains": [s.to_dict() for s in subdomains]
    })

@router.delete("/{subdomain_id}")
async def delete_subdomain(request: Request, subdomain_id: int):
    user = AuthManager.require_auth(request)
    
    subdomain = Subdomain.get_by_id(subdomain_id)
    if not subdomain:
        raise HTTPException(status_code=404, detail="Subdomain not found")
    
    if subdomain.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = subdomain.delete()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete subdomain")
    
    from utils.nginx_manager import NginxManager
    NginxManager.reload_nginx()
    
    return JSONResponse({
        "success": True,
        "message": "Subdomain deleted successfully"
    })

@router.get("/{subdomain_name}")
async def get_subdomain(subdomain_name: str):
    subdomain = Subdomain.get_by_name(subdomain_name)
    if not subdomain:
        raise HTTPException(status_code=404, detail="Subdomain not found")
    
    return JSONResponse(subdomain.to_dict())
