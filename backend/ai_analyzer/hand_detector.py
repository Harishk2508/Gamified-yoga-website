import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

class HandDetector:
    def __init__(self, model_path='hand_landmarker.task'):
        """Initialize MediaPipe Hand Landmarker"""
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
    
    def detect_from_image(self, img_path):
        """Extract hand keypoints from image file"""
        image = mp.Image.create_from_file(img_path)
        detection_result = self.detector.detect(image)
        return self._extract_hand_landmarks(detection_result), detection_result, image.numpy_view()
    
    def detect_from_frame(self, frame):
        """Extract hand keypoints from video frame"""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.detector.detect(mp_image)
        return self._extract_hand_landmarks(detection_result), detection_result
    
    def _extract_hand_landmarks(self, detection_result):
        """Extract and classify left/right hand landmarks"""
        left_hand, right_hand = None, None
        
        if detection_result.hand_landmarks:
            for i, hand_landmarks in enumerate(detection_result.hand_landmarks):
                landmarks_array = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks])
                
                # Determine handedness
                if detection_result.handedness and i < len(detection_result.handedness):
                    handedness = detection_result.handedness[i][0].category_name
                    if handedness == 'Left':
                        left_hand = landmarks_array
                    else:
                        right_hand = landmarks_array
                else:
                    # Fallback assignment
                    if i == 0:
                        left_hand = landmarks_array
                    else:
                        right_hand = landmarks_array
        
        return left_hand, right_hand
