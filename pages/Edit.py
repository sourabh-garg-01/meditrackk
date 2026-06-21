from datetime import date

import streamlit as st

from db.database import fetch_document, fetch_documents, init_db, update_document
from models.document import Document
from utils.helpers import clean_text, ensure_app_directories
from utils.ui import inject_dashboard_css


st.set_page_config(page_title="Edit - Meditrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()
inject_dashboard_css()

st.markdown(
    """
    <div class="hero">
      <div class="brand">
        <div class="brand-icon">M</div>
        <div>
          <div class="brand-title">Edit document</div>
          <div class="brand-subtitle">Correct extracted details and keep your timeline clean</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_home, col_add = st.columns(2)
with col_home:
    st.page_link("app.py", label="Home dashboard")
with col_add:
    st.page_link("pages/Upload.py", label="Add another document")

document_id = st.session_state.get("edit_document_id")
documents = fetch_documents()

if not document_id and documents:
    labels = {
        f"{doc['event_date']} - {doc['event_title']} - {doc['hospital_name']}": doc["id"]
        for doc in documents
    }
    selected_label = st.selectbox("Choose document", list(labels))
    document_id = labels[selected_label]

if not document_id:
    st.info("No document selected.")
    st.stop()

document = fetch_document(document_id)
if not document:
    st.error("This document could not be found.")
    st.stop()

categories = ["Diagnostic", "Hospital", "Pharmacy", "Insurance", "Other"]
category = document["event_type"] if document["event_type"] in categories else "Other"

with st.form("edit_document"):
    col_left, col_right = st.columns(2)
    with col_left:
        edited_date = st.date_input("Date", value=date.fromisoformat(document["event_date"]))
        edited_title = st.text_input("Event Title", value=document["event_title"] or "")
        edited_category = st.selectbox("Category", categories, index=categories.index(category))
    with col_right:
        edited_hospital = st.text_input("Hospital/Lab", value=document["hospital_name"] or "")
        edited_patient = st.text_input("Patient", value=document["patient_name"] or "")
        edited_amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=float(document["amount"] or 0.0),
            step=100.0,
        )

    edited_ocr_text = st.text_area("OCR / extracted text", value=document["ocr_text"] or "", height=180)
    saved = st.form_submit_button("Save changes", use_container_width=True)

if saved:
    update_document(
        Document(
            id=document["id"],
            event_date=edited_date.isoformat(),
            date_source=document["date_source"],
            event_type=edited_category,
            event_title=clean_text(edited_title),
            hospital_name=clean_text(edited_hospital),
            patient_name=clean_text(edited_patient),
            amount=edited_amount,
            thumbnail_path=document["thumbnail_path"],
            document_path=document["document_path"],
            ocr_text=edited_ocr_text,
            created_at=document["created_at"],
        )
    )
    st.success("Document updated.")
    st.page_link("app.py", label="Back to dashboard")
