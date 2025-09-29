# backend/routes/ai_analyzer_routes.py
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
import uuid
import json
import numpy as np

from backend.ai_analyzer.analyzer import YogaPoseAnalyzer
from backend.ai_analyzer.pose_detector import PoseDetector
from backend.ai_analyzer.hand_detector import HandDetector
from backend.ai_analyzer.visualization import LandmarkVisualizer

templates = Jinja2Templates(directory="frontend/pages")
router = APIRouter()

UPLOADS_DIR = "frontend/static/uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

ASANA_LIST = [
    "ardha_chakrasana",
    "ardha_padmasana",
    "marjari_asana_down",
    "marjari_asana_up",
    "padahastasana",
    "pada_angusthasana",
    "padmasana",
    "parvatasana",
    "Prarambhika_sthithi",
    "samakonasana",
    "shashankasana",
    "sukhasana",
    "tadasana",
    "titaliasana",
    "triyakatadasana_left",
    "triyakatadasana_right",
    "utkatasana",
    "vajrasana",
    "veerasana",
    "vrksasana",
    "vyagrasana_down",
    "vyagrasana_up"

]

@router.get("/ai_analyzer", response_class=HTMLResponse)
async def ai_analyzer_page(request: Request):
    return templates.TemplateResponse("ai_analyzer.html", {"request": request, "asanas": ASANA_LIST})

@router.post("/ai_analyzer", response_class=HTMLResponse)
async def handle_ai_upload(request: Request, asana_name: str = Form(...), upload_file: UploadFile = File(...)):
    # Normalize input key
    asana_key = asana_name.lower().replace(" ", "_")
    keypoints_path = r"D:\base_codes\data\asana_keypoints.json"

    # Load reference data
    with open(keypoints_path, "r") as f:
        asana_data = json.load(f)

    if asana_key not in asana_data:
        return templates.TemplateResponse("ai_analyzer.html", {
            "request": request,
            "asanas": ASANA_LIST,
            "error": f"No keypoints found for {asana_name}. Please select another asana."
        })

    ref_pose = np.array(asana_data[asana_key]["pose_keypoints"][0])
    ref_left_hand = np.array(asana_data[asana_key].get("hand_left")) if asana_data[asana_key].get("hand_left") else None
    ref_right_hand = np.array(asana_data[asana_key].get("hand_right")) if asana_data[asana_key].get("hand_right") else None

    # Save uploaded image
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(upload_file.filename)[-1]
    file_path = os.path.join(UPLOADS_DIR, f"{file_id}{ext}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Initialize detector and analyzer instances once (or import at module level)
    pose_detector = PoseDetector()
    hand_detector = HandDetector()
    analyzer = YogaPoseAnalyzer("AIzaSyCpDy7Voq44h9xnvITWmMP_1nR1cPWGD6c")

    # Detect keypoints for uploaded image
    user_pose, pose_result, np_img = pose_detector.detect_from_image(file_path)
    hand_landmarks, hand_detection_result, _ = hand_detector.detect_from_image(file_path)
    left_hand_kp, right_hand_kp = hand_landmarks

    # Convert user data to numpy and squeeze extra dims
    user_pose = np.squeeze(user_pose)

    # Calculate similarity score only
    sim_score, _, _ = analyzer.combined_similarity(
        ref_pose, user_pose,
        ref_left_hand, left_hand_kp,
        ref_right_hand, right_hand_kp
    )

    # Mirror detection
    is_mirrored = analyzer.detect_mirror(ref_pose, user_pose)

    # Generate corrections and feedback
    corrections = analyzer.generate_angle_based_corrections(ref_pose, user_pose, sim_score, is_mirrored, None)
    feedback = analyzer.generate_realistic_feedback(asana_name, sim_score, sim_score, None, corrections, is_mirrored)

    # Fetch detailed asana info (from Gemini API or fallback)
    asana_info = analyzer.fetch_asana_benefits_and_tips(asana_name)

    # Annotate and save visualized image
    visualizer = LandmarkVisualizer()
    annotated_img = visualizer.draw_combined_landmarks(np_img, pose_result, hand_detection_result)
    annotated_path = os.path.join(UPLOADS_DIR, f"{file_id}_annotated.png")
    from matplotlib import pyplot as plt
    plt.imsave(annotated_path, annotated_img)

    return templates.TemplateResponse("ai_report.html", {
        "request": request,
        "asana_name": asana_name,
        "similarity_score": sim_score,
        "asana_info": asana_info,
        "feedback": feedback,
        "corrections": corrections,
        "annotated_image": f"/static/uploads/{file_id}_annotated.png"
    })
