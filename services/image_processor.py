from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def preprocess_image(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=12)
    enhanced = cv2.equalizeHist(denoised)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, sharpen_kernel)
    thresholded = cv2.adaptiveThreshold(
        sharpened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    return thresholded


def save_thumbnail(source_path: Path, thumbnail_path: Path, size: tuple[int, int] = (360, 360)) -> None:
    image = Image.open(source_path)
    image.thumbnail(size)
    image.convert("RGB").save(thumbnail_path, "JPEG", quality=85)
