# backend/routes/game_routes.py - Multiplayer Game Routes
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import string
import time
import json
import os
import uuid
from PIL import Image
import io
import threading
from typing import Dict
from pathlib import Path
from backend.utils.session_manager import get_current_user_from_session
from backend.database.models import User

# Import game utilities
from backend.utils.game_utils import (
    generate_room_code, load_asana_data, calculate_ml_score,
    start_round, end_round_after_timer, process_round_results,
    rooms, file_access_lock, active_requests,
    ROUND_DURATION_SECONDS, SPEED_BONUS_POINTS, COUNTDOWN_SECONDS, INACTIVITY_TIMEOUT,
    asana_lists, asana_display_names, asana_reference_data,
    ML_ENABLED, pose_detector, hand_detector, analyzer
)

router = APIRouter()

# Pydantic models
class CreateRoomResponse(BaseModel):
    room_code: str
    host_id: str

class JoinRoomRequest(BaseModel):
    room_code: str
    player_name: str

class PlayerReadyRequest(BaseModel):
    room_code: str
    player_name: str

class StartGameRequest(BaseModel):
    room_code: str
    game_mode: str

# === BASIC API ENDPOINTS FOR DASHBOARD ===

@router.get("/current-user")
async def get_current_user_api(user_data: dict = Depends(get_current_user_from_session)):
    """Get current user info for dashboard"""
    user_info = user_data.get("user", {})
    return {
        "username": user_info.get("full_name") or user_info.get("username") or "User", 
        "email": user_info.get("email") or "user@example.com",
        "status": "authenticated"
    }

@router.get("/user/brain_score")
async def get_brain_score_api(user_data: dict = Depends(get_current_user_from_session)):
    """Get user brain score for dashboard"""
    try:
        user_info = user_data.get("user", {})
        user_id = user_info.get("id")
        if user_id:
            user = User.get_by_id(user_id)
            if user:
                return {"brain_score": getattr(user, 'brain_score', 90)}
        return {"brain_score": 90}
    except Exception as e:
        print(f"Error getting brain score: {e}")
        return {"brain_score": 90}

@router.get("/user/games_played")
async def get_games_played_api(user_data: dict = Depends(get_current_user_from_session)):
    """FIXED: Get user games played count for dashboard"""
    try:
        user_info = user_data.get("user", {})
        user_id = user_info.get("id")
        if user_id:
            user = User.get_by_id(user_id)
            if user:
                return {"games_played": getattr(user, 'games_played', 0)}
        return {"games_played": 0}
    except Exception as e:
        print(f"Error getting games played: {e}")
        return {"games_played": 0}

# FIXED: Add method to update games played count
def update_user_games_played(user_id: int) -> bool:
    """Update games played count for a user"""
    try:
        from backend.database.connection import get_db_connection
        
        conn = get_db_connection()
        try:
            # Check if games_played column exists, if not add it
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'games_played' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN games_played INTEGER DEFAULT 0")
                conn.commit()
                print("✅ Added games_played column to users table")
            
            # Update games played count
            cursor.execute("""
                UPDATE users 
                SET games_played = COALESCE(games_played, 0) + 1 
                WHERE id = ?
            """, (user_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ Updated games played count for user {user_id}")
                return True
            else:
                print(f"⚠️ No user found with id {user_id}")
                return False
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Error updating games played for user {user_id}: {e}")
        return False

# === ROOM MANAGEMENT ENDPOINTS ===

@router.post("/create-room")
def create_room(user_data: dict = Depends(get_current_user_from_session)):
    """Create a new multiplayer game room"""
    room_code = generate_room_code()
    host_id = str(uuid.uuid4())
    
    # Get user info from session
    user_info = user_data.get("user", {})
    host_name = user_info.get("full_name") or user_info.get("username") or "Host"
    
    rooms[room_code] = {
        "host_id": host_id,
        "host_user_id": user_info.get("id"),  # Store actual user ID for game tracking
        "players": [host_name],
        "player_ids": {host_name: host_id},
        "state": "waiting",
        "game_mode": None,
        "current_round": 0,
        "total_rounds": 0,
        "scores": {host_name: 0.0},
        "ready_status": {host_name: False},
        "used_asanas": set(),
        "round": None,
        "reference_used": {host_name: {}},
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "state_changed_at": datetime.utcnow()
    }
    
    print(f"🏠 Room {room_code} created with host: {host_name}")
    return CreateRoomResponse(room_code=room_code, host_id=host_id)

@router.post("/join-room")
def join_room(req: JoinRoomRequest, user_data: dict = Depends(get_current_user_from_session)):
    """Join an existing multiplayer game room"""
    room_code = req.room_code
    
    # Get user info from session
    user_info = user_data.get("user", {})
    player_name = user_info.get("full_name") or user_info.get("username") or req.player_name.strip()
    
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    if len(room["players"]) >= 2:
        raise HTTPException(status_code=400, detail="Room is full")
    
    if player_name in room["players"]:
        raise HTTPException(status_code=400, detail="Player name already taken")
    
    player_id = str(uuid.uuid4())
    room["players"].append(player_name)
    room["player_ids"][player_name] = player_id
    room["scores"][player_name] = 0.0
    room["ready_status"][player_name] = False
    room["reference_used"][player_name] = {}
    room["last_activity"] = datetime.utcnow()
    room["state_changed_at"] = datetime.utcnow()
    
    # Store player user ID for game tracking
    if "player_user_ids" not in room:
        room["player_user_ids"] = {}
    room["player_user_ids"][player_name] = user_info.get("id")
    
    print(f"👤 {player_name} joined room {room_code}")
    return {
        "message": f"{player_name} joined room {room_code}",
        "player_id": player_id,
        "is_host": False,
        "players_count": len(room["players"]),
        "players": room["players"]
    }

@router.post("/player-ready")
def player_ready(req: PlayerReadyRequest, user_data: dict = Depends(get_current_user_from_session)):
    """Mark player as ready"""
    room_code = req.room_code
    
    # Get player name from session
    user_info = user_data.get("user", {})
    player_name = user_info.get("full_name") or user_info.get("username") or req.player_name
    
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    if player_name not in room["players"]:
        raise HTTPException(status_code=400, detail="Player not in room")
    
    room["ready_status"][player_name] = True
    room["last_activity"] = datetime.utcnow()
    room["state_changed_at"] = datetime.utcnow()
    
    ready_count = sum(room["ready_status"].values())
    both_ready = ready_count == 2 and len(room["players"]) == 2
    
    if both_ready:
        room["state"] = "all_ready"
        room["state_changed_at"] = datetime.utcnow()
        print(f"✅ Both players ready in room {room_code}")
    
    return {
        "message": f"{player_name} is ready",
        "ready_count": ready_count,
        "both_ready": both_ready,
        "ready_status": room["ready_status"],
        "state_changed_at": room["state_changed_at"].isoformat()
    }

@router.get("/room-status/{room_code}")
def get_room_status(room_code: str):
    """Get current room status"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    return {
        "room_code": room_code,
        "players": room["players"],
        "state": room["state"],
        "players_count": len(room["players"]),
        "ready_status": room.get("ready_status", {}),
        "current_round": room.get("current_round", 0),
        "total_rounds": room.get("total_rounds", 0),
        "scores": room.get("scores", {}),
        "game_mode": room.get("game_mode"),
        "state_changed_at": room["state_changed_at"].isoformat(),
        "last_activity": room["last_activity"].isoformat()
    }

# === GAME FLOW ENDPOINTS ===

@router.post("/start-game")
def start_game(req: StartGameRequest, user_data: dict = Depends(get_current_user_from_session)):
    """Start the multiplayer game"""
    room_code = req.room_code
    game_mode = req.game_mode
    
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    if room["state"] != "all_ready":
        raise HTTPException(status_code=400, detail="Both players must be ready to start")
    
    room["game_mode"] = game_mode
    room["total_rounds"] = 3 if game_mode == "rapid" else 5
    room["current_round"] = 0
    room["state"] = "playing"
    room["used_asanas"] = set()
    room["last_activity"] = datetime.utcnow()
    room["state_changed_at"] = datetime.utcnow()
    
    print(f"🎮 Game started in room {room_code} - {game_mode} mode (ML: {'✅' if ML_ENABLED else '❌'})")
    return {
        "message": "Game started successfully!",
        "game_mode": game_mode,
        "total_rounds": room["total_rounds"],
        "players": room["players"],
        "state_changed_at": room["state_changed_at"].isoformat()
    }

@router.post("/start-round/{room_code}")
def api_start_round(room_code: str, background_tasks: BackgroundTasks, user_data: dict = Depends(get_current_user_from_session)):
    """Start a new game round"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    if room["state"] != "playing":
        raise HTTPException(status_code=400, detail="Game not in playing state")
    
    # Increment round ONCE per room
    if room.get("round") is None or not room.get("round", {}).get("active", False):
        room["current_round"] += 1
        start_round(room_code)
    
    # Start fallback timer
    background_tasks.add_task(end_round_after_timer, room_code)
    
    round_info = room['round']
    return {
        "message": "Round started",
        "round_number": room["current_round"],
        "total_rounds": room["total_rounds"],
        "asana": round_info["asana_display"],
        "asana_key": round_info["asana"],
        "duration": ROUND_DURATION_SECONDS,
        "state_changed_at": room["state_changed_at"].isoformat()
    }

@router.get("/round-info/{room_code}")
def get_round_info(room_code: str):
    """Get current round information"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    round_info = room.get("round")
    
    if not round_info or not round_info.get("active", False):
        game_finished = room["current_round"] >= room.get("total_rounds", 0)
        return {
            "active": False,
            "message": "No active round",
            "game_finished": game_finished,
            "state_changed_at": room["state_changed_at"].isoformat()
        }
    
    now = datetime.utcnow()
    time_left = max(0, int((round_info['end_time'] - now).total_seconds()))
    
    return {
        "active": True,
        "asana": round_info["asana_display"],
        "asana_key": round_info["asana"],
        "time_left": time_left,
        "round_number": room["current_round"],
        "total_rounds": room["total_rounds"],
        "submissions_count": len(round_info["submissions"]),
        "state_changed_at": room["state_changed_at"].isoformat()
    }

@router.post("/use-reference/{room_code}")
def use_reference(room_code: str, player_name: str = Form(...), user_data: dict = Depends(get_current_user_from_session)):
    """Record reference image usage"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    current_round = room["current_round"]
    
    # Get actual player name from session
    user_info = user_data.get("user", {})
    actual_player_name = user_info.get("full_name") or user_info.get("username") or player_name
    
    room["reference_used"][actual_player_name][current_round] = True
    room["last_activity"] = datetime.utcnow()
    
    print(f"🖼️ {actual_player_name} used reference for round {current_round}")
    return {"message": f"Reference usage recorded for {actual_player_name}"}

@router.get("/reference-image/{asana_name}")
def get_reference_image(asana_name: str):
    """Fetch reference image with updated paths"""
    with file_access_lock:
        active_requests[asana_name] = active_requests.get(asana_name, 0) + 1
        request_count = active_requests[asana_name]
    
    try:
        print(f"📷 Reference request for {asana_name} (concurrent: {request_count})")
        
        # Updated path to match base module structure
        reference_base = Path("frontend/static/assets/images/reference")
        asana_folder = reference_base / asana_name
        
        if not asana_folder.exists():
            raise HTTPException(status_code=404, detail=f"Reference folder not found for {asana_name}")
        
        # Find image files
        possible_names = ['reference', 'image', 'pose', asana_name]
        possible_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP']
        
        found_image = None
        for name in possible_names:
            for ext in possible_extensions:
                image_path = asana_folder / f"{name}{ext}"
                if image_path.exists() and image_path.is_file():
                    found_image = image_path
                    break
            if found_image:
                break
        
        if not found_image:
            try:
                image_files = [f for f in asana_folder.iterdir()
                              if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
                if image_files:
                    found_image = image_files[0]
            except Exception as e:
                print(f"❌ Error scanning folder: {e}")
        
        if not found_image:
            raise HTTPException(status_code=404, detail=f"No reference image found for {asana_name}")
        
        # Determine media type
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(found_image.suffix.lower(), 'image/jpeg')
        
        response = FileResponse(
            str(found_image),
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=300",
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "X-Content-Type-Options": "nosniff"
            }
        )
        
        print(f"✅ Serving {found_image}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    finally:
        with file_access_lock:
            if asana_name in active_requests:
                active_requests[asana_name] = max(0, active_requests[asana_name] - 1)
                if active_requests[asana_name] == 0:
                    del active_requests[asana_name]

@router.post("/upload-image/{room_code}")
async def upload_image(room_code: str, file: UploadFile = File(...), 
                      user_data: dict = Depends(get_current_user_from_session)):
    """Upload pose image for scoring"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    round_info = room.get("round")
    
    if not round_info or not round_info.get("active", False):
        raise HTTPException(status_code=400, detail="No active round")
    
    # Get player name from session
    user_info = user_data.get("user", {})
    player_name = user_info.get("full_name") or user_info.get("username") or "Player"
    
    if player_name in round_info["submissions"]:
        raise HTTPException(status_code=400, detail="Already submitted for this round")
    
    try:
        image_bytes = await file.read()
        image_id = f"{room_code}_{player_name}_{room['current_round']}_{int(time.time())}"
        
        # Updated upload path to match base module structure
        upload_dir = "frontend/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        image_path = f"{upload_dir}/{image_id}.jpg"
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        submission_time = datetime.utcnow()
        round_info["submissions"][player_name] = {
            "image_path": image_path,
            "timestamp": submission_time,
            "processed": False
        }
        
        # Track submission order for speed bonus
        round_info["submission_order"].append({
            "player": player_name,
            "timestamp": submission_time
        })
        
        room["last_activity"] = datetime.utcnow()
        room["state_changed_at"] = datetime.utcnow()
        
        submission_count = len(round_info["submissions"])
        is_first = len(round_info["submission_order"]) == 1
        
        print(f"📤 {player_name} submitted ({'FIRST' if is_first else 'SECOND'})")
        
        # Auto-progress when both players submit
        if submission_count == 2:
            print(f"🚀 Both submitted - processing ML results...")
            round_info["active"] = False
            room["state_changed_at"] = datetime.utcnow()
            process_round_results(room_code)
            
            return {
                "message": "Both players submitted - AI analyzing poses...",
                "submissions_count": submission_count,
                "is_first": is_first,
                "auto_progress": True,
                "state_changed_at": room["state_changed_at"].isoformat()
            }
        else:
            return {
                "message": f"Upload successful! {'🏃♂️ You were first (+2 bonus)!' if is_first else 'Waiting for other player...'}",
                "submissions_count": submission_count,
                "is_first": is_first,
                "auto_progress": False,
                "state_changed_at": room["state_changed_at"].isoformat()
            }
            
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@router.get("/round-results/{room_code}")
def get_round_results(room_code: str):
    """Get results for completed round"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_code]
    round_info = room.get("round")
    
    return {
        "round_number": room["current_round"],
        "asana": round_info["asana_display"],
        "results": round_info.get("scores", {}),
        "current_totals": room["scores"],
        "submission_order": round_info.get("submission_order", []),
        "state_changed_at": room["state_changed_at"].isoformat()
    }

@router.get("/game-results/{room_code}")
async def get_game_results(room_code: str):
    """FIXED: Get final game results and update user stats ONLY after successful completion"""
    if room_code not in rooms:
        print(f"❌ Room {room_code} not found in active rooms")
        print(f"📋 Active rooms: {list(rooms.keys())}")
        raise HTTPException(status_code=404, detail=f"Room {room_code} not found")
    
    room = rooms[room_code]
    players = room["players"]
    scores = room["scores"]
    
    print(f"\n🏆 === GAME RESULTS REQUEST ===")
    print(f"🏠 Room: {room_code}")
    print(f"👥 Players: {players}")
    print(f"📊 Raw scores: {scores}")
    print(f"🎮 Game mode: {room.get('game_mode', 'unknown')}")
    print(f"🔄 Current round: {room.get('current_round', 0)}")
    print(f"📝 Total rounds: {room.get('total_rounds', 0)}")
    
    # Check if game was actually completed (not abandoned)
    game_completed = room.get("current_round", 0) >= room.get("total_rounds", 0)
    
    print(f"🎯 Game completed status: {game_completed}")
    
    # Ensure consistent final scores
    final_scores = {}
    for player in players:
        raw_score = scores.get(player, 0.0)
        final_scores[player] = round(float(raw_score), 1)
    
    print(f"✅ Final scores: {final_scores}")
    
    # Determine winner correctly
    winner = "TIE"
    loser = "TIE"
    if len(players) == 2:
        player1_score = final_scores[players[0]]
        player2_score = final_scores[players[1]]
        
        if player1_score > player2_score:
            winner = players[0]
            loser = players[1]
        elif player2_score > player1_score:
            winner = players[1]
            loser = players[0]
        else:
            winner = "TIE"
            loser = "TIE"
    
    print(f"🏆 Winner: {winner}")
    
    # FIXED: Only update games played count if game was actually completed
    if game_completed:
        try:
            print(f"📊 Updating games played count for completed game...")
            
            # Update host's games played count
            host_user_id = room.get("host_user_id")
            if host_user_id:
                success = update_user_games_played(host_user_id)
                if success:
                    print(f"✅ Updated games played for host (user_id: {host_user_id})")
                else:
                    print(f"⚠️ Failed to update games played for host (user_id: {host_user_id})")
            
            # Update other player's games played count
            player_user_ids = room.get("player_user_ids", {})
            for player_name, user_id in player_user_ids.items():
                if user_id and user_id != host_user_id:
                    success = update_user_games_played(user_id)
                    if success:
                        print(f"✅ Updated games played for {player_name} (user_id: {user_id})")
                    else:
                        print(f"⚠️ Failed to update games played for {player_name} (user_id: {user_id})")
                        
        except Exception as e:
            print(f"⚠️ Failed to update user statistics: {e}")
    else:
        print(f"⚠️ Game not completed - skipping games played count update")
    
    # Complete result structure with feedback
    result = {
        "players": players,
        "scores": final_scores,
        "total_rounds": room.get("total_rounds", 3),
        "current_rounds_played": room.get("current_round", 0),
        "game_mode": room.get("game_mode", "rapid"),
        "winner": winner,
        "loser": loser,
        "completed": game_completed,
        "room_code": room_code,
        "timestamp": datetime.now().isoformat(),
        "ml_enabled": ML_ENABLED,
        "game_state": room.get("state", "completed"),
        "round_history": room.get("round_history", {})
    }
    
    print(f"📤 Returning result: {result}")
    print(f"🔚 === END GAME RESULTS ===\n")
    
    return result

@router.get("/health")
def health_check():
    """Health check for multiplayer game system"""
    return {
        "status": "healthy",
        "ml_enabled": ML_ENABLED,
        "message": f"🤖 AI Yoga Challenge {'READY' if ML_ENABLED else 'FALLBACK MODE'}!",
        "models_loaded": {
            "pose_detector": pose_detector is not None,
            "hand_detector": hand_detector is not None,
            "analyzer": analyzer is not None,
            "gemini_enabled": analyzer.client is not None if analyzer else False
        },
        "reference_asanas": len(asana_reference_data),
        "version": "Integrated Multiplayer Game Module"
    }
