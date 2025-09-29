from datetime import datetime, timedelta

import sqlite3

from backend.database.connection import get_db_connection

import hashlib

import secrets

class User:

    def __init__(self, id=None, username=None, email=None, password_hash=None,
                 full_name=None, brain_score=0, games_played=0,
                 created_at=None, last_login=None, is_active=1):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.brain_score = brain_score
        self.games_played = games_played  # NEW FIELD
        self.created_at = created_at
        self.last_login = last_login
        self.is_active = is_active

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == hashed

    @classmethod
    def create_user(cls, username: str, email: str, password: str, full_name: str = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            password_hash = cls.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, full_name))
            user_id = cursor.lastrowid
            conn.commit()
            return cls.get_user_by_id(user_id)
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValueError("Username already exists")
            elif "email" in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("User creation failed")
        finally:
            conn.close()

    @classmethod
    def get_user_by_username(cls, username: str):
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,)
            ).fetchone()
            if row:
                return cls(**dict(row))
            return None
        finally:
            conn.close()

    @classmethod
    def get_user_by_id(cls, user_id: int):
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
            if row:
                return cls(**dict(row))
            return None
        finally:
            conn.close()

    @classmethod
    def authenticate_user(cls, username: str, password: str):
        user = cls.get_user_by_username(username)
        if user and cls.verify_password(password, user.password_hash):
            conn = get_db_connection()
            try:
                conn.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user.id,)
                )
                conn.commit()
            finally:
                conn.close()
            return user
        return None

    def update_brain_score(self, delta_score: int):
        conn = get_db_connection()
        try:
            new_score = max(0, self.brain_score + delta_score)
            conn.execute(
                "UPDATE users SET brain_score = ? WHERE id = ?",
                (new_score, self.id)
            )
            conn.commit()
            self.brain_score = new_score
        finally:
            conn.close()

    # === MULTIPLAYER GAME INTEGRATION - NEW METHODS ===

    @classmethod
    def increment_games_played(cls, user_id: int):
        """Increment games played counter for multiplayer tracking"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Add games_played field if it doesn't exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'games_played' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN games_played INTEGER DEFAULT 0")
            
            # Increment games played
            cursor.execute("""
                UPDATE users SET games_played = games_played + 1 
                WHERE id = ?
            """, (user_id,))
            
            conn.commit()
            print(f"✅ Updated games_played for user_id: {user_id}")
        except Exception as e:
            print(f"❌ Error updating games_played: {e}")
            conn.rollback()
        finally:
            conn.close()

    @classmethod 
    def get_games_played(cls, user_id: int):
        """Get games played count for user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT games_played FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result['games_played'] if result else 0
        except:
            return 0
        finally:
            conn.close()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "brain_score": self.brain_score,
            "games_played": getattr(self, 'games_played', 0),  # Handle backward compatibility
            "created_at": self.created_at,
            "last_login": self.last_login
        }


class SimpleSession:

    @classmethod
    def create_session(cls, user_id: int) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, expires_at)
                VALUES (?, ?, ?)
            """, (session_id, user_id, expires_at))
            conn.commit()
            return session_id
        finally:
            conn.close()

    @classmethod
    def get_user_from_session(cls, session_id: str):
        if not session_id:
            return None
        conn = get_db_connection()
        try:
            row = conn.execute("""
                SELECT u.* FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.session_id = ? AND s.is_active = 1 AND s.expires_at > CURRENT_TIMESTAMP
            """, (session_id,)).fetchone()
            if row:
                return User(**dict(row))
            return None
        finally:
            conn.close()

    @classmethod
    def delete_session(cls, session_id: str):
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
        finally:
            conn.close()
