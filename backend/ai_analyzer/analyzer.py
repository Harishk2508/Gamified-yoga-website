import numpy as np
import math
from google import genai

class YogaPoseAnalyzer:
    def __init__(self, gemini_api_key=None):
        self.pose_landmarks_names = {
            11: "left_shoulder", 12: "right_shoulder",
            13: "left_elbow", 14: "right_elbow", 
            15: "left_wrist", 16: "right_wrist",
            23: "left_hip", 24: "right_hip",
            25: "left_knee", 26: "right_knee",
            27: "left_ankle", 28: "right_ankle"
        }
        
        # Initialize Gemini client if API key provided
        if gemini_api_key:
            self.client = genai.Client(api_key=gemini_api_key)
        else:
            self.client = None
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a, b, c = np.array(a), np.array(b), np.array(c)
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
        return angle
    
    def analyze_body_angles(self, keypoints):
        """Extract key body angles for pose analysis"""
        kp = np.squeeze(keypoints)
        if len(kp.shape) != 2 or kp.shape[0] < 33:
            return {}
        
        angles = {}
        try:
            # Shoulder angles
            angles['left_shoulder'] = self.calculate_angle(kp[13], kp[11], kp[23])
            angles['right_shoulder'] = self.calculate_angle(kp[14], kp[12], kp[24])
            
            # Elbow angles  
            angles['left_elbow'] = self.calculate_angle(kp[11], kp[13], kp[15])
            angles['right_elbow'] = self.calculate_angle(kp[12], kp[14], kp[16])
            
            # Hip angles
            angles['left_hip'] = self.calculate_angle(kp[11], kp[23], kp[25])
            angles['right_hip'] = self.calculate_angle(kp[12], kp[24], kp[26])
            
            # Knee angles
            angles['left_knee'] = self.calculate_angle(kp[23], kp[25], kp[27])
            angles['right_knee'] = self.calculate_angle(kp[24], kp[26], kp[28])
            
            # Spine alignment
            angles['spine_alignment'] = self.calculate_angle([kp[11][0], kp[11][1]], 
                                                           [(kp[11][0] + kp[12][0])/2, (kp[11][1] + kp[12][1])/2],
                                                           [(kp[23][0] + kp[24][0])/2, (kp[23][1] + kp[24][1])/2])
        except:
            pass
        
        return angles
    
    def pose_similarity(self, kp1, kp2):
        """Calculate pose similarity (keeping your original function)"""
        kp1 = np.squeeze(kp1)
        kp2 = np.squeeze(kp2)
        def normalize(keypoints):
            left_hip = keypoints[23][:2]
            right_hip = keypoints[24][:2]
            center = (left_hip + right_hip) / 2
            keypoints[:, :2] -= center
            scale = np.linalg.norm(left_hip - right_hip)
            if scale > 0:
                keypoints[:, :2] /= scale
            return keypoints
        kp1 = normalize(kp1.copy())
        kp2 = normalize(kp2.copy())
        sims = []
        for i in range(kp1.shape[0]):
            v1, v2 = kp1[i], kp2[i]
            dot = np.dot(v1, v2)
            norm = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norm > 0:
                sims.append(dot / norm)
        if not sims:
            return 0.0
        similarity = np.mean(sims) * 100
        return round(similarity, 2)
    
    def hand_pose_similarity(self, hand_kp1, hand_kp2):
        """Calculate hand similarity"""
        if hand_kp1 is None or hand_kp2 is None:
            return 0.0
            
        hand_kp1 = np.array(hand_kp1)
        hand_kp2 = np.array(hand_kp2)
        
        if hand_kp1.shape[0] != 21 or hand_kp2.shape[0] != 21:
            return 0.0
        def normalize_hand(keypoints):
            wrist = keypoints[0][:2]
            keypoints_norm = keypoints.copy()
            keypoints_norm[:, :2] -= wrist
            
            finger_tips = [4, 8, 12, 16, 20]
            distances = [np.linalg.norm(keypoints_norm[tip][:2]) for tip in finger_tips]
            max_dist = np.max(distances) if distances else 1.0
            
            if max_dist > 0:
                keypoints_norm[:, :2] /= max_dist
            return keypoints_norm
        hand_kp1_norm = normalize_hand(hand_kp1)
        hand_kp2_norm = normalize_hand(hand_kp2)
        sims = []
        weights = [1.0] * 21
        finger_tips = [4, 8, 12, 16, 20]
        
        for tip in finger_tips:
            weights[tip] = 1.5
        for i in range(21):
            v1, v2 = hand_kp1_norm[i], hand_kp2_norm[i]
            dot = np.dot(v1, v2)
            norm = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norm > 0:
                sims.append((dot / norm) * weights[i])
            else:
                sims.append(0.0)
        if not sims:
            return 0.0
        similarity = np.sum(sims) / np.sum(weights) * 100
        return round(similarity, 2)
    
    def combined_similarity(self, pose_ref, pose_user, hand_left_ref=None, hand_left_user=None, 
                           hand_right_ref=None, hand_right_user=None, pose_weight=0.9, hand_weight=0.1):
        """
        FIXED: Calculate combined similarity with proper weighting
        
        NEW LOGIC:
        - Pose Weight: 90% (primary importance)
        - Hand Weight: 10% (bonus points only)
        - If no hands detected: Overall = Pose Score (no penalty)
        - If hands detected: Overall = 90% pose + 10% hand (slight bonus)
        """
        pose_sim = self.pose_similarity(pose_ref, pose_user)
        
        hand_sims = []
        if hand_left_ref is not None and hand_left_user is not None:
            left_hand_sim = self.hand_pose_similarity(hand_left_ref, hand_left_user)
            if left_hand_sim > 0:  # Only add if actually detected
                hand_sims.append(left_hand_sim)
        
        if hand_right_ref is not None and hand_right_user is not None:
            right_hand_sim = self.hand_pose_similarity(hand_right_ref, hand_right_user)
            if right_hand_sim > 0:  # Only add if actually detected
                hand_sims.append(right_hand_sim)
        
        # FIXED LOGIC: No penalty for missing hands
        if not hand_sims:
            # No hands detected - return pose score as overall score
            return pose_sim, pose_sim, 0.0
        
        # Hands detected - add as bonus
        avg_hand_sim = np.mean(hand_sims)
        combined_sim = pose_weight * pose_sim + hand_weight * avg_hand_sim
        
        return round(combined_sim, 2), pose_sim, avg_hand_sim
    
    def detect_mirror(self, ref_kpts, user_kpts):
        """Detect if pose is mirrored (keeping your original function)"""
        def normalize_keypoints(keypoints):
            hip_center = (keypoints[23] + keypoints[24]) / 2
            shoulder_center = (keypoints[11] + keypoints[12]) / 2
            torso_length = np.linalg.norm(shoulder_center - hip_center)
            kpts_norm = (keypoints - hip_center) / (torso_length if torso_length else 1.0)
            return kpts_norm
        def compute_angle(a, b, c):
            v1, v2 = a - b, c - b
            cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
            return np.arccos(np.clip(cos_theta, -1.0, 1.0))
        def all_joint_angles(kpts):
            joints = [(11, 13, 15), (12, 14, 16), (13, 11, 23), (14, 12, 24),
                     (23, 25, 27), (24, 26, 28), (25, 23, 11), (26, 24, 12)]
            return np.array([compute_angle(kpts[a], kpts[b], kpts[c]) for a, b, c in joints])
        def mirrored_keypoints(kpts):
            swap_map = [(11,12), (13,14), (15,16), (23,24), (25,26), (27,28)]
            kpts_m = kpts.copy()
            for lidx, ridx in swap_map:
                kpts_m[[lidx, ridx]] = kpts_m[[ridx, lidx]]
            return kpts_m
        r_norm = normalize_keypoints(ref_kpts)
        u_norm = normalize_keypoints(user_kpts)
        u_mirr = mirrored_keypoints(u_norm)
        ref_angles = all_joint_angles(r_norm)
        user_angles = all_joint_angles(u_norm)
        user_angles_mirr = all_joint_angles(u_mirr)
        key_idxs = list(range(11, 33))
        pos_error_direct = np.mean(np.linalg.norm(r_norm[key_idxs] - u_norm[key_idxs], axis=1))
        pos_error_mirr = np.mean(np.linalg.norm(r_norm[key_idxs] - u_mirr[key_idxs], axis=1))
        ang_diff_direct = np.mean(np.abs(ref_angles - user_angles))
        ang_diff_mirr = np.mean(np.abs(ref_angles - user_angles_mirr))
        total_direct = pos_error_direct + 3.0 * ang_diff_direct
        total_mirr = pos_error_mirr + 3.0 * ang_diff_mirr
        return total_mirr + 0.2 < total_direct
    
    def generate_angle_based_corrections(self, ref_keypoints, user_keypoints, score, is_mirrored, hand_score=None):
        """Generate realistic corrections based on angle analysis with adjusted logic"""
        ref_angles = self.analyze_body_angles(ref_keypoints)
        user_angles = self.analyze_body_angles(user_keypoints)
        
        corrections = []
        
        if is_mirrored:
            corrections.append("MIRROR DETECTED: Switch to the opposite side to match the reference pose")
        
        # Angle-based corrections with thresholds
        angle_thresholds = {
            'shoulder': 15,
            'elbow': 20,
            'hip': 15, 
            'knee': 20,
            'spine_alignment': 10
        }
        
        for joint in ['left_shoulder', 'right_shoulder']:
            if joint in ref_angles and joint in user_angles:
                angle_diff = abs(ref_angles[joint] - user_angles[joint])
                if angle_diff > angle_thresholds['shoulder']:
                    side = "left" if "left" in joint else "right"
                    if user_angles[joint] > ref_angles[joint]:
                        corrections.append(f"{side} shoulder: relax and lower - you're lifting too high ({angle_diff:.0f}° off)")
                    else:
                        corrections.append(f"{side} shoulder: engage and lift slightly ({angle_diff:.0f}° off)")
        
        for joint in ['left_elbow', 'right_elbow']:
            if joint in ref_angles and joint in user_angles:
                angle_diff = abs(ref_angles[joint] - user_angles[joint])
                if angle_diff > angle_thresholds['elbow']:
                    side = "left" if "left" in joint else "right"
                    if user_angles[joint] > ref_angles[joint]:
                        corrections.append(f"{side} elbow: bend more to achieve proper angle ({angle_diff:.0f}° off)")
                    else:
                        corrections.append(f"{side} elbow: straighten slightly ({angle_diff:.0f}° off)")
        
        for joint in ['left_knee', 'right_knee']:
            if joint in ref_angles and joint in user_angles:
                angle_diff = abs(ref_angles[joint] - user_angles[joint])
                if angle_diff > angle_thresholds['knee']:
                    side = "left" if "left" in joint else "right"
                    if user_angles[joint] > ref_angles[joint]:
                        corrections.append(f"{side} knee: bend deeper ({angle_diff:.0f}° off)")
                    else:
                        corrections.append(f"{side} knee: straighten more ({angle_diff:.0f}° off)")
        
        # ADJUSTED: Only mention hands if they were actually detected and scored poorly
        if hand_score is not None and hand_score > 0 and hand_score < 75:
            corrections.append("Hand positioning: adjust finger alignment and wrist angle for better mudra")
        
        # Limit corrections based on score
        if score >= 95:
            return corrections[:1] if corrections else ["Excellent form! Just minor fine-tuning needed."]
        elif score >= 90:
            return corrections[:2] if corrections else ["Great alignment! Small adjustments will perfect it."]
        elif score >= 80:
            return corrections[:3] if corrections else ["Good foundation! Focus on key alignment points."]
        else:
            return corrections[:4] if corrections else ["Keep practicing! Focus on fundamental positioning."]
    
    def fetch_asana_benefits_and_tips(self, asana_name):
        """NEW METHOD: Fetch asana-specific benefits and important focus areas using Gemini API"""
        if not self.client:
            # Fallback when no API key provided
            return f"For optimal benefits in {asana_name}, focus on proper alignment, steady breathing, and listening to your body's limits."
        
        try:
            prompt = f"""As an expert yoga instructor, provide comprehensive information about {asana_name} yoga pose.
            
Please provide:
1. Key physical and mental benefits of this pose
2. Important alignment cues and focus areas
3. Common mistakes to avoid 
4. Breathing techniques specific to this pose
5. Modifications for beginners if needed
6. Therapeutic applications (if any)
Structure your response as a professional note that would be valuable for yoga practitioners to understand the importance and proper execution of {asana_name}. Keep it informative, practical, and educational - around 4-6 sentences covering the most essential aspects."""
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            print(f"⚠️ Gemini API error for asana tips: {e}. Using fallback.")
            # Enhanced fallback with basic asana information
            return f"For optimal benefits in {asana_name}, focus on proper spinal alignment, engage your core muscles, and maintain steady ujjayi breathing. Pay attention to weight distribution and avoid forcing the pose beyond your current flexibility. This pose helps improve strength, balance, and mental focus when practiced with mindful awareness and proper technique."
    
    def generate_realistic_feedback(self, asana_name, combined_score, pose_score, hand_score, corrections, is_mirrored):
        """Simplified Gemini API powered realistic feedback generation"""
        score_breakdown = f"Overall: {combined_score}% | Body: {pose_score}% | Hands: {hand_score if hand_score and hand_score > 0 else 'Not detected'}%"

        # Format corrections as numbered list for clarity in prompt
        correction_list_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(corrections)]) if corrections else "No specific corrections detected."

        # Build prompt for Gemini API
        if is_mirrored:
            prompt = f"""You are a professional yoga instructor. The student is performing {asana_name} on the WRONG SIDE (mirrored).
Student's performance summary: {score_breakdown}

Critical issue: Pose mirrored - needs to switch to the correct side.

Detected corrections to address:
{correction_list_text}

Provide feedback in 4 clear lines:
1. Emphasize the need to switch sides immediately.
2. Explain why the correct side is important for {asana_name}.
3. Give steps to switch sides and re-establish the pose.
4. Encourage safe practice and acknowledge effort."""
        else:
            prompt = f"""You are a professional yoga instructor. The student has practiced {asana_name}.

Student's performance summary: {score_breakdown}

Corrections needed:
{correction_list_text}

Provide realistic, constructive feedback in {7 if combined_score < 70 else 5 if combined_score < 90 else 2} lines, covering:
- Key corrections to focus on
- Why these corrections matter for {asana_name}
- Steps to improve
- Motivational encouragement

Also, provide a note on important areas to focus while performing {asana_name} for maximum benefit, as a separate paragraph."""

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"⚠️ Gemini API error in feedback generation: {e}")

        # Minimal fallback if Gemini API unavailable
        fallback_feedback = "Feedback generation is currently unavailable. Continue practicing mindfully and focus on the corrections provided."
        return fallback_feedback
