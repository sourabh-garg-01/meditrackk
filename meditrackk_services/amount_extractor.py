import re


PREFERRED_LABELS = [
    "total amount",
    "grand total",
    "net amount",
    "amount paid",
    "total payable",
]


def _parse_amount(value: str) -> float | None:
    cleaned = value.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_amount(ocr_text: str) -> float | None:
    lower_text = ocr_text.lower()
    for label in PREFERRED_LABELS:
        pattern = rf"{re.escape(label)}\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9][0-9,]*(?:\.\d{{1,2}})?)"
        match = re.search(pattern, lower_text, flags=re.IGNORECASE)
        if match:
            return _parse_amount(match.group(1))

    amounts = re.findall(r"(?:rs\.?|inr|₹)\s*([0-9][0-9,]*(?:\.\d{1,2})?)", ocr_text, flags=re.IGNORECASE)
    parsed_amounts = [amount for amount in (_parse_amount(value) for value in amounts) if amount is not None]
    return max(parsed_amounts) if parsed_amounts else None
