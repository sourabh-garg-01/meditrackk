import base64
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from pdf2image import convert_from_path
from PIL import Image


DEFAULT_AI_OCR_MODEL = "gpt-4o-mini"


def get_ai_ocr_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


def is_ai_ocr_available(api_key: str | None = None) -> bool:
    return bool(api_key or get_ai_ocr_key())


def extract_metadata_with_ai(document_path: Path, api_key: str | None = None) -> dict:
    api_key = api_key or get_ai_ocr_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("AI_OCR_MODEL", DEFAULT_AI_OCR_MODEL)
    image_payloads = _document_to_image_payloads(document_path)

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured data from Indian medical documents. "
                    "Return only valid JSON. If a value is missing, use null. "
                    "Prefer final payable amount over intermediate amounts."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract this JSON object: "
                            "{event_date,date_source,event_type,event_title,"
                            "hospital_name,patient_name,amount,conditions,ocr_text}. "
                            "event_date must be YYYY-MM-DD when visible. "
                            "date_source must be document when found, otherwise null. "
                            "event_type must be Diagnostic, Hospital, Pharmacy, Insurance, or Other."
                        ),
                    },
                    *image_payloads,
                ],
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    data["ocr_text"] = data.get("ocr_text") or ""
    return data


def _document_to_image_payloads(document_path: Path) -> list[dict]:
    paths: list[Path] = []
    if document_path.suffix.lower() == ".pdf":
        with TemporaryDirectory() as temp_dir:
            pages = convert_from_path(str(document_path), dpi=160, first_page=1, last_page=3)
            for index, page in enumerate(pages, start=1):
                image_path = Path(temp_dir) / f"page-{index}.jpg"
                page.save(image_path, "JPEG", quality=85)
                paths.append(image_path)
            return [_image_payload(path) for path in paths]

    return [_image_payload(document_path)]


def _image_payload(image_path: Path) -> dict:
    with Image.open(image_path) as image:
        image.thumbnail((1400, 1400))
        with TemporaryDirectory() as temp_dir:
            normalized_path = Path(temp_dir) / "image.jpg"
            image.convert("RGB").save(normalized_path, "JPEG", quality=85)
            encoded = base64.b64encode(normalized_path.read_bytes()).decode("ascii")

    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{encoded}",
        },
    }
