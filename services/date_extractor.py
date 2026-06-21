from datetime import date
import re

import dateparser


DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b",
]


def extract_event_date(ocr_text: str, upload_date: date | None = None) -> tuple[str, str]:
    upload_date = upload_date or date.today()
    for pattern in DATE_PATTERNS:
        for match in re.findall(pattern, ocr_text, flags=re.IGNORECASE):
            parsed = dateparser.parse(match, settings={"DATE_ORDER": "DMY"})
            if parsed:
                return parsed.date().isoformat(), "document"
    return upload_date.isoformat(), "upload"
