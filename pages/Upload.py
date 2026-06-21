import streamlit as st

from meditrackk_data.database import init_db
from meditrackk_utils.helpers import ensure_app_directories
from meditrackk_utils.ui import inject_dashboard_css


st.set_page_config(page_title="Upload - Meditrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()
inject_dashboard_css()

st.markdown(
    """
    <div class="hero">
      <div class="brand">
        <div class="brand-icon">M</div>
        <div>
          <div class="brand-title">Upload moved home</div>
          <div class="brand-subtitle">Use the Add button on the dashboard to upload in a pop-up window.</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.page_link("app.py", label="Open dashboard")
