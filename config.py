# this is just configg

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    TIMEZONE = "Asia/Tashkent"
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///tinchost.db")
    
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "https://tinchost.uz/auth/callback")
    
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/tinchost_uploads")
    SITES_FOLDER = os.getenv("SITES_FOLDER", "/media/storage/sws")
    
    NGINX_CONFIG_PATH = os.getenv("NGINX_CONFIG_PATH", "/etc/nginx/sites-available/tinchost")
    NGINX_ENABLED_PATH = os.getenv("NGINX_ENABLED_PATH", "/etc/nginx/sites-enabled/tinchost")
    
    BASE_DOMAIN = os.getenv("BASE_DOMAIN", "tinchost.uz")
    
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tinchost.uz")
    
    @classmethod
    def create_directories(cls):
        Path(cls.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(cls.SITES_FOLDER).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

config = Config()
config.create_directories()
