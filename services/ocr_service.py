from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2
from pdf2image import convert_from_path

from services.image_processor import preprocess_image


@lru_cache(maxsize=1)
def get_ocr_engine():
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            "PaddleOCR is not installed in this environment. "
            "Install optional OCR dependencies with: "
            "pip install -r requirements-ocr.txt"
        ) from exc

    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


def extract_text_from_image(image_path: Path) -> str:
    processed = preprocess_image(image_path)
    with TemporaryDirectory() as temp_dir:
        processed_path = Path(temp_dir) / "processed.png"
        cv2.imwrite(str(processed_path), processed)
        result = get_ocr_engine().ocr(str(processed_path), cls=True)

    lines: list[str] = []
    for page in result or []:
        for item in page or []:
            if len(item) >= 2 and item[1]:
                lines.append(str(item[1][0]))
    return "\n".join(lines)


def extract_text_from_pdf(pdf_path: Path) -> str:
    text_parts: list[str] = []
    with TemporaryDirectory() as temp_dir:
        pages = convert_from_path(str(pdf_path), dpi=200, output_folder=temp_dir)
        for index, page in enumerate(pages, start=1):
            image_path = Path(temp_dir) / f"page-{index}.jpg"
            page.save(image_path, "JPEG")
            text_parts.append(extract_text_from_image(image_path))
    return "\n\n".join(part for part in text_parts if part)


def extract_text(document_path: Path) -> str:
    if document_path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(document_path)
    return extract_text_from_image(document_path)
