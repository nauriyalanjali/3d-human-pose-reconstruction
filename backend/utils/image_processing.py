"""
Image processing utilities
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def preprocess_image(
    image: np.ndarray,
    target_size: Optional[Tuple[int, int]] = None,
    normalize: bool = True
) -> np.ndarray:
    """
    Preprocess image for model inference
    
    Args:
        image: Input image (BGR format)
        target_size: Target image size (height, width)
        normalize: Whether to normalize to [0, 1]
        
    Returns:
        Preprocessed image
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image")
    
    # Resize if target size specified
    if target_size is not None:
        image = cv2.resize(image, (target_size[1], target_size[0]))
    
    # Convert to float
    processed = image.astype(np.float32)
    
    # Normalize
    if normalize:
        processed = processed / 255.0
    
    return processed

def postprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Convert processed image back to displayable format
    
    Args:
        image: Processed image (float format)
        
    Returns:
        Image in uint8 format (0-255)
    """
    if image.dtype == np.float32 or image.dtype == np.float64:
        image = np.clip(image * 255, 0, 255).astype(np.uint8)
    return image

def resize_image(
    image: np.ndarray,
    max_size: int = 2048,
    min_size: int = 64
) -> Tuple[np.ndarray, float]:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: Input image
        max_size: Maximum width/height
        min_size: Minimum width/height
        
    Returns:
        Resized image and scale factor
    """
    h, w = image.shape[:2]
    
    # Check min size
    if h < min_size or w < min_size:
        scale = min_size / min(h, w)
    else:
        scale = 1.0
    
    # Check max size
    if h > max_size or w > max_size:
        scale = max_size / max(h, w)
    
    if scale != 1.0:
        new_h, new_w = int(h * scale), int(w * scale)
        image = cv2.resize(image, (new_w, new_h))
    
    return image, scale

def pad_image(
    image: np.ndarray,
    target_size: Tuple[int, int],
    color: Tuple[int, int, int] = (0, 0, 0)
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Pad image to target size while maintaining aspect ratio
    
    Args:
        image: Input image
        target_size: Target (height, width)
        color: Padding color (BGR)
        
    Returns:
        Padded image and offset (y, x)
    """
    h, w = image.shape[:2]
    target_h, target_w = target_size
    
    # Calculate scaling to fit
    scale = min(target_w / w, target_h / h)
    new_h, new_w = int(h * scale), int(w * scale)
    
    # Resize
    resized = cv2.resize(image, (new_w, new_h))
    
    # Create padded image
    padded = np.full((target_h, target_w, 3), color, dtype=np.uint8)
    
    # Calculate offset
    offset_y = (target_h - new_h) // 2
    offset_x = (target_w - new_w) // 2
    
    # Place resized image
    padded[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = resized
    
    return padded, (offset_y, offset_x)

def augment_image(
    image: np.ndarray,
    hflip: bool = False,
    brightness: float = 0.0,
    contrast: float = 1.0
) -> np.ndarray:
    """
    Apply data augmentation to image
    
    Args:
        image: Input image
        hflip: Horizontal flip
        brightness: Brightness adjustment (-100 to 100)
        contrast: Contrast adjustment (0.5 to 2.0)
        
    Returns:
        Augmented image
    """
    result = image.copy()
    
    # Horizontal flip
    if hflip:
        result = cv2.flip(result, 1)
    
    # Brightness
    if brightness != 0:
        result = cv2.convertScaleAbs(result, alpha=1, beta=brightness)
    
    # Contrast
    if contrast != 1.0:
        result = cv2.convertScaleAbs(result, alpha=contrast, beta=0)
    
    return result

def crop_bbox(
    image: np.ndarray,
    bbox: dict,
    padding: float = 0.1
) -> Optional[np.ndarray]:
    """
    Crop image to bounding box with padding
    
    Args:
        image: Input image
        bbox: Bounding box dict with xmin, ymin, xmax, ymax (normalized 0-1)
        padding: Padding as fraction of bbox size
        
    Returns:
        Cropped image
    """
    h, w = image.shape[:2]
    
    xmin = int(bbox["xmin"] * w)
    ymin = int(bbox["ymin"] * h)
    xmax = int(bbox["xmax"] * w)
    ymax = int(bbox["ymax"] * h)
    
    # Add padding
    bw = xmax - xmin
    bh = ymax - ymin
    
    xmin = max(0, int(xmin - bw * padding))
    ymin = max(0, int(ymin - bh * padding))
    xmax = min(w, int(xmax + bw * padding))
    ymax = min(h, int(ymax + bh * padding))
    
    return image[ymin:ymax, xmin:xmax]

def convert_color_space(
    image: np.ndarray,
    from_space: str = "BGR",
    to_space: str = "RGB"
) -> np.ndarray:
    """
    Convert image between color spaces
    
    Args:
        image: Input image
        from_space: Source color space (BGR, RGB, HSV, GRAY)
        to_space: Target color space
        
    Returns:
        Converted image
    """
    conversion_map = {
        ("BGR", "RGB"): cv2.COLOR_BGR2RGB,
        ("RGB", "BGR"): cv2.COLOR_RGB2BGR,
        ("BGR", "HSV"): cv2.COLOR_BGR2HSV,
        ("RGB", "HSV"): cv2.COLOR_RGB2HSV,
        ("BGR", "GRAY"): cv2.COLOR_BGR2GRAY,
        ("RGB", "GRAY"): cv2.COLOR_RGB2GRAY,
    }
    
    if from_space == to_space:
        return image
    
    key = (from_space, to_space)
    if key not in conversion_map:
        raise ValueError(f"Unsupported conversion: {from_space} -> {to_space}")
    
    return cv2.cvtColor(image, conversion_map[key])
