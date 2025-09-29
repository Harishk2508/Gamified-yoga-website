# backend/routes/auth_routes.py - WITH PROPER ERROR HANDLING
from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.database.models import User
from backend.utils.session_manager import (
    create_user_session, get_current_user_from_session,
    delete_user_session
)

router = APIRouter()
templates = Jinja2Templates(directory="frontend/pages")

from fastapi import Depends
from backend.database.models import User
from backend.routes.auth_routes import get_current_user_from_session

@router.get("/user/brain_score")
async def get_brain_score(user_data: dict = Depends(get_current_user_from_session)):
    try:
        # FIX: Access the user data from the nested structure
        user_info = user_data.get("user", {})
        user = User(
            id=user_info.get("id"),
            username=user_info.get("username"),
            email=user_info.get("email"),
            password_hash=user_info.get("password_hash"),
            full_name=user_info.get("full_name"),
            brain_score=user_info.get("brain_score", 0),
            games_played=user_info.get("games_played", 0),  # NEW FIELD
            created_at=user_info.get("created_at"),
            last_login=user_info.get("last_login"),
            is_active=user_info.get("is_active", 1),
        )
        
        return {"brain_score": user.brain_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching brain score: {str(e)}")

# === MULTIPLAYER GAME INTEGRATION - NEW ENDPOINT ===
@router.get("/user/games_played")
async def get_games_played(user_data: dict = Depends(get_current_user_from_session)):
    """Get games played count for dashboard"""
    try:
        user_info = user_data.get("user", {})
        user_id = user_info.get("id")
        
        if user_id:
            games_played = User.get_games_played(user_id)
            return {"games_played": games_played}
        
        return {"games_played": 0}
    except Exception as e:
        print(f"Error getting games played: {e}")
        return {"games_played": 0}

@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form("")
):
    """User registration with proper error handling"""
    try:
        # Validate inputs
        if len(username) < 3:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "error": "Username must be at least 3 characters long",
                "username": username,
                "email": email,
                "full_name": full_name
            })
        
        if len(password) < 6:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "error": "Password must be at least 6 characters long",
                "username": username,
                "email": email,
                "full_name": full_name
            })
        
        # Create user
        user = User.create_user(username, email, password, full_name or None)
        
        # Create session and redirect to home
        session_id = create_user_session(user)
        response = RedirectResponse(url="/home", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=86400
        )
        return response
        
    except ValueError as e:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": str(e),
            "username": username if "username" not in str(e).lower() else "",
            "email": email if "email" not in str(e).lower() else "",
            "full_name": full_name
        })

@router.post("/signin")
async def signin(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """User login with proper error handling"""
    # Authenticate user
    user = User.authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("signin.html", {
            "request": request,
            "error": "Invalid username or password. Please try again.",
            "username": username
        })
    
    # Create session and redirect
    session_id = create_user_session(user)
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400
    )
    return response

@router.post("/logout")
async def logout(request: Request):
    """Simple logout"""
    session_id = request.cookies.get("session_id")
    delete_user_session(session_id)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response

@router.get("/current-user")
async def get_current_user(user_data: dict = Depends(get_current_user_from_session)):
    """Get current user info"""
    return user_data
