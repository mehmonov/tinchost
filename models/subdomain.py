

import os
import shutil
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import database as db
from config import config

class Subdomain:
    """Subdomain model"""
    
    def __init__(self, user_id: Optional[int] = None, subdomain_name: str = "",
                 file_path: str = "", original_filename: Optional[str] = None,
                 id: Optional[int] = None, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.subdomain_name = subdomain_name
        self.file_path = file_path
        self.original_filename = original_filename
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def save(self) -> int:
        """Save subdomain to database"""
        if self.id:
            # Update existing subdomain
            query = '''
                UPDATE subdomains 
                SET user_id = ?, subdomain_name = ?, file_path = ?, 
                    original_filename = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_query(query, (self.user_id, self.subdomain_name, self.file_path, 
                                   self.original_filename, self.id))
            return self.id
        else:
            # Create new subdomain
            query = '''
                INSERT INTO subdomains (user_id, subdomain_name, file_path, original_filename)
                VALUES (?, ?, ?, ?)
            '''
            subdomain_id = db.execute_query(query, (self.user_id, self.subdomain_name, 
                                                  self.file_path, self.original_filename))
            self.id = subdomain_id
            return subdomain_id
    
    def delete(self) -> bool:
        """Delete subdomain and its files"""
        if not self.id:
            return False
        
        try:
            if self.file_path and os.path.exists(self.file_path):
                shutil.rmtree(self.file_path)
            
            db.execute_query("DELETE FROM subdomains WHERE id = ?", (self.id,))
            return True
        except Exception as e:
            print(f"Error deleting subdomain: {e}")
            return False
    
    def update_name(self, new_name: str) -> bool:
        """Update subdomain name and move files"""
        if not self.id or not new_name:
            return False
        
        # Check if new name is available
        if self.name_exists(new_name):
            return False
        
        try:
            old_path = self.file_path
            new_path = os.path.join(config.SITES_FOLDER, new_name)
            
            # Move files if they exist
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            
            
            self.subdomain_name = new_name
            self.file_path = new_path
            self.save()
            
            return True
        except Exception as e:
            print(f"Error updating subdomain name: {e}")
            return False
    
    def get_url(self) -> str:
        """Get full URL for subdomain"""
        return f"https://{self.subdomain_name}.{config.BASE_DOMAIN}"
    
    def get_file_size(self) -> int:
        """Get total size of files in bytes"""
        if not os.path.exists(self.file_path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.file_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def get_file_count(self) -> int:
        """Get total number of files"""
        if not os.path.exists(self.file_path):
            return 0
        
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(self.file_path):
            file_count += len(filenames)
        return file_count
    
    @classmethod
    def get_by_id(cls, subdomain_id: int) -> Optional['Subdomain']:
        """Get subdomain by ID"""
        result = db.execute_query("SELECT * FROM subdomains WHERE id = ?", (subdomain_id,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                user_id=row['user_id'],
                subdomain_name=row['subdomain_name'],
                file_path=row['file_path'],
                original_filename=row['original_filename'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None
    
    @classmethod
    def get_by_name(cls, subdomain_name: str) -> Optional['Subdomain']:
        """Get subdomain by name"""
        result = db.execute_query("SELECT * FROM subdomains WHERE subdomain_name = ?", (subdomain_name,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                user_id=row['user_id'],
                subdomain_name=row['subdomain_name'],
                file_path=row['file_path'],
                original_filename=row['original_filename'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int) -> List['Subdomain']:
        """Get all subdomains for a user"""
        result = db.execute_query("SELECT * FROM subdomains WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        subdomains = []
        for row in result:
            subdomains.append(cls(
                id=row['id'],
                user_id=row['user_id'],
                subdomain_name=row['subdomain_name'],
                file_path=row['file_path'],
                original_filename=row['original_filename'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return subdomains
    
    @classmethod
    def get_all(cls) -> List['Subdomain']:
        """Get all subdomains"""
        result = db.execute_query("SELECT * FROM subdomains ORDER BY created_at DESC")
        subdomains = []
        for row in result:
            subdomains.append(cls(
                id=row['id'],
                user_id=row['user_id'],
                subdomain_name=row['subdomain_name'],
                file_path=row['file_path'],
                original_filename=row['original_filename'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return subdomains
    
    @classmethod
    def name_exists(cls, subdomain_name: str) -> bool:
        """Check if subdomain name exists"""
        result = db.execute_query("SELECT id FROM subdomains WHERE subdomain_name = ?", (subdomain_name,))
        return len(result) > 0
    
    @classmethod
    def generate_unique_name(cls, base_name: str = None) -> str:
        """Generate unique 5-character random subdomain name"""
        import random
        import string
        
        # Always generate 5-character random name, ignore base_name
        while True:
            name = ''.join(random.choices(string.ascii_lowercase, k=5))
            if not cls.name_exists(name):
                return name
    
    def to_dict(self) -> dict:
        """Convert subdomain to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subdomain_name': self.subdomain_name,
            'file_path': self.file_path,
            'original_filename': self.original_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'url': self.get_url(),
            'file_size': self.get_file_size(),
            'file_count': self.get_file_count()
        }
