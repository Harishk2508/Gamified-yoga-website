import sqlite3
import os
from pathlib import Path

# Use absolute path to ensure consistent DB usage
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "yoga_platform.db"

def get_db_connection():
    if not DB_PATH.parent.exists():
        os.makedirs(DB_PATH.parent)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This is crucial for dict-like row access
    return conn

def initialize_database():
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                brain_score INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Add games_played column if it doesn't exist (for existing databases)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN games_played INTEGER DEFAULT 0")
            print("✅ Added games_played column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists, which is fine
            pass
            
        conn.commit()
        print("✅ Database initialized successfully with multiplayer game support")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Database initialization error: {e}")
    finally:
        conn.close()
