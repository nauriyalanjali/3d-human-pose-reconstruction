"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class PoseDetectionFormat(str, Enum):
    """Supported output formats"""
    JSON = "json"
    NUMPY = "numpy"

class Landmark(BaseModel):
    """Single 3D landmark"""
    x: float
    y: float
    z: Optional[float] = None
    confidence: Optional[float] = None
    name: Optional[str] = None

class BoundingBox(BaseModel):
    """2D bounding box"""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    width: int
    height: int

class PoseDetectionResponse(BaseModel):
    """Response from pose detection endpoint"""
    success: bool
    landmarks: List[Landmark]
    landmark_names: Optional[List[str]] = None
    bbox: Optional[BoundingBox] = None
    confidence: float
    num_people: int
    image_shape: List[int]
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "landmarks": [
                    {"x": 0.5, "y": 0.3, "z": 0.0, "confidence": 0.95, "name": "nose"},
                ],
                "landmark_names": ["nose", "left_eye", "right_eye"],
                "bbox": {
                    "xmin": 0.1,
                    "ymin": 0.1,
                    "xmax": 0.9,
                    "ymax": 0.9,
                    "width": 640,
                    "height": 480
                },
                "confidence": 0.92,
                "num_people": 1,
                "image_shape": [480, 640]
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    model_provider: str
    device: str

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid image format",
                "error_code": "INVALID_IMAGE"
            }
        }

class VisualizationRequest(BaseModel):
    """Request for pose visualization"""
    landmarks: List[Landmark]
    image_width: int
    image_height: int
    joint_radius: Optional[int] = 4
    line_thickness: Optional[int] = 2
    joint_color: Optional[List[int]] = [0, 255, 0]  # BGR
    line_color: Optional[List[int]] = [255, 0, 0]   # BGR

class PoseSimilarityRequest(BaseModel):
    """Request to compare two poses"""
    landmarks1: List[Landmark]
    landmarks2: List[Landmark]

class PoseSimilarityResponse(BaseModel):
    """Response from pose similarity"""
    similarity_score: float
    interpretation: str
    
    class Config:
        schema_extra = {
            "example": {
                "similarity_score": 0.87,
                "interpretation": "Very similar poses"
            }
        }

class ModelInfoResponse(BaseModel):
    """Information about loaded model"""
    name: str
    version: str
    num_landmarks: int
    supported_formats: List[str]
    description: str
    performance_info: Optional[Dict[str, Any]] = None

class BatchPoseDetectionRequest(BaseModel):
    """Batch pose detection request"""
    image_count: int
    descriptions: List[str]
    
class BatchPoseDetectionResponse(BaseModel):
    """Batch detection response"""
    total_processed: int
    successful: int
    failed: int
    results: List[PoseDetectionResponse]
