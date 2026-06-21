from dataclasses import dataclass


@dataclass
class Document:
    id: str
    event_date: str
    date_source: str
    event_type: str
    event_title: str
    hospital_name: str
    patient_name: str
    amount: float | None
    thumbnail_path: str
    document_path: str
    ocr_text: str
    created_at: str
