import cv2
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import matplotlib.pyplot as plt


class LandmarkVisualizer:
    def __init__(self):
        self.pose_connections = solutions.pose.POSE_CONNECTIONS
        self.hand_connections = solutions.hands.HAND_CONNECTIONS
        self.pose_style = solutions.drawing_styles.get_default_pose_landmarks_style()
        self.hand_style = solutions.drawing_styles.get_default_hand_landmarks_style()
    
    def draw_pose_landmarks(self, image, pose_detection_result):
        """Draw pose landmarks on image"""
        annotated_image = np.copy(image)
        
        if pose_detection_result.pose_landmarks:
            for pose_landmarks in pose_detection_result.pose_landmarks:
                pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                pose_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z) 
                    for lm in pose_landmarks
                ])
                
                solutions.drawing_utils.draw_landmarks(
                    annotated_image,
                    pose_landmarks_proto,
                    self.pose_connections,
                    self.pose_style
                )
        return annotated_image
    
    def draw_hand_landmarks(self, image, hand_detection_result):
        """Draw hand landmarks on image"""
        annotated_image = np.copy(image)
        
        if hand_detection_result.hand_landmarks:
            for hand_landmarks in hand_detection_result.hand_landmarks:
                hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                hand_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z) 
                    for lm in hand_landmarks
                ])
                
                solutions.drawing_utils.draw_landmarks(
                    annotated_image,
                    hand_landmarks_proto,
                    self.hand_connections,
                    self.hand_style
                )
        return annotated_image
    
    def draw_combined_landmarks(self, image, pose_detection_result=None, hand_detection_result=None):
        """Draw both pose and hand landmarks on the same image"""
        annotated_image = np.copy(image)
        
        # Draw pose landmarks first
        if pose_detection_result and pose_detection_result.pose_landmarks:
            annotated_image = self.draw_pose_landmarks(annotated_image, pose_detection_result)
        
        # Draw hand landmarks on top
        if hand_detection_result and hand_detection_result.hand_landmarks:
            annotated_image = self.draw_hand_landmarks(annotated_image, hand_detection_result)
        
        return annotated_image
    
    def show_landmarks(self, image, title="Landmark Detection"):
        """Display the annotated image using matplotlib instead of cv2 window"""
        # Convert image color from RGB to BGR for OpenCV drawing, but matplotlib expects RGB
        # MediaPipe draws on RGB images, so no need to convert color space here, just show as is
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        plt.title(title)
        plt.axis('off')
        plt.show()
