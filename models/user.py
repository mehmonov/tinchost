from datetime import datetime
from typing import Optional, List
from database import db

class User:
    def __init__(self, github_id: Optional[int] = None, username: str = "", 
                 email: Optional[str] = None, avatar_url: Optional[str] = None, 
                 id: Optional[int] = None, created_at: Optional[datetime] = None):
        self.id = id
        self.github_id = github_id
        self.username = username
        self.email = email
        self.avatar_url = avatar_url
        self.created_at = created_at or datetime.utcnow()
    
    def save(self) -> int:
        if self.id:
            # Update existing user
            query = '''
                UPDATE users 
                SET github_id = ?, username = ?, email = ?, avatar_url = ?
                WHERE id = ?
            '''
            db.execute_query(query, (self.github_id, self.username, self.email, self.avatar_url, self.id))
            return self.id
        else:
            # Create new user
            query = '''
                INSERT INTO users (github_id, username, email, avatar_url)
                VALUES (?, ?, ?, ?)
            '''
            user_id = db.execute_query(query, (self.github_id, self.username, self.email, self.avatar_url))
            self.id = user_id
            return user_id
    
    def delete(self) -> bool:
        """Delete user from database"""
        if not self.id:
            return False
        
        try:
            # First delete all user's subdomains
            from models.subdomain import Subdomain
            subdomains = self.get_subdomains()
            for subdomain in subdomains:
                subdomain.delete()
            
            # Delete user
            db.execute_query("DELETE FROM users WHERE id = ?", (self.id,))
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_subdomains(self) -> List['Subdomain']:
        """Get all subdomains for this user"""
        if not self.id:
            return []
        
        from models.subdomain import Subdomain
        return Subdomain.get_by_user_id(self.id)
    
    def is_admin(self) -> bool:
        """Check if user is admin - only the pre-configured admin from env"""
        from config import config
        return self.username == config.ADMIN_USERNAME and self.id == -1
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Get user by ID"""
        result = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                github_id=row['github_id'],
                username=row['username'],
                email=row['email'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
        return None
    
    @classmethod
    def get_by_github_id(cls, github_id: int) -> Optional['User']:
        """Get user by GitHub ID"""
        result = db.execute_query("SELECT * FROM users WHERE github_id = ?", (github_id,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                github_id=row['github_id'],
                username=row['username'],
                email=row['email'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
        return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username"""
        result = db.execute_query("SELECT * FROM users WHERE username = ?", (username,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                github_id=row['github_id'],
                username=row['username'],
                email=row['email'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
        return None
    
    @classmethod
    def get_all(cls) -> List['User']:
        """Get all users"""
        result = db.execute_query("SELECT * FROM users ORDER BY created_at DESC")
        users = []
        for row in result:
            users.append(cls(
                id=row['id'],
                github_id=row['github_id'],
                username=row['username'],
                email=row['email'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            ))
        return users
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'github_id': self.github_id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_admin': self.is_admin()
        }