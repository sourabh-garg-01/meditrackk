from datetime import date
from pathlib import Path

import streamlit as st

from db.database import init_db, insert_document
from models.document import Document
from services.amount_extractor import extract_amount
from services.classifier import classify_event, extract_hospital_name, extract_patient_name
from services.date_extractor import extract_event_date
from services.image_processor import save_thumbnail
from services.ocr_service import extract_text
from utils.helpers import (
    SUPPORTED_EXTENSIONS,
    THUMBNAILS_DIR,
    UPLOADS_DIR,
    clean_text,
    ensure_app_directories,
    generate_id,
    now_iso,
    relative_to_base,
)


st.set_page_config(page_title="Upload - Meditrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()

st.title("Upload Document")

uploaded_file = st.file_uploader(
    "Choose a medical document",
    type=sorted(SUPPORTED_EXTENSIONS),
)

if uploaded_file:
    document_id = generate_id()
    suffix = Path(uploaded_file.name).suffix.lower()
    saved_path = UPLOADS_DIR / f"{document_id}{suffix}"
    saved_path.write_bytes(uploaded_file.getbuffer())

    with st.spinner("Running OCR locally..."):
        try:
            ocr_text = extract_text(saved_path)
        except Exception as exc:
            ocr_text = ""
            st.warning(f"OCR could not complete: {exc}")

    event_date, date_source = extract_event_date(ocr_text, date.today())
    event_type, event_title = classify_event(ocr_text)
    hospital_name = extract_hospital_name(ocr_text)
    patient_name = extract_patient_name(ocr_text)
    amount = extract_amount(ocr_text)

    thumbnail_path = THUMBNAILS_DIR / f"{document_id}.jpg"
    if suffix == ".pdf":
        thumbnail_path = saved_path
    else:
        save_thumbnail(saved_path, thumbnail_path)

    st.success("OCR Complete")

    with st.form("document_metadata"):
        col_left, col_right = st.columns(2)
        with col_left:
            edited_date = st.date_input("Date", value=date.fromisoformat(event_date))
            edited_title = st.text_input("Event Title", value=clean_text(event_title))
            edited_category = st.selectbox(
                "Category",
                ["Diagnostic", "Hospital", "Pharmacy", "Insurance", "Other"],
                index=["Diagnostic", "Hospital", "Pharmacy", "Insurance", "Other"].index(event_type),
            )
        with col_right:
            edited_hospital = st.text_input("Hospital/Lab", value=clean_text(hospital_name))
            edited_patient = st.text_input("Patient", value=clean_text(patient_name))
            edited_amount = st.number_input(
                "Amount",
                min_value=0.0,
                value=float(amount or 0.0),
                step=100.0,
            )

        st.caption(f"Date Source: {'Document' if date_source == 'document' else 'Upload Date'}")

        if ocr_text:
            with st.expander("OCR text"):
                st.text_area("Extracted text", value=ocr_text, height=220, disabled=True)

        saved = st.form_submit_button("Save to Timeline", use_container_width=True)

    if saved:
        document = Document(
            id=document_id,
            event_date=edited_date.isoformat(),
            date_source=date_source,
            event_type=edited_category,
            event_title=clean_text(edited_title),
            hospital_name=clean_text(edited_hospital),
            patient_name=clean_text(edited_patient),
            amount=edited_amount,
            thumbnail_path=relative_to_base(thumbnail_path),
            document_path=relative_to_base(saved_path),
            ocr_text=ocr_text,
            created_at=now_iso(),
        )
        insert_document(document)
        st.success("Saved to timeline.")
        st.page_link("pages/Timeline.py", label="Open Timeline")
