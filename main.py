from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

# Backend imports
from backend.routes.auth_routes import router as auth_router
from backend.routes.ai_analyzer_routes import router as ai_analyzer_router
from backend.routes.quiz_routes import router as quiz_router
from backend.database.connection import initialize_database
from backend.routes.game_routes import router as multiplayer_router

# NEW: Pose Detection Module Import
from backend.routes.pose_detection_routes import router as pose_detection_router

app = FastAPI(
    title="Harish Yoga Platform",
    description="Professional Modular Yoga Platform with Authentication",
    version="1.0.0"
)

# Initialize database
initialize_database()

# Mount static files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/css", StaticFiles(directory="frontend/static/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/static/js"), name="js")

templates = Jinja2Templates(directory="frontend/pages")

# ===== FRONTEND ROUTES (YOUR ORIGINAL BASE MODULE) =====

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Original landing page - UNCHANGED"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """Dashboard page after login - UNCHANGED"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/learning", response_class=HTMLResponse)
async def learning_page(request: Request):
    return templates.TemplateResponse("learning.html", {"request": request})

@app.get("/quiz", response_class=HTMLResponse)
async def brain_tester_page(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})

# ===== NEW MULTIPLAYER ROUTES (ADDED) =====

@app.get("/multiplayer", response_class=HTMLResponse)
async def multiplayer_index(request: Request):
    """NEW: Multiplayer landing page"""
    return templates.TemplateResponse("multiplayer_index.html", {"request": request})

@app.get("/multiplayer/host", response_class=HTMLResponse)
async def multiplayer_host(request: Request):
    """NEW: Host game page"""
    return templates.TemplateResponse("multiplayer_host.html", {"request": request})

@app.get("/multiplayer/player", response_class=HTMLResponse)
async def multiplayer_player(request: Request):
    """NEW: Join game page"""
    return templates.TemplateResponse("multiplayer_player.html", {"request": request})

@app.get("/multiplayer/game", response_class=HTMLResponse)
async def multiplayer_game(request: Request):
    """NEW: Game interface"""
    return templates.TemplateResponse("multiplayer_game.html", {"request": request})

@app.get("/multiplayer/results", response_class=HTMLResponse)
async def multiplayer_results(request: Request):
    """NEW: Game results page"""
    return templates.TemplateResponse("multiplayer_results.html", {"request": request})

# ===== NEW: POSE DETECTION FRONTEND ROUTE =====

@app.get("/pose-detector", response_class=HTMLResponse)
async def pose_detector_page(request: Request):
    """NEW: Pose Detection page"""
    return templates.TemplateResponse("pose_detector.html", {"request": request})

# ===== MODULE ROUTES REGISTRATION =====

app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(ai_analyzer_router, prefix="", tags=["AI Analyzer"])
app.include_router(quiz_router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(multiplayer_router, prefix="/api", tags=["Multiplayer"])

# NEW: Pose Detection API Routes
app.include_router(pose_detection_router, prefix="/api/pose", tags=["Pose Detection"])

# ===== HEALTH CHECK =====

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "yoga-platform",
        "version": "1.0.0",
        "modules": ["authentication", "learning", "quiz", "multiplayer", "pose-detection"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
