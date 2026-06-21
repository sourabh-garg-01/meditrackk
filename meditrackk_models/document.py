from dataclasses import dataclass


@dataclass
class Document:
    id: str
    event_date: str
    date_source: str
    event_type: str
    event_title: str
    hospital_name: str
    provider_city: str
    normalized_provider: str
    patient_name: str
    amount: float | None
    thumbnail_path: str
    document_path: str
    ocr_text: str
    conditions: str
    test_results: str
    document_hash: str
    duplicate_key: str
    source_file_name: str
    page_number: int | None
    created_at: str
