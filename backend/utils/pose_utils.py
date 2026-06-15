"""
Pose-specific utilities
"""

import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def get_skeleton_edges() -> List[Tuple[int, int]]:
    """
    Get standard skeleton connection indices
    
    Returns:
        List of (start_idx, end_idx) tuples for skeleton edges
    """
    return [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (16, 18), (18, 20), (18, 22), (12, 14), (14, 16), (23, 24),
        (23, 25), (25, 27), (27, 29), (29, 31), (24, 26), (26, 28), (28, 30), (30, 32)
    ]

def filter_landmarks(
    landmarks: List[Dict],
    confidence_threshold: float = 0.5
) -> List[Dict]:
    """
    Filter landmarks by confidence threshold
    
    Args:
        landmarks: List of landmark dicts with 'confidence' key
        confidence_threshold: Minimum confidence value
        
    Returns:
        Filtered landmarks list
    """
    return [l for l in landmarks if l.get("confidence", 0) >= confidence_threshold]

def get_joint_angle(
    point1: np.ndarray,
    point2: np.ndarray,
    point3: np.ndarray
) -> float:
    """
    Calculate angle at point2 between point1-point2-point3
    
    Args:
        point1: First point (2D or 3D)
        point2: Vertex point
        point3: Third point
        
    Returns:
        Angle in degrees
    """
    v1 = point1 - point2
    v2 = point3 - point2
    
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    angle = np.arccos(cos_angle)
    return np.degrees(angle)

def get_pose_center(landmarks: List[Dict]) -> np.ndarray:
    """
    Calculate center of pose from landmarks
    
    Args:
        landmarks: List of landmark dicts with 'x', 'y' keys
        
    Returns:
        Center point as (x, y) or (x, y, z) array
    """
    if not landmarks:
        return np.array([0, 0])
    
    coords = []
    for l in landmarks:
        if "z" in l:
            coords.append([l["x"], l["y"], l["z"]])
        else:
            coords.append([l["x"], l["y"]])
    
    coords = np.array(coords)
    return np.mean(coords, axis=0)

def get_pose_scale(landmarks: List[Dict]) -> float:
    """
    Calculate scale/size of pose from landmarks
    
    Uses distance between shoulders as reference
    
    Args:
        landmarks: List of landmark dicts
        
    Returns:
        Scale value
    """
    if len(landmarks) < 13:  # Need at least shoulders (indices 11, 12)
        return 1.0
    
    left_shoulder = np.array([landmarks[11]["x"], landmarks[11]["y"]])
    right_shoulder = np.array([landmarks[12]["x"], landmarks[12]["y"]])
    
    scale = np.linalg.norm(right_shoulder - left_shoulder)
    return max(scale, 1e-6)

def normalize_pose(
    landmarks: List[Dict],
    center: bool = True,
    scale: bool = True
) -> List[Dict]:
    """
    Normalize pose for consistency
    
    Args:
        landmarks: List of landmark dicts
        center: Center pose at origin
        scale: Normalize pose scale
        
    Returns:
        Normalized landmarks
    """
    normalized = [l.copy() for l in landmarks]
    
    if center:
        center_point = get_pose_center(landmarks)
        for l in normalized:
            l["x"] -= center_point[0]
            l["y"] -= center_point[1]
            if "z" in l and len(center_point) > 2:
                l["z"] -= center_point[2]
    
    if scale:
        scale_value = get_pose_scale(normalized)
        for l in normalized:
            l["x"] /= scale_value
            l["y"] /= scale_value
            if "z" in l:
                l["z"] /= scale_value
    
    return normalized

def compute_pose_embedding(landmarks: List[Dict]) -> np.ndarray:
    """
    Compute pose embedding for similarity comparison
    
    Args:
        landmarks: List of landmark dicts
        
    Returns:
        Pose embedding vector
    """
    normalized = normalize_pose(landmarks, center=True, scale=True)
    
    coords = []
    for l in normalized:
        if "z" in l:
            coords.append([l["x"], l["y"], l["z"]])
        else:
            coords.append([l["x"], l["y"]])
    
    embedding = np.array(coords).flatten()
    return embedding

def pose_similarity(
    landmarks1: List[Dict],
    landmarks2: List[Dict]
) -> float:
    """
    Calculate similarity between two poses
    
    Args:
        landmarks1: First pose landmarks
        landmarks2: Second pose landmarks
        
    Returns:
        Similarity score (0-1, higher is more similar)
    """
    if len(landmarks1) != len(landmarks2):
        return 0.0
    
    emb1 = compute_pose_embedding(landmarks1)
    emb2 = compute_pose_embedding(landmarks2)
    
    # Cosine similarity
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-6)
    return float(np.clip(sim, 0, 1))

def get_body_part_landmarks(landmarks: List[Dict], body_part: str) -> List[Dict]:
    """
    Extract specific body part landmarks
    
    Args:
        landmarks: List of all landmarks
        body_part: 'head', 'torso', 'arms', 'legs', 'left_arm', 'right_arm', etc.
        
    Returns:
        Filtered landmarks for body part
    """
    # Define indices for each body part
    parts = {
        "head": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "torso": [11, 12, 23, 24],
        "left_arm": [11, 13, 15, 17, 19, 21],
        "right_arm": [12, 14, 16, 18, 20, 22],
        "left_leg": [23, 25, 27, 29, 31],
        "right_leg": [24, 26, 28, 30, 32],
        "arms": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        "legs": [23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
    }
    
    if body_part not in parts:
        logger.warning(f"Unknown body part: {body_part}")
        return landmarks
    
    indices = parts[body_part]
    return [landmarks[i] for i in indices if i < len(landmarks)]

def compute_keypoint_distances(landmarks: List[Dict]) -> Dict[Tuple[int, int], float]:
    """
    Compute pairwise distances between all landmarks
    
    Args:
        landmarks: List of landmark dicts
        
    Returns:
        Dictionary mapping (idx1, idx2) -> distance
    """
    distances = {}
    
    for i in range(len(landmarks)):
        for j in range(i + 1, len(landmarks)):
            p1 = np.array([landmarks[i]["x"], landmarks[i]["y"]])
            p2 = np.array([landmarks[j]["x"], landmarks[j]["y"]])
            
            dist = np.linalg.norm(p2 - p1)
            distances[(i, j)] = float(dist)
    
    return distances
