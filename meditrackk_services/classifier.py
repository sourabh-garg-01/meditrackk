import re


DIAGNOSTIC_KEYWORDS = {
    "CBC": ["cbc", "complete blood count"],
    "LFT": ["lft", "liver function"],
    "KFT": ["kft", "kidney function"],
    "Smear": ["smear"],
    "X-Ray": ["x-ray", "xray"],
    "CT Scan": ["ct scan"],
    "MRI": ["mri"],
    "Ultrasound": ["ultrasound", "usg"],
}

HOSPITAL_KEYWORDS = {
    "OPD Visit": ["opd", "consultation"],
    "Emergency Visit": ["emergency"],
    "Admission": ["admission", "admitted"],
    "Discharge": ["discharge"],
}


def classify_event(ocr_text: str) -> tuple[str, str]:
    text = ocr_text.lower()

    for title, keywords in DIAGNOSTIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return "Diagnostic", _diagnostic_title(title)

    for title, keywords in HOSPITAL_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return "Hospital", title

    if any(keyword in text for keyword in ["pharmacy", "medicine", "tablet", "capsule"]):
        return "Pharmacy", "Medicine Purchase"

    if any(keyword in text for keyword in ["claim", "insurance", "policy"]):
        return "Insurance", "Claim Document"

    if "report" in text:
        return "Other", "Medical Report"

    return "Other", "Unknown"


def _diagnostic_title(title: str) -> str:
    mapping = {
        "CBC": "CBC Blood Test",
        "LFT": "Liver Function Test",
        "KFT": "Kidney Function Test",
    }
    return mapping.get(title, title)


def extract_hospital_name(ocr_text: str) -> str:
    patterns = [
        r"([A-Z][A-Za-z&.\s]+(?:Hospital|Clinic|Laboratory|Lab|PathLabs|Diagnostics|Diagnostic Center))",
        r"((?:Dr\.?\s+)?[A-Z][A-Za-z&.\s]+(?:PathLabs|Labs))",
    ]
    for pattern in patterns:
        match = re.search(pattern, ocr_text)
        if match:
            return " ".join(match.group(1).split())
    return "Unknown"


def extract_patient_name(ocr_text: str) -> str:
    patterns = [
        r"(?:Patient Name|Patient|Beneficiary|Name)\s*[:\-]\s*([A-Za-z .]{2,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, ocr_text, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split())
    return "Unknown"
