from datetime import datetime
import hashlib
import re
from pathlib import Path
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
THUMBNAILS_DIR = BASE_DIR / "thumbnails"
DATABASE_DIR = BASE_DIR / "database"

SUPPORTED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "pdf"}


def ensure_app_directories() -> None:
    for directory in (UPLOADS_DIR, THUMBNAILS_DIR, DATABASE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def generate_id() -> str:
    return str(uuid4())


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def clean_text(value: str | None, default: str = "Unknown") -> str:
    if not value:
        return default
    cleaned = " ".join(value.split())
    return cleaned if cleaned else default


def normalize_provider_name(value: str | None) -> str:
    cleaned = clean_text(value, "Unknown").lower()
    cleaned = re.sub(r"\b(hospitals|hospital|clinic|laboratory|laboratories|diagnostics|diagnostic|pvt|ltd)\b", "", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return " ".join(cleaned.split()) or "unknown"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_duplicate_key(
    event_date: str,
    event_title: str,
    hospital_name: str,
    patient_name: str,
    amount: float | None,
    document_hash: str,
) -> str:
    parts = [
        event_date or "",
        clean_text(event_title, "").lower(),
        normalize_provider_name(hospital_name),
        clean_text(patient_name, "").lower(),
        str(round(float(amount or 0), 2)),
        document_hash[:16],
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def format_amount(amount: float | None) -> str:
    if amount is None:
        return "Not found"
    return f"Rs. {amount:,.2f}"


def relative_to_base(path: Path) -> str:
    return str(path.resolve().relative_to(BASE_DIR)).replace("\\", "/")
