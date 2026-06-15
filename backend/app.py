"""
Main FastAPI application for 3D pose reconstruction
Phase 1: MVP with MediaPipe
"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np

from backend.config import settings
from backend.models import MediaPipeModel
from backend.api.schemas import PoseDetectionResponse, HealthResponse, Landmark, BoundingBox
from backend.utils.pose_utils import filter_landmarks

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Global model instance
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    Load model on startup, cleanup on shutdown
    """
    global model
    
    # Startup
    logger.info("Starting application...")
    try:
        logger.info(f"Loading {settings.MODEL_PROVIDER} model...")
        model = MediaPipeModel(confidence_threshold=settings.CONFIDENCE_THRESHOLD)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if model is not None:
        del model
    logger.info("Cleanup complete")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="3D Human Pose Reconstruction from Single Images",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== Health & Info Endpoints =====================

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint"""
    return {
        "message": "3D Pose Reconstruction API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        model_provider=settings.MODEL_PROVIDER,
        device=settings.DEVICE
    )

@app.get("/api/v1/info", tags=["Info"])
async def model_info():
    """Get information about loaded model"""
    return {
        "model_provider": settings.MODEL_PROVIDER,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
        "max_people": settings.MAX_PEOPLE,
        "device": settings.DEVICE,
        "num_landmarks": 33,  # MediaPipe has 33 landmarks
        "optimization": {
            "onnx_enabled": settings.USE_ONNX,
            "tensorrt_enabled": settings.USE_TENSORRT,
            "batch_size": settings.BATCH_SIZE
        }
    }

# ===================== Pose Detection Endpoints =====================

@app.post(
    f"{settings.API_PREFIX}/detect",
    response_model=PoseDetectionResponse,
    tags=["Pose Detection"],
    summary="Detect pose from image"
)
async def detect_pose(file: UploadFile = File(...)):
    """
    Detect human pose from uploaded image
    
    - **file**: Image file (jpg, png, bmp, webp)
    
    Returns pose landmarks with confidence scores
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in settings.ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {settings.ALLOWED_FORMATS}"
        )
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None or image.size == 0:
            raise HTTPException(status_code=400, detail="Failed to decode image")
        
        # Validate image dimensions
        h, w = image.shape[:2]
        if h < settings.MIN_IMAGE_SIZE or w < settings.MIN_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too small. Minimum: {settings.MIN_IMAGE_SIZE}x{settings.MIN_IMAGE_SIZE}"
            )
        if h > settings.MAX_IMAGE_SIZE or w > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum: {settings.MAX_IMAGE_SIZE}x{settings.MAX_IMAGE_SIZE}"
            )
        
        # Run detection
        logger.info(f"Processing image: {file.filename} ({w}x{h})")
        detection_result = model.detect(image)
        
        if not detection_result["success"]:
            logger.error(f"Detection failed: {detection_result.get('error')}")
            return PoseDetectionResponse(
                success=False,
                landmarks=[],
                landmark_names=[],
                bbox=None,
                confidence=0.0,
                num_people=0,
                image_shape=[h, w],
                error=detection_result.get("error", "Unknown error")
            )
        
        # Convert to response format
        landmarks = detection_result.get("landmarks", [])
        landmark_objects = []
        for i, l in enumerate(landmarks):
            name = detection_result.get("landmark_names", [])[i] if i < len(detection_result.get("landmark_names", [])) else None
            landmark_objects.append(
                Landmark(
                    x=l["x"],
                    y=l["y"],
                    z=l.get("z"),
                    confidence=l.get("confidence"),
                    name=name
                )
            )
        
        bbox = None
        if detection_result.get("bbox"):
            bbox_data = detection_result["bbox"]
            bbox = BoundingBox(
                xmin=bbox_data["xmin"],
                ymin=bbox_data["ymin"],
                xmax=bbox_data["xmax"],
                ymax=bbox_data["ymax"],
                width=bbox_data["width"],
                height=bbox_data["height"]
            )
        
        response = PoseDetectionResponse(
            success=True,
            landmarks=landmark_objects,
            landmark_names=detection_result.get("landmark_names"),
            bbox=bbox,
            confidence=detection_result.get("confidence", 0.0),
            num_people=detection_result.get("num_people", 0),
            image_shape=detection_result.get("image_shape", [h, w])
        )
        
        logger.info(f"Detection successful: {len(landmarks)} landmarks detected")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during pose detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# ===================== Visualization Endpoint =====================

@app.post(
    f"{settings.API_PREFIX}/visualize",
    tags=["Visualization"],
    summary="Draw pose on image"
)
async def visualize_pose(
    file: UploadFile = File(...),
    joint_radius: int = 4,
    line_thickness: int = 2
):
    """
    Detect pose and return image with drawn skeleton
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None or image.size == 0:
            raise HTTPException(status_code=400, detail="Failed to decode image")
        
        # Detect pose
        detection_result = model.detect(image)
        
        if not detection_result["success"] or not detection_result.get("landmarks"):
            raise HTTPException(status_code=400, detail="No pose detected")
        
        landmarks = detection_result["landmarks"]
        
        # Draw landmarks
        output_image = model.draw_landmarks(
            image,
            landmarks,
            joint_radius=joint_radius,
            line_thickness=line_thickness
        )
        
        # Encode to JPEG
        _, buffer = cv2.imencode(".jpg", output_image)
        
        return {
            "image": buffer.tobytes().hex(),
            "format": "jpeg",
            "num_landmarks": len(landmarks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# ===================== Error Handlers =====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ===================== Entry Point =====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
