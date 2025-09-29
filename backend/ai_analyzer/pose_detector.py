import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

class PoseDetector:
    def __init__(self, model_path='pose_landmarker_heavy.task'):
        """Initialize MediaPipe Pose Landmarker"""
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=True
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)
    
    def detect_from_image(self, img_path):
        """Extract pose keypoints from image file"""
        image = mp.Image.create_from_file(img_path)
        detection_result = self.detector.detect(image)
        
        keypoints = []
        if detection_result.pose_landmarks:
            for pose_landmarks in detection_result.pose_landmarks:
                kp = [[lm.x, lm.y, lm.z] for lm in pose_landmarks]
                keypoints.append(kp)
        
        keypoints = np.array(keypoints) if keypoints else np.array([])
        return keypoints, detection_result, image.numpy_view()
    
    def detect_from_frame(self, frame):
        """Extract pose keypoints from video frame"""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.detector.detect(mp_image)
        
        keypoints = []
        if detection_result.pose_landmarks:
            for pose_landmarks in detection_result.pose_landmarks:
                kp = [[lm.x, lm.y, lm.z] for lm in pose_landmarks]
                keypoints.append(kp)
        
        keypoints = np.array(keypoints) if keypoints else np.array([])
        return keypoints, detection_result
