from datetime import date

import streamlit as st

from db.database import init_db
from services.analytics_service import (
    condition_counts,
    date_range,
    monthly_spend,
    spend_by_category,
    spend_by_provider,
    total_spend,
)
from services.timeline_service import get_timeline_events, group_events_by_year_month
from utils.helpers import BASE_DIR, ensure_app_directories
from utils.ui import image_to_data_uri, inject_dashboard_css


st.set_page_config(page_title="MediTrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()
inject_dashboard_css()


def money(value: float | None) -> str:
    if not value:
        return "Rs. 0"
    return f"Rs. {value:,.0f}"


def type_pill(event_type: str) -> str:
    normalized = (event_type or "Other").lower()
    css_class = "pill-report" if "report" in normalized or "diagnostic" in normalized else "pill-bill"
    label = "Test Report" if "diagnostic" in normalized else event_type or "Other"
    return f'<span class="pill {css_class}">{label}</span>'


def condition_pills(text: str) -> str:
    keywords = ["pid", "adenomyoma", "evolving fibroid", "nabothian cysts"]
    pills = []
    lower_text = text.lower()
    for keyword in keywords:
        if keyword in lower_text:
            pills.append(f'<span class="pill">{keyword.title()}</span>')
    return "".join(pills)


def render_header() -> None:
    col_brand, col_action = st.columns([5, 1])
    with col_brand:
        st.markdown(
            """
            <div class="hero">
              <div class="brand">
                <div class="brand-icon">M</div>
                <div>
                  <div class="brand-title">MediTrackk</div>
                  <div class="brand-subtitle">Your medical timeline</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_action:
        if st.button("+  Add", type="primary", use_container_width=True):
            st.switch_page("pages/Upload.py")


def render_timeline(events) -> None:
    search = st.text_input("Search title, provider, condition...", label_visibility="collapsed")
    event_types = ["All types"] + sorted({event["event_type"] or "Other" for event in events})
    selected_type = st.selectbox("Event type", event_types, label_visibility="collapsed")

    filtered_events = []
    for event in events:
        haystack = f"{event['event_title']} {event['hospital_name']} {event['ocr_text']}".lower()
        matches_search = not search or search.lower() in haystack
        matches_type = selected_type == "All types" or event["event_type"] == selected_type
        if matches_search and matches_type:
            filtered_events.append(event)

    if not filtered_events:
        st.info("No timeline entries match your filters.")
        return

    grouped = group_events_by_year_month(filtered_events)
    for year in sorted(grouped):
        for month, month_events in grouped[year].items():
            st.markdown(f'<div class="timeline-month">{month.upper()} {year}</div>', unsafe_allow_html=True)
            for event in month_events:
                event_date = date.fromisoformat(event["event_date"])
                thumbnail_path = BASE_DIR / event["thumbnail_path"]
                image_uri = image_to_data_uri(thumbnail_path)
                thumb_html = (
                    f'<img class="thumb" src="{image_uri}" alt="Document thumbnail">'
                    if image_uri
                    else '<div class="thumb-placeholder">Document</div>'
                )
                pills = type_pill(event["event_type"]) + condition_pills(
                    f"{event['event_title']} {event['ocr_text'] or ''}"
                )
                st.markdown(
                    f"""
                    <div class="event-shell">
                      <div class="event-dot"></div>
                      <div class="timeline-card">
                        {thumb_html}
                        <div>
                          <div class="event-date">{event_date.strftime('%a, %d %b %Y')} {pills}</div>
                          <div class="event-title">{event['event_title']}</div>
                          <div class="event-provider">{event['hospital_name'] or 'Unknown provider'}</div>
                          <div class="event-amount">{money(event['amount'])}</div>
                        </div>
                        <div></div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Edit", key=f"edit-{event['id']}"):
                    st.session_state["edit_document_id"] = event["id"]
                    st.switch_page("pages/Edit.py")


def render_overview(events) -> None:
    first_date, last_date = date_range(events)
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-label">Total spend</div><div class="metric-value">{money(total_spend(events))}</div></div>
          <div class="metric-card"><div class="metric-label">Documents</div><div class="metric-value">{len(events)}</div></div>
          <div class="metric-card"><div class="metric-label">From</div><div class="metric-value">{first_date}</div></div>
          <div class="metric-card"><div class="metric-label">Until</div><div class="metric-value">{last_date}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    category_rows, category_counts = spend_by_category(events)
    st.markdown('<div class="panel"><div class="panel-title">By category</div>', unsafe_allow_html=True)
    for category, amount in category_rows:
        entries = category_counts[category]
        st.markdown(
            f"""
            <div class="row-item">
              <div><strong>{category}</strong><br><span class="event-provider">{entries} {'entry' if entries == 1 else 'entries'}</span></div>
              <strong>{money(amount)}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    provider_rows, provider_counts = spend_by_provider(events)
    st.markdown('<div class="panel"><div class="panel-title">Top providers</div>', unsafe_allow_html=True)
    for provider, amount in provider_rows[:5]:
        visits = provider_counts[provider]
        st.markdown(
            f"""
            <div class="row-item">
              <div><strong>{provider}</strong><br><span class="event-provider">{visits} {'visit' if visits == 1 else 'visits'}</span></div>
              <strong>{money(amount)}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_trends(events) -> None:
    conditions = condition_counts(events)
    st.markdown(
        '<div class="panel"><div class="panel-title">Conditions tracked</div>'
        '<div class="panel-subtitle">Auto-extracted from your documents.</div>',
        unsafe_allow_html=True,
    )
    if conditions:
        st.markdown(
            "".join(f'<span class="pill">{name} - {count}</span>' for name, count in conditions.items()),
            unsafe_allow_html=True,
        )
    else:
        st.caption("No condition keywords found yet.")
    st.markdown("</div>", unsafe_allow_html=True)

    monthly = monthly_spend(events)
    st.markdown(
        '<div class="panel"><div class="panel-title">Monthly spend</div>'
        '<div class="panel-subtitle">Total document amount by month.</div>',
        unsafe_allow_html=True,
    )
    if monthly:
        st.bar_chart(monthly)
    else:
        st.caption("No spending data yet.")
    st.markdown("</div>", unsafe_allow_html=True)


render_header()
events = get_timeline_events()

if not events:
    st.info("No documents yet. Click Add to upload your first medical file.")
    st.stop()

timeline_tab, overview_tab, trends_tab = st.tabs(["Timeline", "Overview", "Trends"])

with timeline_tab:
    render_timeline(events)

with overview_tab:
    render_overview(events)

with trends_tab:
    render_trends(events)
