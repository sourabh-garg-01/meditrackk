from datetime import date
from pathlib import Path

import streamlit as st

from db.database import init_db
from services.timeline_service import get_timeline_events, group_events_by_year_month
from utils.helpers import BASE_DIR, ensure_app_directories, format_amount


st.set_page_config(page_title="Timeline - Meditrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()

st.title("Medical Timeline")

events = get_timeline_events()

if not events:
    st.info("No documents have been saved yet.")
    st.page_link("pages/Upload.py", label="Upload your first document")
    st.stop()

grouped_events = group_events_by_year_month(events)

for year in sorted(grouped_events):
    st.header(str(year))
    for month, month_events in grouped_events[year].items():
        st.subheader(month)
        for event in month_events:
            event_date = date.fromisoformat(event["event_date"])
            with st.container(border=True):
                col_meta, col_thumb = st.columns([3, 1])
                with col_meta:
                    st.markdown(f"**{event['event_title']}**")
                    st.write(event_date.strftime("%a, %d %b %Y"))
                    st.write(event["hospital_name"] or "Unknown hospital/lab")
                    st.write(f"Patient: {event['patient_name'] or 'Unknown'}")
                    st.write(format_amount(event["amount"]))
                    if event["date_source"] == "upload":
                        st.caption("Date Source: Upload Date")

                with col_thumb:
                    thumbnail_path = BASE_DIR / event["thumbnail_path"]
                    document_path = BASE_DIR / event["document_path"]
                    if thumbnail_path.exists() and thumbnail_path.suffix.lower() != ".pdf":
                        st.image(str(thumbnail_path), use_container_width=True)
                    else:
                        st.write("Document")
                    if document_path.exists():
                        with document_path.open("rb") as file_handle:
                            st.download_button(
                                "Open original",
                                data=file_handle,
                                file_name=document_path.name,
                                mime="application/octet-stream",
                                use_container_width=True,
                            )
