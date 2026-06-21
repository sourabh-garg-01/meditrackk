from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from pdf2image import convert_from_path

from meditrackk_data.database import find_duplicates
from meditrackk_models.document import Document
from meditrackk_services.ai_ocr_service import extract_metadata_from_image_with_ai
from meditrackk_services.amount_extractor import extract_amount
from meditrackk_services.classifier import classify_event, extract_hospital_name, extract_patient_name
from meditrackk_services.date_extractor import extract_event_date
from meditrackk_services.image_processor import save_thumbnail
from meditrackk_services.ocr_service import extract_text
from meditrackk_utils.helpers import (
    THUMBNAILS_DIR,
    clean_text,
    file_sha256,
    generate_id,
    make_duplicate_key,
    normalize_provider_name,
    now_iso,
    relative_to_base,
)


def prepare_documents_from_upload(saved_path: Path, source_file_name: str, api_key: str | None = None) -> list[dict]:
    if saved_path.suffix.lower() == ".pdf":
        return _prepare_pdf_pages(saved_path, source_file_name, api_key)
    return [_prepare_one_document(saved_path, source_file_name, api_key=api_key, page_number=None)]


def _prepare_pdf_pages(saved_path: Path, source_file_name: str, api_key: str | None) -> list[dict]:
    prepared = []
    with TemporaryDirectory() as temp_dir:
        pages = convert_from_path(str(saved_path), dpi=180)
        for index, page in enumerate(pages, start=1):
            page_path = Path(temp_dir) / f"page-{index}.jpg"
            page.save(page_path, "JPEG", quality=90)
            prepared.append(
                _prepare_one_document(
                    page_path,
                    source_file_name,
                    api_key=api_key,
                    page_number=index,
                    original_document_path=saved_path,
                )
            )

    unique = []
    seen_keys = set()
    for item in prepared:
        key = item["document"].duplicate_key
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(item)
    return unique


def _prepare_one_document(
    image_path: Path,
    source_file_name: str,
    api_key: str | None,
    page_number: int | None,
    original_document_path: Path | None = None,
) -> dict:
    document_id = generate_id()
    document_path = original_document_path or image_path
    thumbnail_path = THUMBNAILS_DIR / f"{document_id}.jpg"
    save_thumbnail(image_path, thumbnail_path)

    ai_data = {}
    ocr_text = ""
    ai_error = ""
    local_ocr_error = ""
    if api_key:
        try:
            ai_data = extract_metadata_from_image_with_ai(image_path, api_key=api_key)
            ocr_text = ai_data.get("ocr_text") or ""
        except Exception as exc:
            ai_error = str(exc)
            ai_data = {}
    else:
        ai_error = "GEMINI_API_KEY is not configured in Streamlit Secrets."

    if not ai_data:
        try:
            ocr_text = extract_text(image_path)
        except Exception as exc:
            local_ocr_error = str(exc)
            ocr_text = ""

    event_date, date_source = extract_event_date(ocr_text, date.today())
    event_type, event_title = classify_event(ocr_text)
    amount = _normalize_amount(ai_data.get("amount")) if ai_data else None
    if amount is None:
        amount = extract_amount(ocr_text)

    hospital_name = ai_data.get("hospital_name") or extract_hospital_name(ocr_text)
    patient_name = ai_data.get("patient_name") or extract_patient_name(ocr_text)
    event_date = _normalize_event_date(ai_data.get("event_date"), event_date)
    event_type = _normalize_category(ai_data.get("event_type") or event_type)
    event_title = ai_data.get("event_title") or event_title
    conditions = _join_list(ai_data.get("conditions"))
    test_results = _join_list(ai_data.get("test_results"))
    document_hash = file_sha256(image_path)
    duplicate_key = make_duplicate_key(event_date, event_title, hospital_name, patient_name, amount, document_hash)

    document = Document(
        id=document_id,
        event_date=event_date,
        date_source=ai_data.get("date_source") or date_source,
        event_type=event_type,
        event_title=clean_text(event_title),
        hospital_name=clean_text(hospital_name),
        provider_city=clean_text(ai_data.get("provider_city"), ""),
        normalized_provider=normalize_provider_name(hospital_name),
        patient_name=clean_text(patient_name),
        amount=amount,
        thumbnail_path=relative_to_base(thumbnail_path),
        document_path=relative_to_base(document_path),
        ocr_text=ocr_text,
        conditions=conditions,
        test_results=test_results,
        document_hash=document_hash,
        duplicate_key=duplicate_key,
        source_file_name=source_file_name,
        page_number=page_number,
        created_at=now_iso(),
    )
    return {
        "document": document,
        "duplicates": find_duplicates(duplicate_key, document_hash),
        "ai_error": ai_error,
        "local_ocr_error": local_ocr_error,
        "used_ai": bool(ai_data),
    }


def _join_list(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item)
    return str(value)


def _normalize_amount(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = "".join(ch for ch in str(value) if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_category(value: str | None) -> str:
    categories = ["Diagnostic", "Hospital", "Pharmacy", "Insurance", "Other"]
    if not value:
        return "Other"
    lowered = value.lower()
    for category in categories:
        if category.lower() in lowered:
            return category
    if "opd" in lowered:
        return "Hospital"
    if "bill" in lowered or "test" in lowered or "report" in lowered:
        return "Diagnostic"
    return "Other"


def _normalize_event_date(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return fallback
