"""
SmartChallan AI - Automatic License Plate Recognition (ANPR) Module
Extracts motorcycle license plate ROIs, applies computer vision preprocessing,
and extracts alphanumeric registration numbers using deep-learning OCR (EasyOCR).
"""

import os
import re
import cv2
import numpy as np
from typing import Tuple, Optional

_READER = None


def get_ocr_reader():
    """Lazily loads and caches the EasyOCR English reader instance."""
    global _READER
    if _READER is None:
        try:
            import easyocr
            # Attempt CPU-based reader to ensure universal edge compatibility
            _READER = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            print(f"[SmartChallan ANPR] Note: EasyOCR loading: {e}")
            _READER = False
    return _READER


def extract_plate_roi(motorcycle_crop: np.ndarray) -> np.ndarray:
    """
    Isolates the lower region of the motorcycle bounding box where the
    license plate is typically mounted (lower 35% height, middle 70% width).
    """
    if motorcycle_crop is None or motorcycle_crop.size == 0:
        return np.zeros((60, 160, 3), dtype=np.uint8)

    h, w, _ = motorcycle_crop.shape

    # Focus on lower 35% height
    y_start = int(h * 0.65)
    y_end = h

    # Focus on middle 70% width
    x_start = int(w * 0.15)
    x_end = int(w * 0.85)

    plate_roi = motorcycle_crop[y_start:y_end, x_start:x_end]

    # If the crop is too small or empty, return the lower half
    if plate_roi.shape[0] < 15 or plate_roi.shape[1] < 30:
        plate_roi = motorcycle_crop[int(h * 0.5):, :]

    return plate_roi if plate_roi.size > 0 else motorcycle_crop


def preprocess_plate_image(plate_img: np.ndarray) -> np.ndarray:
    """
    Applies image preprocessing to improve OCR character edge contrast:
    - Grayscale conversion
    - Bilateral filtering for edge-preserving denoising
    - Contrast Limited Adaptive Histogram Equalization (CLAHE)
    """
    if plate_img is None or plate_img.size == 0:
        return plate_img

    # Convert to grayscale if 3 channels
    if len(plate_img.shape) == 3:
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_img

    # Resize up if very small to assist OCR
    gh, gw = gray.shape
    if gh < 80 or gw < 180:
        scale = max(80.0 / gh, 180.0 / gw)
        gray = cv2.resize(gray, (int(gw * scale), int(gh * scale)), interpolation=cv2.INTER_CUBIC)

    # Denoise while preserving sharp character boundaries
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)

    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    return enhanced


def clean_plate_text(raw_text: str) -> str:
    """Sanitizes OCR string to uppercase alphanumerics."""
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    return cleaned


def format_indian_plate(cleaned: str) -> str:
    """
    Attempts to format a standard Indian plate into readable chunks:
    e.g. MH12AB1234 -> MH 12 AB 1234
    """
    pattern = r'^([A-Z]{2})([0-9]{1,2})([A-Z]{1,3})([0-9]{4})$'
    match = re.match(pattern, cleaned)
    if match:
        return f"{match.group(1)} {match.group(2)} {match.group(3)} {match.group(4)}"
    return cleaned


def read_license_plate(plate_crop: np.ndarray, track_id: Optional[int] = None) -> Tuple[str, float]:
    """
    Extracts license plate number and confidence score from a plate crop.
    Falls back to a provisional ID if OCR cannot decipher characters.
    """
    fallback_id = f"IND-TMP-{track_id if track_id is not None else '01'}"
    fallback_conf = 0.65

    if plate_crop is None or plate_crop.size == 0:
        return fallback_id, fallback_conf

    processed = preprocess_plate_image(plate_crop)
    reader = get_ocr_reader()

    if not reader:
        # Fallback if EasyOCR is unavailable
        return fallback_id, fallback_conf

    try:
        results = reader.readtext(processed)
        if not results:
            # Try on original crop without CLAHE
            results = reader.readtext(plate_crop)

        best_text = ""
        best_conf = 0.0

        for bbox, text, conf in results:
            sanitized = clean_plate_text(text)
            # Plates typically have at least 4 alphanumeric characters
            if len(sanitized) >= 4 and conf > best_conf:
                best_text = sanitized
                best_conf = conf

        if best_text and best_conf > 0.35:
            formatted = format_indian_plate(best_text)
            return formatted, round(float(best_conf), 2)

    except Exception as e:
        print(f"[SmartChallan ANPR] OCR read error: {e}")

    return fallback_id, fallback_conf
