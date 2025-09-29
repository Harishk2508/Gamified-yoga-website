import json
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
import cv2

from backend.ai_analyzer.pose_detector import PoseDetector
from backend.ai_analyzer.hand_detector import HandDetector
from backend.ai_analyzer.analyzer import YogaPoseAnalyzer

class PoseDetectionService:
    def __init__(self):
        # Initialize detectors and analyzer
        self.pose_detector = PoseDetector(model_path=r"D:\base_codes\pose_landmarker_heavy.task")
        self.hand_detector = HandDetector(model_path=r"D:\base_codes\hand_landmarker.task")
        self.analyzer = YogaPoseAnalyzer(gemini_api_key="AIzaSyBXz4PsJe7OI9kwnhIeTEEG8dhiSguhs50")
        
        # Load reference poses
        self.reference_data = self._load_reference_data()
        self.reference_poses = {
            name: np.array(entry["pose_keypoints"]) 
            for name, entry in self.reference_data.items()
        }
        
        # Ensure uploads directory exists
        self.uploads_dir = "frontend/static/uploads"
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def _load_reference_data(self) -> Dict:
        """Load reference pose data from JSON file"""
        try:
            with open("D:\\base_codes\\data\\asana_keypoints.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("Reference pose data not found. Please ensure asana_keypoints.json exists.")
        except json.JSONDecodeError:
            raise Exception("Invalid reference pose data format.")
    
    async def classify_pose_from_image(self, image_path: str) -> Dict:
        """
        Classify yoga pose from image and return detailed results
        """
        try:
            # Detect pose and hand keypoints
            pose_kps, _, _ = self.pose_detector.detect_from_image(image_path)
            hand_kps, _, _ = self.hand_detector.detect_from_image(image_path)
            
            if pose_kps.shape[0] == 0:
                return {
                    "pose_detected": False,
                    "message": "No pose detected in the image. Please ensure a clear view of the full body."
                }
            
            # Find best matching asana
            best_match = self._find_best_match(pose_kps)
            
            # Generate feedback based on similarity score
            feedback = self._generate_feedback(best_match['similarity'])
            
            return {
                "pose_detected": True,
                "best_asana": best_match['asana'],
                "similarity": f"{best_match['similarity']:.2f}%",
                "confidence_level": best_match['confidence_level'],
                "feedback": feedback,
                "suggestions": self._get_improvement_suggestions(best_match),
                "all_matches": best_match['all_scores'][:5]  # Top 5 matches
            }
            
        except Exception as e:
            raise Exception(f"Error during pose classification: {str(e)}")
    
    def _find_best_match(self, pose_kps: np.ndarray) -> Dict:
        """Find the best matching asana and return detailed scoring"""
        all_scores = []
        best_score = -1
        best_asana = None
        
        for asana_name, ref_pose in self.reference_poses.items():
            try:
                sim, pose_sim, hand_sim = self.analyzer.combined_similarity(
                    ref_pose, pose_kps,
                    hand_left_ref=None, hand_left_user=None,
                    hand_right_ref=None, hand_right_user=None
                )
                
                all_scores.append({
                    "asana": asana_name,
                    "similarity": sim,
                    "pose_similarity": pose_sim,
                    "hand_similarity": hand_sim
                })
                
                if sim > best_score:
                    best_score = sim
                    best_asana = asana_name
                    
            except Exception as e:
                print(f"Error comparing with {asana_name}: {e}")
                continue
        
        # Sort all scores by similarity
        all_scores.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(best_score)
        
        return {
            "asana": best_asana,
            "similarity": best_score,
            "confidence_level": confidence_level,
            "all_scores": all_scores
        }
    
    def _get_confidence_level(self, similarity: float) -> str:
        """Determine confidence level based on similarity score"""
        if similarity >= 90:
            return "Excellent"
        elif similarity >= 80:
            return "Good"
        elif similarity >= 70:
            return "Fair"
        elif similarity >= 60:
            return "Needs Improvement"
        else:
            return "Poor Match"
    
    def _generate_feedback(self, similarity: float) -> str:
        """Generate user feedback based on similarity score"""
        if similarity >= 90:
            return "Excellent pose! Your form is very accurate."
        elif similarity >= 80:
            return "Good pose! Minor adjustments may improve your form."
        elif similarity >= 70:
            return "Fair pose. Focus on alignment and positioning."
        elif similarity >= 60:
            return "Needs improvement. Check your posture and alignment."
        else:
            return "Poor match. Please review the correct pose form or try a different angle."
    
    def _get_improvement_suggestions(self, match_result: Dict) -> List[str]:
        """Generate improvement suggestions based on pose analysis"""
        suggestions = []
        similarity = match_result['similarity']
        
        if similarity < 90:
            suggestions.append("Focus on proper alignment of joints")
        if similarity < 80:
            suggestions.append("Check your spine positioning")
            suggestions.append("Ensure balanced weight distribution")
        if similarity < 70:
            suggestions.append("Review the reference pose image")
            suggestions.append("Consider starting with preparatory poses")
        if similarity < 60:
            suggestions.append("Practice basic poses first")
            suggestions.append("Consider getting guidance from an instructor")
        
        return suggestions
    
    async def compare_with_reference(self, image_path: str, reference_asana: str) -> Dict:
        """Compare user pose with specific reference asana"""
        if reference_asana not in self.reference_poses:
            raise Exception(f"Reference asana '{reference_asana}' not found")
        
        try:
            pose_kps, _, _ = self.pose_detector.detect_from_image(image_path)
            
            if pose_kps.shape[0] == 0:
                return {"pose_detected": False, "message": "No pose detected"}
            
            ref_pose = self.reference_poses[reference_asana]
            sim, pose_sim, hand_sim = self.analyzer.combined_similarity(
                ref_pose, pose_kps,
                hand_left_ref=None, hand_left_user=None,
                hand_right_ref=None, hand_right_user=None
            )
            
            return {
                "pose_detected": True,
                "reference_asana": reference_asana,
                "similarity": f"{sim:.2f}%",
                "pose_similarity": f"{pose_sim:.2f}%",
                "hand_similarity": f"{hand_sim:.2f}%",
                "confidence_level": self._get_confidence_level(sim),
                "feedback": self._generate_feedback(sim),
                "suggestions": self._get_improvement_suggestions({"similarity": sim})
            }
            
        except Exception as e:
            raise Exception(f"Error comparing poses: {str(e)}")
    
    def get_available_asanas(self) -> List[Dict]:
        """Get list of all available asanas"""
        asanas = []
        for name, data in self.reference_data.items():
            asanas.append({
                "name": name,
                "display_name": name.replace("_", " ").title(),
                "keypoints_count": len(data.get("pose_keypoints", []))
            })
        return sorted(asanas, key=lambda x: x["display_name"])
    
    def get_asana_info(self, asana_name: str) -> Optional[Dict]:
        """Get detailed information about specific asana"""
        if asana_name not in self.reference_data:
            return None
        
        data = self.reference_data[asana_name]
        return {
            "name": asana_name,
            "display_name": asana_name.replace("_", " ").title(),
            "pose_keypoints_count": len(data.get("pose_keypoints", [])),
            "left_hand_keypoints_count": len(data.get("left_hand_keypoints", [])),
            "right_hand_keypoints_count": len(data.get("right_hand_keypoints", [])),
            "has_hand_analysis": bool(data.get("left_hand_keypoints") or data.get("right_hand_keypoints"))
        }
    
    def cleanup_temp_files(self, file_path: str) -> None:
        """Clean up temporary files"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {e}")
