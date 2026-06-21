from datetime import datetime
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


def format_amount(amount: float | None) -> str:
    if amount is None:
        return "Not found"
    return f"Rs. {amount:,.2f}"


def relative_to_base(path: Path) -> str:
    return str(path.resolve().relative_to(BASE_DIR)).replace("\\", "/")
