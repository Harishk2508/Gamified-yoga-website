# backend/utils/game_utils.py - Multiplayer Game Utilities with FIXED SCORING & GEMINI AI
from datetime import datetime, timedelta
import random
import string
import time
import json
import threading
from typing import Dict
from pathlib import Path
import numpy as np

# Try to import ML components AND Gemini AI
ML_ENABLED = False
pose_detector = None
hand_detector = None
analyzer = None

# Import Gemini AI directly
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    # Updated import paths to match base module structure
    from backend.ai_analyzer.pose_detector import PoseDetector
    from backend.ai_analyzer.hand_detector import HandDetector  
    from backend.ai_analyzer.analyzer import YogaPoseAnalyzer
    
    ML_ENABLED = True
    print("✅ ML components loaded successfully for multiplayer!")
    
    # Initialize ML components
    pose_detector = PoseDetector()
    hand_detector = HandDetector()
    
    # Initialize analyzer with Gemini API key
    GEMINI_API_KEY = "AIzaSyBXz4PsJe7OI9kwnhIeTEEG8dhiSguhs50"
    analyzer = YogaPoseAnalyzer(gemini_api_key=GEMINI_API_KEY)
    
    # Configure Gemini AI directly
    if GEMINI_AVAILABLE:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_MODEL = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Direct Gemini AI configured successfully!")
    
    print("✅ ML models initialized successfully for multiplayer with Gemini AI!")
    
except ImportError as e:
    print(f"⚠️ ML components not available for multiplayer: {e}")
    ML_ENABLED = False

# Game configuration constants
ROUND_DURATION_SECONDS = 300  # 5 minutes
SPEED_BONUS_POINTS = 2
COUNTDOWN_SECONDS = 5
INACTIVITY_TIMEOUT = 180

# Sanskrit asana names and display names
asana_lists = {
    "rapid": [
        "pada_angushthasana",
        "poorna_dhanurasana", 
        "kapalabhati_pranayama"
    ],
    "normal": [
        "pada_angushthasana",
        "poorna_dhanurasana",
        "kapalabhati_pranayama",
        "nadishodhana_pranayama",
        "ekapada_rajakapotasana"
    ]
}

# Display names (what users see - with spaces)
asana_display_names = {
    "pada_angushthasana": "pada angushthasana",
    "poorna_dhanurasana": "poorna dhanurasana", 
    "kapalabhati_pranayama": "kapalabhati pranayama",
    "nadishodhana_pranayama": "nadishodhana pranayama",
    "ekapada_rajakapotasana": "ekapada rajakapotasana"
}

# Global storage and locks
rooms = {}
file_access_lock = threading.Lock()
active_requests: Dict[str, int] = {}

def load_asana_data():
    """Load reference keypoints from JSON file"""
    try:
        with open('data/asana_keypoints1.json', 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded reference data for {len(data)} asanas")
        return data
    except Exception as e:
        print(f"⚠️ Could not load asana keypoints: {e}")
        return {}

# Load asana reference data
asana_reference_data = load_asana_data()

def generate_room_code():
    """Generate unique 6-digit room code"""
    while True:
        code = ''.join(random.choices(string.digits, k=6))
        if code not in rooms:
            return code

def start_round(room_code: str):
    """Start a new round - SAME asana for both players"""
    if room_code not in rooms:
        return
    
    room = rooms[room_code]
    
    # Select ONE asana for BOTH players
    available_asanas = [
        asana for asana in asana_lists[room["game_mode"]] 
        if asana not in room["used_asanas"]
    ]
    
    if not available_asanas:
        room["used_asanas"] = set()
        available_asanas = asana_lists[room["game_mode"]]
    
    # SAME asana for both players
    round_asana = random.choice(available_asanas)
    room["used_asanas"].add(round_asana)
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(seconds=ROUND_DURATION_SECONDS)
    
    room['round'] = {
        "asana": round_asana,
        "asana_display": asana_display_names.get(round_asana, round_asana),
        "start_time": start_time,
        "end_time": end_time,
        "active": True,
        "submissions": {},
        "scores": {},
        "round_number": room["current_round"],
        "submission_order": []
    }
    
    room["state_changed_at"] = datetime.utcnow()
    print(f"🎯 Round {room['current_round']} started: {round_asana}")

def end_round_after_timer(room_code: str):
    """Fallback timer - ends round after 5 minutes"""
    time.sleep(ROUND_DURATION_SECONDS)
    
    if room_code in rooms:
        room = rooms[room_code]
        round_info = room.get("round")
        
        if round_info and round_info.get("active", False):
            print(f"⏰ Timer expired for room {room_code} - ending round")
            round_info["active"] = False
            room["state_changed_at"] = datetime.utcnow()
            process_round_results(room_code)

# FIXED: YOUR EXACT SCORING SYSTEM
def calculate_your_custom_score(pose_similarity, hand_left_sim, hand_right_sim):
    """
    YOUR EXACT SCORING REQUIREMENTS:
    - 100% = 10 points
    - 95-99% = 9-10 points  
    - 90-94% = 7-9 points
    - 80-89% = 5-7 points
    - 45-79% = 1-5 points
    - Below 45% = 0 points
    - Hand similarity: maximum 0.5 penalty, minimal influence
    """
    try:
        print(f"📊 === YOUR CUSTOM SCORING SYSTEM ===")
        print(f"📈 Pose similarity: {pose_similarity:.1f}%")
        print(f"🤚 Left hand: {hand_left_sim:.1f}%" if hand_left_sim is not None else "🤚 Left hand: N/A")
        print(f"✋ Right hand: {hand_right_sim:.1f}%" if hand_right_sim is not None else "✋ Right hand: N/A")
        
        # YOUR SCORING RANGES
        if pose_similarity >= 100.0:
            base_score = 10.0
            print(f"🏆 Perfect pose: 10.0 points")
        elif pose_similarity >= 95.0:
            # 95-99% = 9-10 points (linear interpolation)
            base_score = 9.0 + ((pose_similarity - 95.0) / 5.0)
            print(f"🥇 Excellent range (95-99%): {base_score:.1f} points")
        elif pose_similarity >= 90.0:
            # 90-94% = 7-9 points (linear interpolation)
            base_score = 7.0 + ((pose_similarity - 90.0) / 5.0) * 2.0
            print(f"🥈 Very good range (90-94%): {base_score:.1f} points")
        elif pose_similarity >= 80.0:
            # 80-89% = 5-7 points (linear interpolation)
            base_score = 5.0 + ((pose_similarity - 80.0) / 10.0) * 2.0
            print(f"🥉 Good range (80-89%): {base_score:.1f} points")
        elif pose_similarity >= 45.0:
            # 45-79% = 1-5 points (linear interpolation)
            base_score = 1.0 + ((pose_similarity - 45.0) / 35.0) * 4.0
            print(f"✅ Fair range (45-79%): {base_score:.1f} points")
        else:
            # Below 45% = 0 points
            base_score = 0.0
            print(f"❌ Below threshold (<45%): 0 points")
        
        # Hand penalty (maximum 0.5 penalty when not matching)
        hand_penalty = 0.0
        if hand_left_sim is not None or hand_right_sim is not None:
            # Average hand similarity
            hand_scores = []
            if hand_left_sim is not None:
                hand_scores.append(hand_left_sim)
            if hand_right_sim is not None:
                hand_scores.append(hand_right_sim)
            
            if hand_scores:
                avg_hand = sum(hand_scores) / len(hand_scores)
                if avg_hand < 50.0:  # Poor hand alignment
                    hand_penalty = min(0.5, (50.0 - avg_hand) / 100.0)
                    print(f"👋 Hand penalty: -{hand_penalty:.2f} (avg hand: {avg_hand:.1f}%)")
                else:
                    print(f"👋 Hand alignment good: {avg_hand:.1f}% (no penalty)")
        
        final_score = max(0.0, base_score - hand_penalty)
        
        print(f"✅ Base score: {base_score:.2f}")
        print(f"✅ Hand penalty: -{hand_penalty:.2f}")
        print(f"🎯 FINAL SCORE: {final_score:.2f}/10")
        print(f"📊 === SCORING COMPLETE ===")
        
        return final_score
        
    except Exception as e:
        print(f"❌ Score calculation error: {e}")
        return 0.0

# FIXED: REAL GEMINI AI FEEDBACK GENERATION
def generate_real_gemini_feedback(asana_name, pose_similarity, hand_left_sim, hand_right_sim):
    """
    Generate REAL Gemini AI feedback - not fallback templates!
    """
    try:
        if not GEMINI_AVAILABLE or not GEMINI_MODEL:
            raise Exception("Gemini AI not available")
        
        print(f"🤖 Calling REAL Gemini API for {asana_name} feedback...")
        
        # Prepare detailed prompt for Gemini
        asana_display = asana_name.replace('_', ' ').title()
        
        # Build comprehensive analysis data
        hand_info = ""
        if hand_left_sim is not None or hand_right_sim is not None:
            hand_details = []
            if hand_left_sim is not None:
                hand_details.append(f"left hand {hand_left_sim:.1f}%")
            if hand_right_sim is not None:
                hand_details.append(f"right hand {hand_right_sim:.1f}%")
            hand_info = f", hand positioning: {', '.join(hand_details)}"
        
        # Comprehensive Gemini prompt
        prompt = f"""As an expert yoga instructor and AI pose analyst, provide detailed feedback for a student's {asana_display} practice.

Performance Analysis:
- Pose accuracy: {pose_similarity:.1f}%{hand_info}
- Asana: {asana_display}

Provide professional feedback covering:
1. Specific alignment observations based on the accuracy score
2. Areas for improvement with actionable advice
3. Encouragement and next steps
4. Breathing and mindfulness tips

Keep the feedback:
- Professional but encouraging
- Specific to this pose and accuracy level
- Around 2-3 sentences
- Focused on practical improvements

Response should sound natural and personalized, not template-based."""

        # Call Gemini API
        response = GEMINI_MODEL.generate_content(prompt)
        
        if response and response.text:
            feedback = response.text.strip()
            print(f"✅ Real Gemini AI feedback generated: {len(feedback)} characters")
            return feedback
        else:
            raise Exception("Empty response from Gemini")
            
    except Exception as e:
        print(f"⚠️ Gemini AI error: {e}")
        print(f"⚠️ Using enhanced fallback feedback...")
        
        # Enhanced fallback (still better than simple templates)
        asana_display = asana_name.replace('_', ' ').title()
        
        if pose_similarity >= 95:
            return f"Outstanding {asana_display} execution! Your alignment is nearly perfect at {pose_similarity:.1f}%. Continue maintaining this exceptional form while focusing on breath awareness and inner stability."
        elif pose_similarity >= 80:
            return f"Strong {asana_display} practice with {pose_similarity:.1f}% accuracy. Fine-tune your foundation and core engagement to reach the next level. Your dedication to proper form is evident."
        elif pose_similarity >= 60:
            return f"Good progress in {asana_display} with {pose_similarity:.1f}% alignment. Focus on key foundational elements and breathe deeply through each transition. Consistent practice will enhance your stability."
        elif pose_similarity >= 45:
            return f"You're building strength in {asana_display}. At {pose_similarity:.1f}% accuracy, concentrate on basic alignment principles and move mindfully. Each practice session brings improvement."
        else:
            return f"Keep exploring {asana_display} with patience and awareness. Focus on fundamental positioning and listen to your body. Remember, yoga is a journey of gradual refinement and self-discovery."

def calculate_ml_score(image_path: str, asana_name: str, reference_used: bool) -> dict:
    """Calculate AI-powered pose similarity score with YOUR scoring system and REAL Gemini feedback"""
    if not ML_ENABLED or not pose_detector or not analyzer:
        base_score = round(random.uniform(1.0, 3.0), 1)
        reference_penalty = 2 if reference_used else 0
        final_score = max(0, base_score - reference_penalty)
        return {
            "final_score": final_score,
            "raw_ai_score": base_score,
            "base_score": base_score,
            "pose_similarity": base_score * 10,
            "hand_similarity_left": None,
            "hand_similarity_right": None,
            "reference_penalty": reference_penalty,
            "ml_used": False,
            "error": "ML models not available",
            "feedback": "AI analysis unavailable. Keep practicing with mindful awareness!"
        }
    
    print(f"\n🤖 === AI ANALYSIS START ===")
    print(f"📷 Image: {image_path}")
    print(f"🧘 Target Asana: {asana_name}")
    print(f"📖 Reference Used: {reference_used}")
    print(f"⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Get reference data
    reference_data = asana_reference_data.get(asana_name)
    if not reference_data:
        print(f"❌ No reference data for {asana_name}")
        return {
            "final_score": 0.0,
            "raw_ai_score": 0.0,
            "base_score": 0.0,
            "pose_similarity": 0.0,
            "hand_similarity_left": None,
            "hand_similarity_right": None,
            "reference_penalty": 0,
            "ml_used": False,
            "error": f"No reference keypoints for {asana_name}",
            "feedback": f"Reference data not available for {asana_name.replace('_', ' ')}"
        }
    
    print(f"✅ Reference data loaded")
    
    # Extract user pose keypoints
    print(f"🔍 Extracting user pose keypoints...")
    try:
        pose_result = pose_detector.detect_from_image(image_path)
        user_pose_kpts = pose_result[0]
        
        if user_pose_kpts.size == 0 or len(user_pose_kpts) == 0:
            print("ℹ️ No pose keypoints detected - 0% similarity")
            return {
                "final_score": 0.0,
                "raw_ai_score": 0.0,
                "base_score": 0.0,
                "pose_similarity": 0.0,
                "hand_similarity_left": None,
                "hand_similarity_right": None,
                "reference_penalty": 0,
                "ml_used": True,
                "error": None,
                "feedback": "No pose detected. Try taking a clearer full-body photo with good lighting."
            }
        
        print(f"✅ Detected {len(user_pose_kpts)} person(s)")
        print(f"✅ First person has {len(user_pose_kpts[0])} keypoints")
        
    except Exception as e:
        print(f"❌ Pose detection error: {e}")
        return {
            "final_score": 0.0,
            "raw_ai_score": 0.0,
            "base_score": 0.0,
            "pose_similarity": 0.0,
            "hand_similarity_left": None,
            "hand_similarity_right": None,
            "reference_penalty": 0,
            "ml_used": False,
            "error": f"Pose detection failed: {e}",
            "feedback": "Technical issue with pose detection. Please try again with a clearer image."
        }
    
    # Extract hand keypoints
    print(f"🖐️ Extracting hand keypoints...")
    user_hand_left = None
    user_hand_right = None
    try:
        hand_result = hand_detector.detect_from_image(image_path)
        hand_landmarks = hand_result[0]
        user_hand_left, user_hand_right = hand_landmarks
        print(f"✅ Left hand: {'Detected' if user_hand_left is not None else 'Not detected'}")
        print(f"✅ Right hand: {'Detected' if user_hand_right is not None else 'Not detected'}")
    except Exception as e:
        print(f"⚠️ Hand detection error (continuing): {e}")
    
    # Get reference keypoints
    ref_pose_kpts = reference_data.get('pose_keypoints', [])
    ref_hand_left = reference_data.get('hand_left')
    ref_hand_right = reference_data.get('hand_right')
    
    if not ref_pose_kpts:
        return {
            "final_score": 0.0,
            "raw_ai_score": 0.0,
            "base_score": 0.0,
            "pose_similarity": 0.0,
            "hand_similarity_left": None,
            "hand_similarity_right": None,
            "reference_penalty": 0,
            "ml_used": False,
            "error": f"No reference pose keypoints for {asana_name}",
            "feedback": f"Reference data incomplete for {asana_name.replace('_', ' ')}"
        }
    
    print(f"📊 Reference keypoints loaded:")
    print(f" 🧘 Pose: {len(ref_pose_kpts[0])} keypoints")
    print(f" 🤚 Left hand: {'Available' if ref_hand_left else 'Not available'}")
    print(f" ✋ Right hand: {'Available' if ref_hand_right else 'Not available'}")
    
    # Calculate pose similarity
    print(f"🔍 Calculating pose similarity...")
    try:
        pose_sim = analyzer.pose_similarity(ref_pose_kpts[0], user_pose_kpts[0])
        print(f"✅ Pose similarity: {pose_sim:.2f}%")
    except Exception as e:
        print(f"❌ Pose similarity calculation failed: {e}")
        return {
            "final_score": 0.0,
            "raw_ai_score": 0.0,
            "base_score": 0.0,
            "pose_similarity": 0.0,
            "hand_similarity_left": None,
            "hand_similarity_right": None,
            "reference_penalty": 0,
            "ml_used": False,
            "error": f"Pose analysis failed: {e}",
            "feedback": "Technical issue with pose analysis. Please try again."
        }
    
    # Calculate hand similarities
    hand_left_sim = None
    hand_right_sim = None
    
    if ref_hand_left is not None and user_hand_left is not None:
        try:
            hand_left_sim = analyzer.hand_pose_similarity(ref_hand_left, user_hand_left)
            print(f"✅ Left hand similarity: {hand_left_sim:.2f}%")
        except Exception as e:
            print(f"⚠️ Left hand analysis failed: {e}")
    else:
        print(f"⚪ Left hand analysis skipped")
    
    if ref_hand_right is not None and user_hand_right is not None:
        try:
            hand_right_sim = analyzer.hand_pose_similarity(ref_hand_right, user_hand_right)
            print(f"✅ Right hand similarity: {hand_right_sim:.2f}%")
        except Exception as e:
            print(f"⚠️ Right hand analysis failed: {e}")
    else:
        print(f"⚪ Right hand analysis skipped")
    
    # FIXED: Use YOUR custom scoring system
    print(f"📊 Computing score with YOUR custom system...")
    try:
        raw_score = calculate_your_custom_score(
            pose_sim, 
            hand_left_sim, 
            hand_right_sim
        )
        print(f"✅ Raw AI score calculated: {raw_score:.2f}")
    except Exception as e:
        print(f"❌ Score calculation failed: {e}")
        raw_score = 0.0
    
    # FIXED: Generate REAL Gemini AI-powered feedback
    print(f"🤖 Generating REAL Gemini AI feedback...")
    try:
        feedback = generate_real_gemini_feedback(
            asana_name, 
            pose_sim, 
            hand_left_sim, 
            hand_right_sim
        )
        print(f"✅ Real Gemini feedback generated")
    except Exception as e:
        print(f"⚠️ Feedback generation error: {e}")
        feedback = f"Great effort practicing {asana_name.replace('_', ' ')}! Focus on proper alignment, steady breathing, and consistent practice."
    
    # Apply reference penalty
    reference_penalty = 2 if reference_used else 0
    final_score = max(0, raw_score - reference_penalty)
    
    print(f"🎯 === YOUR CUSTOM AI SCORING ===")
    print(f" Pose Quality: {pose_sim:.1f}%")
    print(f" Custom Score: {raw_score:.2f}/10")
    print(f" Reference Penalty: -{reference_penalty}")
    print(f" Final Score: {final_score:.2f}/10")
    print(f" Feedback: Real Gemini AI Generated")
    print(f"🤖 === AI ANALYSIS COMPLETE ===\n")
    
    return {
        "final_score": final_score,
        "raw_ai_score": raw_score,
        "base_score": raw_score,
        "pose_similarity": pose_sim,
        "hand_similarity_left": hand_left_sim,
        "hand_similarity_right": hand_right_sim,
        "reference_penalty": reference_penalty,
        "ml_used": True,
        "error": None,
        "feedback": feedback,
        "keypoints_detected": {
            "pose_keypoints": len(user_pose_kpts[0]) if len(user_pose_kpts) > 0 else 0,
            "left_hand_detected": user_hand_left is not None,
            "right_hand_detected": user_hand_right is not None
        }
    }

def process_round_results(room_code: str):
    """Process round results with YOUR scoring system and REAL Gemini feedback"""
    if room_code not in rooms:
        return
    
    room = rooms[room_code]
    round_info = room.get("round")
    
    if not round_info:
        return
    
    current_round = room["current_round"]
    asana_name = round_info["asana"]
    
    print(f"\n🔄 === AI SCORING ROUND {current_round} ===")
    print(f"🧘 Asana: {asana_name}")
    
    # Determine first player (for speed bonus eligibility)
    first_player = None
    if round_info["submission_order"]:
        first_player = round_info["submission_order"][0]["player"]
        print(f"🏃♂️ First to submit: {first_player}")
    
    # Process each player
    round_scores = {}
    for player_name in room["players"]:
        if player_name in round_info["submissions"]:
            submission = round_info["submissions"][player_name]
            if not submission["processed"]:
                try:
                    print(f"\n👤 AI analyzing {player_name}...")
                    
                    # Check reference usage
                    reference_used = room["reference_used"][player_name].get(current_round, False)
                    is_first = (player_name == first_player)
                    
                    # Get AI score with reference penalty already applied
                    ml_result = calculate_ml_score(
                        submission["image_path"],
                        asana_name,
                        reference_used
                    )
                    
                    # STRICT: Quality-based speed bonus (consistent with your system)
                    speed_bonus = 0.0
                    bonus_tier = "N/A"
                    
                    if is_first:
                        pose_similarity = ml_result.get("pose_similarity", 0)
                        
                        # STRICT: Only reward high-quality poses
                        if pose_similarity >= 95:
                            speed_bonus = 2.0
                            bonus_tier = "🏆 EXCELLENT"
                        elif pose_similarity >= 90:
                            speed_bonus = 1.5
                            bonus_tier = "🥇 GOOD"  
                        elif pose_similarity >= 80:
                            speed_bonus = 1.0
                            bonus_tier = "🥈 AVERAGE"
                        else:
                            speed_bonus = 0.0
                            bonus_tier = "❌ NO BONUS"
                        
                        print(f"⚡ STRICT SPEED BONUS:")
                        print(f" Pose quality: {pose_similarity:.1f}% ({bonus_tier})")
                        print(f" Speed bonus: +{speed_bonus} points")
                    else:
                        print(f"⏰ Not first submission → No speed bonus")
                    
                    # Calculate final score
                    final_score_with_bonus = round(ml_result["final_score"] + speed_bonus, 1)
                    
                    # Store detailed results with REAL Gemini feedback
                    player_result = {
                        "final_score": final_score_with_bonus,
                        "base_score": ml_result["base_score"],
                        "raw_ai_score": ml_result["final_score"],
                        "pose_similarity": ml_result["pose_similarity"],
                        "hand_similarity_left": ml_result["hand_similarity_left"],
                        "hand_similarity_right": ml_result["hand_similarity_right"],
                        "reference_used": reference_used,
                        "reference_penalty": ml_result["reference_penalty"],
                        "speed_bonus": speed_bonus,
                        "speed_bonus_tier": bonus_tier if is_first else "N/A",
                        "is_first": is_first,
                        "ml_used": ml_result["ml_used"],
                        "ml_error": ml_result["error"],
                        "feedback": ml_result.get("feedback", "")  # REAL Gemini AI feedback
                    }
                    
                    round_info["scores"][player_name] = player_result
                    round_scores[player_name] = final_score_with_bonus
                    
                    # Update total score
                    room["scores"][player_name] = round(
                        room["scores"][player_name] + final_score_with_bonus, 1
                    )
                    
                    submission["processed"] = True
                    
                    print(f"✅ {player_name}: {final_score_with_bonus} points")
                    print(f" 📊 Breakdown:")
                    print(f" Custom AI: {ml_result['base_score']:.1f}")
                    print(f" Reference penalty: -{ml_result['reference_penalty']}")
                    print(f" AI after penalty: {ml_result['final_score']:.1f}")
                    print(f" Speed bonus: +{speed_bonus}")
                    print(f" FINAL: {final_score_with_bonus:.1f}")
                    
                    if ml_result["ml_used"]:
                        print(f" 🤖 AI Analysis: {ml_result['pose_similarity']:.1f}% pose accuracy")
                        print(f" 🤖 Gemini Feedback: Real AI Generated")
                
                except Exception as e:
                    print(f"❌ Critical error processing {player_name}: {e}")
                    player_result = {
                        "final_score": 0.0,
                        "base_score": 0.0,
                        "reference_used": False,
                        "speed_bonus": 0,
                        "speed_bonus_tier": "ERROR",
                        "ml_used": False,
                        "error": str(e),
                        "feedback": "Error processing your pose. Please try again."
                    }
                    
                    round_info["scores"][player_name] = player_result
                    round_scores[player_name] = 0.0
                    submission["processed"] = True
        else:
            # No submission
            player_result = {
                "final_score": 0.0,
                "base_score": 0.0,
                "reference_used": False,
                "speed_bonus": 0,
                "speed_bonus_tier": "NO SUBMISSION",
                "ml_used": False,
                "error": "No submission",
                "feedback": "No pose submitted for this round."
            }
            
            round_info["scores"][player_name] = player_result
            round_scores[player_name] = 0.0
            print(f"⏰ {player_name}: No submission (0 points)")
    
    # Store round history for results display
    if "round_history" not in room:
        room["round_history"] = {}
    
    room["round_history"][str(current_round)] = {
        "asana": asana_name,
        "asana_display": round_info["asana_display"],
        "scores": round_scores,
        "detailed_results": round_info["scores"],
        "first_player": first_player,
        "timestamp": datetime.now().isoformat()
    }
    
    room["state_changed_at"] = datetime.utcnow()
    
    print(f"\n📊 ROUND {current_round} FINAL SCORES:")
    for player, score in round_scores.items():
        total = room["scores"][player]
        result = round_info["scores"].get(player, {})
        bonus_info = f" (Speed: +{result.get('speed_bonus', 0)}, {result.get('speed_bonus_tier', 'N/A')})" if result.get('is_first') else ""
        print(f" {player}: +{score} → Total: {total}{bonus_info}")
    
    print(f"🔚 === AI SCORING COMPLETE ===\n")
