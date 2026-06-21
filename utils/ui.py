import base64
from pathlib import Path

import streamlit as st


def inject_dashboard_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 38%);
        }
        .main .block-container {
            max-width: 980px;
            padding-top: 1.25rem;
        }
        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92);
            border-bottom: 1px solid #dce5ef;
        }
        [data-testid="stSidebar"] {
            display: none;
        }
        .hero {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.35rem 0 1.2rem;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }
        .brand-icon {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            display: grid;
            place-items: center;
            background: #0b8edb;
            color: white;
            font-size: 22px;
            font-weight: 800;
        }
        .brand-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #101827;
            line-height: 1.1;
        }
        .brand-subtitle {
            color: #64748b;
            font-size: 0.92rem;
            margin-top: 0.15rem;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: #0f172a;
            color: #ffffff;
            border: 0;
            border-radius: 8px;
            min-height: 2.8rem;
            font-weight: 800;
            box-shadow: none;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin-bottom: 1rem;
        }
        .metric-card, .panel, .timeline-card {
            background: #ffffff;
            border: 1px solid #dbe5ef;
            border-radius: 13px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.10);
        }
        .metric-card {
            padding: 0.9rem;
        }
        .metric-label {
            color: #496581;
            font-size: 0.82rem;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            color: #020617;
            font-weight: 800;
            font-size: 1.08rem;
        }
        .panel {
            padding: 1rem;
            margin: 1rem 0;
        }
        .panel-title {
            font-weight: 800;
            color: #020617;
            margin-bottom: 0.2rem;
        }
        .panel-subtitle {
            color: #496581;
            font-size: 0.84rem;
            margin-bottom: 0.8rem;
        }
        .timeline-month {
            color: #496581;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin: 1rem 0 0.5rem;
        }
        .event-shell {
            display: grid;
            grid-template-columns: 18px 1fr;
            gap: 0.8rem;
            margin-bottom: 0.75rem;
        }
        .event-dot {
            width: 13px;
            height: 13px;
            background: #0b8edb;
            border-radius: 999px;
            margin-top: 1.55rem;
            box-shadow: 0 0 0 4px #e5f4ff;
        }
        .timeline-card {
            display: grid;
            grid-template-columns: 98px 1fr auto;
            gap: 0.95rem;
            padding: 0.9rem;
            align-items: center;
        }
        .thumb {
            width: 86px;
            height: 86px;
            object-fit: cover;
            border-radius: 8px;
            border: 1px solid #dbe5ef;
            background: #f8fafc;
        }
        .thumb-placeholder {
            width: 86px;
            height: 86px;
            border-radius: 8px;
            border: 1px dashed #cbd5e1;
            display: grid;
            place-items: center;
            color: #64748b;
            font-size: 0.78rem;
            background: #f8fafc;
        }
        .event-date {
            font-size: 0.84rem;
            font-weight: 800;
            color: #020617;
        }
        .event-title {
            font-size: 0.96rem;
            font-weight: 800;
            color: #020617;
            margin: 0.3rem 0 0.1rem;
        }
        .event-provider {
            color: #496581;
            font-size: 0.86rem;
        }
        .event-amount {
            color: #0369a1;
            font-weight: 800;
            margin-top: 0.35rem;
        }
        .pill {
            display: inline-block;
            border-radius: 999px;
            background: #eef4fb;
            color: #34516e;
            font-size: 0.76rem;
            font-weight: 700;
            padding: 0.22rem 0.55rem;
            margin-right: 0.3rem;
        }
        .pill-bill {
            background: #fff3c4;
            color: #a35400;
        }
        .pill-report {
            background: #ebe5ff;
            color: #5b21b6;
        }
        .row-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.75rem;
            border: 1px solid #dbe5ef;
            border-radius: 9px;
            margin-top: 0.55rem;
        }
        @media (max-width: 760px) {
            .metric-grid, .timeline-card {
                grid-template-columns: 1fr;
            }
            .hero {
                align-items: flex-start;
                flex-direction: column;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def image_to_data_uri(path: Path) -> str | None:
    if not path.exists() or path.suffix.lower() == ".pdf":
        return None
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
