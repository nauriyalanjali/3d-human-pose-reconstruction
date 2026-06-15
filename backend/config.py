"""
Configuration management for the pose reconstruction application
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "3D Pose Reconstruction API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Paths
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    UPLOADS_DIR: Path = PROJECT_ROOT / "uploads"
    
    # Model configuration
    MODEL_PROVIDER: str = "mediapipe"  # mediapipe, hrnet, vibe
    CONFIDENCE_THRESHOLD: float = 0.5
    MAX_PEOPLE: int = 10
    
    # GPU/Device
    DEVICE: str = "cuda"  # cuda, cpu
    GPU_ID: int = 0
    
    # Optimization
    USE_ONNX: bool = False
    USE_TENSORRT: bool = False
    BATCH_SIZE: int = 1
    
    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Model URLs
    MEDIAPIPE_MODEL_URL: str = "https://storage.googleapis.com/mediapipe-models/image_classifier/efficientnet_lite0/float16/latest.tflite"
    HRNET_MODEL_URL: str = "https://github.com/leoxiaobin/deep-high-resolution-net.pytorch/releases/download/hrnetv2/hrnetv2_w32_imagenet.pth"
    
    # Input validation
    MAX_IMAGE_SIZE: int = 2048
    MIN_IMAGE_SIZE: int = 64
    ALLOWED_FORMATS: list = ["jpg", "jpeg", "png", "bmp", "webp"]
    
    # Output
    OUTPUT_SKELETON_THICKNESS: int = 2
    OUTPUT_JOINT_RADIUS: int = 4
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create necessary directories
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
