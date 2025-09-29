# backend/utils/session_manager.py - SIMPLIFIED VERSION
from fastapi import Request, HTTPException, status
from backend.database.models import User, SimpleSession
from typing import Optional

def create_user_session(user: User) -> str:
    """Create simple session for user"""
    return SimpleSession.create_session(user.id)

def get_current_user_from_session(request: Request) -> dict:
    """Get current user from session - SIMPLIFIED"""
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to continue"
        )
    
    user = SimpleSession.get_user_from_session(session_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again."
        )
    
    return {"user": user.to_dict()}

def delete_user_session(session_id: str):
    """Delete user session"""
    if session_id:
        SimpleSession.delete_session(session_id)

def get_optional_user(request: Request) -> Optional[dict]:
    """Get user if logged in, None otherwise"""
    try:
        return get_current_user_from_session(request)
    except HTTPException:
        return None
