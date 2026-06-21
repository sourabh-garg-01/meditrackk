from pathlib import Path

import streamlit as st

from db.database import init_db
from utils.helpers import ensure_app_directories


st.set_page_config(
    page_title="Meditrackk",
    page_icon="M",
    layout="wide",
)

ensure_app_directories()
init_db()

st.title("Meditrackk")
st.caption("Local-first medical document timeline")

st.write(
    "Upload medical documents, review extracted details, and build a timeline "
    "of your healthcare journey."
)

col_upload, col_timeline = st.columns(2)

with col_upload:
    st.subheader("Upload")
    st.write("Add bills, prescriptions, reports, OPD slips, invoices, or PDFs.")
    if st.button("Go to Upload", use_container_width=True):
        st.switch_page("pages/Upload.py")

with col_timeline:
    st.subheader("Timeline")
    st.write("Review saved medical events sorted by event date.")
    if st.button("Open Timeline", use_container_width=True):
        st.switch_page("pages/Timeline.py")

st.divider()
st.markdown(
    """
    **Storage:** Everything stays local in this project folder.

    - Uploads: `uploads/`
    - Thumbnails: `thumbnails/`
    - Database: `database/meditrackk.db`
    """
)
