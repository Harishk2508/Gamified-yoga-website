import os
import random
import re
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from pydantic import BaseModel
from backend.database.models import User
from backend.database.connection import get_db_connection
from backend.routes.auth_routes import get_current_user_from_session

router = APIRouter()

IMAGE_DIR = "frontend/static/assets/images/reference"
NUM_QUESTIONS = 5
CORRECT_MARK = 10
WRONG_MARK = -5

class AnswerInput(BaseModel):
    question_id: int
    user_answer: str

class QuizSubmission(BaseModel):
    answers: List[AnswerInput]
    raw_questions: List[Dict]

def normalize_answer(text: str) -> str:
    return re.sub(r"[\s_]", "", text.strip().lower()) if isinstance(text, str) else ""

@router.get("/questions")
def get_quiz_questions(user_data: dict = Depends(get_current_user_from_session)):
    all_folders = [f for f in os.listdir(IMAGE_DIR) if os.path.isdir(os.path.join(IMAGE_DIR, f))]
    if len(all_folders) < NUM_QUESTIONS:
        raise HTTPException(status_code=500, detail="Not enough poses for quiz.")
    chosen_folders = random.sample(all_folders, NUM_QUESTIONS)
    questions = [{"id": i, "image": f"/static/assets/images/reference/{folder}/reference.jpg"} for i, folder in enumerate(chosen_folders)]
    raw_questions = [{"folder": folder} for folder in chosen_folders]
    return {"questions": questions, "raw_questions": raw_questions}

@router.post("/submit")
def submit_quiz(submission: QuizSubmission, user_data: dict = Depends(get_current_user_from_session)):
    print(f"DEBUG: user_data received: {user_data}")
    
    # FIX: Access the user data from the nested structure
    user_info = user_data.get("user", {})
    user_id = user_info.get("id")
    
    print(f"DEBUG: extracted user_id: {user_id}")
    
    if not user_id:
        raise HTTPException(status_code=403, detail="User not authenticated.")

    total_score = sum(CORRECT_MARK if normalize_answer(ans.user_answer) == normalize_answer(submission.raw_questions[ans.question_id]["folder"]) else WRONG_MARK for ans in submission.answers)
    total_score = max(0, total_score)
    
    breakdown = [
        {
            "question_id": ans.question_id,
            "user_answer": ans.user_answer,
            "correct_answer": submission.raw_questions[ans.question_id]["folder"],
            "correct": normalize_answer(ans.user_answer) == normalize_answer(submission.raw_questions[ans.question_id]["folder"]),
            "mark": CORRECT_MARK if normalize_answer(ans.user_answer) == normalize_answer(submission.raw_questions[ans.question_id]["folder"]) else WRONG_MARK,
        }
        for ans in submission.answers
    ]

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT brain_score FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        
        current_brain_score = row["brain_score"]
        new_brain_score = current_brain_score + total_score
        
        cursor.execute("UPDATE users SET brain_score = ? WHERE id = ?", (new_brain_score, user_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

    return {"score": total_score, "breakdown": breakdown, "new_brain_score": new_brain_score}
