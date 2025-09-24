import sqlite3
from config import config

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = config.DATABASE_URL.replace('sqlite:///', '')
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    github_id INTEGER UNIQUE,
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    avatar_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS subdomains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    subdomain_name VARCHAR(255) UNIQUE NOT NULL,
                    original_filename VARCHAR(255),
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            

            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_subdomains_user_id ON subdomains(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_subdomains_name ON subdomains(subdomain_name)')
            
            conn.commit()
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        conn = self.get_connection()
        try:
            if params:
                cursor = conn.execute(query, params)
            else:
                cursor = conn.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

db = Database()

# Admin is now handled through environment variables only - no database table needed