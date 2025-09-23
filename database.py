from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
from config import config
from models.base import Base
from models.user import User
from models.subdomain import Subdomain


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = config.DATABASE_URL.replace('sqlite:///', '')
        db_url_object = URL(
            "sqlite+pysqlite",
            database=db_path
        )
        self.db_url_object = db_url_object
        self.engine = create_engine(db_url_object, echo=True)
        self.db_path = db_path
        self.init_database()
    
    def session(self):
        return Session(self.engine)
    
    def init_database(self):
        try:
            with self.session() as db_session:
                Base.metadata.create_all(bind=self.engine)
                # conn.execute('CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id)')
                # conn.execute('CREATE INDEX IF NOT EXISTS idx_subdomains_user_id ON subdomains(user_id)')
                # conn.execute('CREATE INDEX IF NOT EXISTS idx_subdomains_name ON subdomains(subdomain_name)')
        except Exception as e:
            print(f"Error initializing database: {e}")

db = Database()

