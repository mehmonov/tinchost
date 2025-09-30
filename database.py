from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
from config import config

class Database:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            db_url = config.DATABASE_URL
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=True)
    
    def session(self) -> Session:
        return Session(self.engine)
    
    def init_database(self):
        try:
            from models.base import Base
            from models.user import User
            from models.subdomain import Subdomain
            from models.admin import Admin
            Base.metadata.create_all(bind=self.engine)

        except Exception as e:
            print(f"Error initializing database: {e}")

db = Database()

