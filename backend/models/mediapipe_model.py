"""
MediaPipe-based pose detection model
This serves as our Phase 1 MVP baseline
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)

class MediaPipeModel:
    """
    MediaPipe Pose detection model wrapper
    
    Detects 33 body landmarks including:
    - Face: 10 landmarks
    - Torso: 4 landmarks
    - Arms: 6 landmarks each
    - Legs: 5 landmarks each
    """
    
    # Landmark indices for common body parts
    LANDMARK_NAMES = [
        "nose", "left_eye_inner", "left_eye", "left_eye_outer",
        "right_eye_inner", "right_eye", "right_eye_outer",
        "left_ear", "right_ear",
        "mouth_left", "mouth_right",
        "left_shoulder", "right_shoulder",
        "left_elbow", "right_elbow",
        "left_wrist", "right_wrist",
        "left_pinky", "right_pinky",
        "left_index", "right_index",
        "left_thumb", "right_thumb",
        "left_hip", "right_hip",
        "left_knee", "right_knee",
        "left_ankle", "right_ankle",
        "left_heel", "right_heel",
        "left_foot_index", "right_foot_index"
    ]
    
    # Skeleton connections (bone pairs)
    SKELETON_EDGES = [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (16, 18), (18, 20), (18, 22), (12, 14), (14, 16), (23, 24),
        (23, 25), (25, 27), (27, 29), (29, 31), (24, 26), (26, 28), (28, 30), (30, 32)
    ]
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize MediaPipe pose detector
        
        Args:
            confidence_threshold: Minimum confidence to consider a detection valid
        """
        self.confidence_threshold = confidence_threshold
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,  # 0=light, 1=full, 2=heavy
            smooth_landmarks=True,
            min_detection_confidence=confidence_threshold,
            min_tracking_confidence=confidence_threshold
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        logger.info("MediaPipe model initialized successfully")
    
    def detect(self, image: np.ndarray) -> Dict:
        """
        Detect pose landmarks in an image
        
        Args:
            image: Input image (BGR or RGB format, H x W x 3)
            
        Returns:
            Dictionary containing:
            - landmarks: List of (x, y, z, confidence) for each joint
            - bboxes: Bounding boxes for detected people
            - confidence: Overall detection confidence
            - success: Boolean indicating detection success
        """
        if image is None or image.size == 0:
            logger.error("Invalid image provided")
            return {"success": False, "landmarks": [], "error": "Invalid image"}
        
        try:
            # Convert BGR to RGB if needed
            if len(image.shape) != 3 or image.shape[2] != 3:
                logger.error("Invalid image shape")
                return {"success": False, "landmarks": [], "error": "Invalid image shape"}
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, _ = image.shape
            
            # Run inference
            results = self.pose.process(rgb_image)
            
            if not results.pose_landmarks:
                logger.warning("No pose landmarks detected")
                return {
                    "success": True,
                    "landmarks": [],
                    "confidence": 0.0,
                    "num_people": 0
                }
            
            # Extract landmarks
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append({
                    "x": float(landmark.x),
                    "y": float(landmark.y),
                    "z": float(landmark.z),
                    "confidence": float(landmark.visibility)
                })
            
            # Calculate bounding box
            valid_landmarks = [l for l in landmarks if l["confidence"] > self.confidence_threshold]
            if valid_landmarks:
                xs = [l["x"] for l in valid_landmarks]
                ys = [l["y"] for l in valid_landmarks]
                bbox = {
                    "xmin": min(xs),
                    "ymin": min(ys),
                    "xmax": max(xs),
                    "ymax": max(ys),
                    "width": w,
                    "height": h
                }
            else:
                bbox = None
            
            return {
                "success": True,
                "landmarks": landmarks,
                "landmark_names": self.LANDMARK_NAMES,
                "bbox": bbox,
                "confidence": float(np.mean([l["confidence"] for l in valid_landmarks])) if valid_landmarks else 0.0,
                "num_people": 1,  # MediaPipe detects single person
                "image_shape": [h, w]
            }
            
        except Exception as e:
            logger.error(f"Error during pose detection: {str(e)}")
            return {"success": False, "landmarks": [], "error": str(e)}
    
    def detect_batch(self, images: List[np.ndarray]) -> List[Dict]:
        """
        Detect poses in multiple images
        
        Args:
            images: List of input images
            
        Returns:
            List of detection results
        """
        results = []
        for image in images:
            results.append(self.detect(image))
        return results
    
    def draw_landmarks(
        self,
        image: np.ndarray,
        landmarks: List[Dict],
        joint_radius: int = 4,
        line_thickness: int = 2,
        joint_color: Tuple[int, int, int] = (0, 255, 0),
        line_color: Tuple[int, int, int] = (255, 0, 0)
    ) -> np.ndarray:
        """
        Draw pose landmarks and skeleton on image
        
        Args:
            image: Input image
            landmarks: List of landmark dictionaries
            joint_radius: Radius of joint circles
            line_thickness: Thickness of skeleton lines
            joint_color: Color of joints (BGR)
            line_color: Color of skeleton lines (BGR)
            
        Returns:
            Image with drawn landmarks
        """
        if not landmarks or len(landmarks) == 0:
            return image
        
        h, w = image.shape[:2]
        output_image = image.copy()
        
        # Filter valid landmarks
        valid_indices = [i for i, l in enumerate(landmarks) if l["confidence"] > self.confidence_threshold]
        
        if not valid_indices:
            return output_image
        
        # Draw skeleton
        for start_idx, end_idx in self.SKELETON_EDGES:
            if start_idx in valid_indices and end_idx in valid_indices:
                start = landmarks[start_idx]
                end = landmarks[end_idx]
                
                start_pos = (int(start["x"] * w), int(start["y"] * h))
                end_pos = (int(end["x"] * w), int(end["y"] * h))
                
                cv2.line(output_image, start_pos, end_pos, line_color, line_thickness)
        
        # Draw joints
        for i in valid_indices:
            landmark = landmarks[i]
            pos = (int(landmark["x"] * w), int(landmark["y"] * h))
            cv2.circle(output_image, pos, joint_radius, joint_color, -1)
        
        return output_image
    
    def get_2d_pose(self, landmarks: List[Dict]) -> np.ndarray:
        """
        Extract 2D pose from landmarks
        
        Returns:
            Array of shape (33, 2) with x, y coordinates
        """
        pose_2d = np.zeros((len(landmarks), 2))
        for i, landmark in enumerate(landmarks):
            pose_2d[i] = [landmark["x"], landmark["y"]]
        return pose_2d
    
    def get_3d_pose_placeholder(self, landmarks: List[Dict]) -> np.ndarray:
        """
        Extract 3D pose from landmarks (z is from MediaPipe depth estimation)
        
        Returns:
            Array of shape (33, 3) with x, y, z coordinates
        """
        pose_3d = np.zeros((len(landmarks), 3))
        for i, landmark in enumerate(landmarks):
            pose_3d[i] = [landmark["x"], landmark["y"], landmark["z"]]
        return pose_3d
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'pose'):
            self.pose.close()


def test_mediapipe_model():
    """Quick test of MediaPipe model"""
    model = MediaPipeModel()
    
    # Create dummy image
    dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Run detection
    result = model.detect(dummy_image)
    print(f"Detection successful: {result['success']}")
    print(f"Number of landmarks: {len(result['landmarks'])}")


if __name__ == "__main__":
    test_mediapipe_model()
