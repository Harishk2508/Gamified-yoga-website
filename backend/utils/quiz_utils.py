import os
import random
import re

IMAGE_DIR = "frontend/assets/images/reference"
NUM_QUESTIONS = 5
CORRECT_MARK = 10
WRONG_MARK = -5

def normalize_answer(s: str) -> str:
    return re.sub(r'[\s_]', '', s.strip().lower())

def select_questions():
    folders = [f for f in os.listdir(IMAGE_DIR) if os.path.isdir(os.path.join(IMAGE_DIR, f))]
    if len(folders) < NUM_QUESTIONS:
        raise Exception("Not enough yoga poses available")
    chosen = random.sample(folders, NUM_QUESTIONS)
    return [{"folder": folder, "image": f"{IMAGE_DIR}/{folder}/reference.jpg"} for folder in chosen]

def score_answers(answers, questions):
    total_score = 0
    breakdown = []
    for answer in answers:
        qid = answer['question_id']
        user_ans = answer['user_answer']
        correct_ans = questions[qid]['folder']
        correct = normalize_answer(user_ans) == normalize_answer(correct_ans)
        mark = CORRECT_MARK if correct else WRONG_MARK
        total_score += mark
        breakdown.append({
            "question_id": qid,
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "correct": correct,
            "mark": mark
        })
    total_score = max(0, total_score)
    return total_score, breakdown
