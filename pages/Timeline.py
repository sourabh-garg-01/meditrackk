import streamlit as st

from db.database import init_db
from utils.helpers import ensure_app_directories
from utils.ui import inject_dashboard_css


st.set_page_config(page_title="Timeline - Meditrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()
inject_dashboard_css()

st.markdown(
    """
    <div class="hero">
      <div class="brand">
        <div class="brand-icon">M</div>
        <div>
          <div class="brand-title">Timeline moved home</div>
          <div class="brand-subtitle">Timeline, overview, and trends now live in one dashboard</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_home, col_add = st.columns(2)
with col_home:
    st.page_link("app.py", label="Open dashboard")
with col_add:
    st.page_link("pages/Upload.py", label="Add document")
