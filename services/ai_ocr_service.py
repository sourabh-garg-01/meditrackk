import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from pdf2image import convert_from_path
from PIL import Image


DEFAULT_AI_OCR_MODEL = "gemini-3.5-flash"


def get_ai_ocr_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


def is_ai_ocr_available(api_key: str | None = None) -> bool:
    return bool(api_key or get_ai_ocr_key())


def extract_metadata_with_ai(document_path: Path, api_key: str | None = None) -> dict:
    api_key = api_key or get_ai_ocr_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    model = os.getenv("AI_OCR_MODEL", DEFAULT_AI_OCR_MODEL)
    image_parts = _document_to_image_parts(document_path)

    response = client.models.generate_content(
        model=model,
        contents=[
            *image_parts,
            (
                "You extract structured data from Indian medical documents. "
                "Return only valid JSON with these keys: "
                "event_date, date_source, event_type, event_title, hospital_name, "
                "patient_name, amount, conditions, ocr_text. "
                "event_date must be YYYY-MM-DD when visible. "
                "date_source must be document when found, otherwise null. "
                "event_type must be Diagnostic, Hospital, Pharmacy, Insurance, or Other. "
                "Prefer final payable amount over intermediate amounts. "
                "conditions must be an array of short condition names found in the document. "
                "If a value is missing, use null."
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text or "{}")
    data["ocr_text"] = data.get("ocr_text") or ""
    return data


def _document_to_image_parts(document_path: Path):
    if document_path.suffix.lower() == ".pdf":
        with TemporaryDirectory() as temp_dir:
            pages = convert_from_path(str(document_path), dpi=160, first_page=1, last_page=3)
            parts = []
            for index, page in enumerate(pages, start=1):
                image_path = Path(temp_dir) / f"page-{index}.jpg"
                page.save(image_path, "JPEG", quality=85)
                parts.append(_image_part(image_path))
            return parts

    return [_image_part(document_path)]


def _image_part(image_path: Path):
    from google.genai import types

    with Image.open(image_path) as image:
        image.thumbnail((1400, 1400))
        with TemporaryDirectory() as temp_dir:
            normalized_path = Path(temp_dir) / "image.jpg"
            image.convert("RGB").save(normalized_path, "JPEG", quality=85)
            image_bytes = normalized_path.read_bytes()

    return types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
