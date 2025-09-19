from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import tempfile
import os
from auth import AuthManager
from utils.file_validator import FileValidator
from models.subdomain import Subdomain
from config import config

router = APIRouter(prefix="/upload", tags=["upload"])
templates = Jinja2Templates(directory="templates")

@router.post("/")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        user = AuthManager.get_current_user(request)
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        is_valid_type, type_message = FileValidator.validate_file_type(file.filename)
        if not is_valid_type:
            raise HTTPException(status_code=400, detail=type_message)
        
        file_content = await file.read()
        file_size = len(file_content)
        
        is_valid_size, size_message = FileValidator.validate_file_size(file_size)
        if not is_valid_size:
            raise HTTPException(status_code=413, detail=size_message)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        is_valid_zip, zip_message, valid_files = FileValidator.validate_zip_file(temp_file_path)
        
        if not is_valid_zip:
            raise HTTPException(status_code=400, detail=zip_message)
        
        subdomain_name = Subdomain.generate_unique_name()
        
        target_path = os.path.join(config.SITES_FOLDER, subdomain_name)
        
        from utils.file_manager import FileManager
        success, message = FileManager.extract_zip_to_directory(temp_file_path, target_path)
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        subdomain = Subdomain(
            user_id=user.id if user else None,
            subdomain_name=subdomain_name,
            file_path=target_path,
            original_filename=file.filename
        )
        subdomain.save()
        
        return JSONResponse({
            "success": True,
            "url": subdomain.get_url(),
            "subdomain": subdomain_name,
            "filename": file.filename,
            "message": "Fayl muvaffaqiyatli yuklandi!"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)