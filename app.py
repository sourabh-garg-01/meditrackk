from datetime import date
from pathlib import Path

import streamlit as st

from meditrackk_data.database import delete_document, init_db, insert_document
from meditrackk_services.analytics_service import (
    condition_counts,
    date_range,
    events_for_condition,
    monthly_spend,
    spend_by_category,
    spend_by_provider,
    total_spend,
)
from meditrackk_services.document_processor import prepare_documents_from_upload
from meditrackk_services.timeline_service import get_timeline_events, group_events_by_year_month
from meditrackk_utils.helpers import BASE_DIR, SUPPORTED_EXTENSIONS, UPLOADS_DIR, ensure_app_directories, generate_id
from meditrackk_utils.ui import image_to_data_uri, inject_dashboard_css


st.set_page_config(page_title="MediTrackk", page_icon="M", layout="wide")
ensure_app_directories()
init_db()
inject_dashboard_css()


def get_secret(name: str) -> str | None:
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def money(value: float | None) -> str:
    if not value:
        return "Rs. 0"
    return f"Rs. {value:,.0f}"


def display_provider(event) -> str:
    city = event["provider_city"] or ""
    provider = event["hospital_name"] or "Unknown provider"
    return f"{provider}, {city}" if city else provider


def set_focus(kind: str, value: str) -> None:
    st.session_state["focus_kind"] = kind
    st.session_state["focus_value"] = value


def clear_focus() -> None:
    st.session_state.pop("focus_kind", None)
    st.session_state.pop("focus_value", None)


def type_pill(event_type: str) -> str:
    normalized = (event_type or "Other").lower()
    css_class = "pill-report" if "report" in normalized or "diagnostic" in normalized else "pill-bill"
    label = "Test Report" if "diagnostic" in normalized else event_type or "Other"
    return f'<span class="pill {css_class}">{label}</span>'


def condition_pills(value: str) -> str:
    return "".join(
        f'<span class="pill">{condition.strip().title()}</span>'
        for condition in (value or "").split(",")
        if condition.strip()
    )


@st.dialog("Add medical document")
def upload_dialog() -> None:
    uploaded_file = st.file_uploader(
        "Upload image or PDF",
        type=sorted(SUPPORTED_EXTENSIONS),
        help="PDFs are split into page-level timeline candidates.",
    )
    st.caption("Gemini extraction runs when `GEMINI_API_KEY` is set in Streamlit Secrets.")

    if not uploaded_file:
        return

    if st.button("Process document", type="primary", use_container_width=True):
        file_id = generate_id()
        suffix = Path(uploaded_file.name).suffix.lower()
        saved_path = UPLOADS_DIR / f"{file_id}{suffix}"
        saved_path.write_bytes(uploaded_file.getbuffer())

        with st.spinner("Extracting timeline entries..."):
            prepared = prepare_documents_from_upload(
                saved_path,
                uploaded_file.name,
                api_key=get_secret("GEMINI_API_KEY"),
            )
        st.session_state["prepared_uploads"] = prepared

    prepared_uploads = st.session_state.get("prepared_uploads", [])
    if not prepared_uploads:
        return

    st.write(f"Found {len(prepared_uploads)} timeline candidate(s).")
    save_requested = st.button("Save candidates", type="primary", use_container_width=True)

    saved_count = 0
    skipped_count = 0
    for index, item in enumerate(prepared_uploads, start=1):
        document = item["document"]
        duplicates = item["duplicates"]
        duplicate_label = f"duplicate-{document.duplicate_key}-{index}"

        with st.expander(f"{index}. {document.event_date} - {document.event_title}", expanded=True):
            st.write(f"Provider: {document.hospital_name}")
            st.write(f"Patient: {document.patient_name}")
            st.write(f"Amount: {money(document.amount)}")
            if document.conditions:
                st.write(f"Illness/findings: {document.conditions}")
            if item.get("used_ai"):
                st.caption("Extracted with Gemini.")
            else:
                st.caption("Gemini extraction did not run successfully; fallback/manual fields were used.")
                if item.get("ai_error"):
                    with st.expander("Gemini extraction error"):
                        st.code(item["ai_error"])
                if item.get("local_ocr_error"):
                    with st.expander("Local OCR fallback error"):
                        st.code(item["local_ocr_error"])

            allow_duplicate = True
            if duplicates:
                st.warning(
                    "This already appears to exist with matching file or extracted details. "
                    "It will be skipped unless you confirm twice."
                )
                confirm_one = st.checkbox("I checked this duplicate", key=f"{duplicate_label}-one")
                confirm_two = st.checkbox("Save anyway", key=f"{duplicate_label}-two")
                allow_duplicate = confirm_one and confirm_two

            if save_requested:
                if duplicates and not allow_duplicate:
                    skipped_count += 1
                    continue
                insert_document(document)
                saved_count += 1

    if save_requested:
        st.session_state.pop("prepared_uploads", None)
        if saved_count:
            st.success(f"Saved {saved_count} entr{'y' if saved_count == 1 else 'ies'} to timeline.")
        if skipped_count:
            st.info(f"Skipped {skipped_count} duplicate entr{'y' if skipped_count == 1 else 'ies'}.")
        st.rerun()


def render_header() -> None:
    st.markdown('<div class="fixed-shell">', unsafe_allow_html=True)
    col_brand, col_action = st.columns([5, 1])
    with col_brand:
        st.markdown(
            """
            <div class="brand">
              <div class="brand-icon">M</div>
              <div>
                <div class="brand-title">MediTrackk</div>
                <div class="brand-subtitle">Your medical timeline</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_action:
        if st.button("+  Add", type="primary", use_container_width=True):
            upload_dialog()
    st.markdown("</div>", unsafe_allow_html=True)


def apply_filters(events):
    if st.session_state.get("focus_kind"):
        st.info(f"Showing {st.session_state['focus_kind']}: {st.session_state['focus_value']}")
        if st.button("Clear drill-down"):
            clear_focus()
            st.rerun()

    col_search, col_type, col_provider = st.columns([2.4, 1.1, 1.4])
    with col_search:
        search = st.text_input("Search", placeholder="Search title, provider, patient, illness...")
    with col_type:
        event_types = ["All types"] + sorted({event["event_type"] or "Other" for event in events})
        selected_type = st.selectbox("Category", event_types)
    with col_provider:
        providers = ["All providers"] + sorted({display_provider(event) for event in events})
        selected_provider = st.selectbox("Provider", providers)

    col_start, col_end, col_min, col_max = st.columns(4)
    dates = [date.fromisoformat(event["event_date"]) for event in events]
    with col_start:
        start_date = st.date_input("From", value=min(dates) if dates else date.today())
    with col_end:
        end_date = st.date_input("Until", value=max(dates) if dates else date.today())
    with col_min:
        min_amount = st.number_input("Min amount", min_value=0.0, value=0.0, step=500.0)
    with col_max:
        max_amount = st.number_input("Max amount", min_value=0.0, value=0.0, step=500.0)

    filtered = []
    for event in events:
        haystack = (
            f"{event['event_title']} {display_provider(event)} {event['patient_name']} "
            f"{event['conditions']} {event['test_results']} {event['ocr_text']}"
        ).lower()
        event_date = date.fromisoformat(event["event_date"])
        amount = float(event["amount"] or 0)
        matches = True
        matches = matches and (not search or search.lower() in haystack)
        matches = matches and (selected_type == "All types" or event["event_type"] == selected_type)
        matches = matches and (selected_provider == "All providers" or display_provider(event) == selected_provider)
        matches = matches and start_date <= event_date <= end_date
        matches = matches and amount >= min_amount
        matches = matches and (max_amount == 0 or amount <= max_amount)

        focus_kind = st.session_state.get("focus_kind")
        focus_value = st.session_state.get("focus_value")
        if focus_kind == "category":
            matches = matches and event["event_type"] == focus_value
        elif focus_kind == "provider":
            matches = matches and (event["normalized_provider"] or event["hospital_name"]) == focus_value
        elif focus_kind == "condition":
            matches = matches and event in events_for_condition(events, focus_value)

        if matches:
            filtered.append(event)
    return filtered


def render_event_card(event) -> None:
    event_date = date.fromisoformat(event["event_date"])
    thumbnail_path = BASE_DIR / event["thumbnail_path"]
    image_uri = image_to_data_uri(thumbnail_path)
    thumb_html = (
        f'<img class="thumb" src="{image_uri}" alt="Document thumbnail">'
        if image_uri
        else '<div class="thumb-placeholder">Document</div>'
    )
    pills = type_pill(event["event_type"]) + condition_pills(event["conditions"] or "")
    page_note = f"Page {event['page_number']}" if event["page_number"] else "Uploaded file"
    st.markdown(
        f"""
        <div class="event-shell">
          <div class="event-dot"></div>
          <div class="timeline-card">
            {thumb_html}
            <div>
              <div class="event-date">{event_date.strftime('%a, %d %b %Y')} {pills}</div>
              <div class="event-title">{event['event_title']}</div>
              <div class="event-provider">{display_provider(event)}</div>
              <div class="event-provider">Patient: {event['patient_name'] or 'Unknown'}</div>
              <div class="event-amount">{money(event['amount'])}</div>
              <div class="event-provider">{page_note}</div>
            </div>
            <div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_edit, col_remove = st.columns([1, 5])
    with col_edit:
        if st.button("Edit", key=f"edit-{event['id']}"):
            st.session_state["edit_document_id"] = event["id"]
            st.switch_page("pages/Edit.py")
    with col_remove:
        if st.button("Remove", key=f"remove-{event['id']}"):
            delete_document(event["id"])
            st.rerun()


def render_timeline(events) -> None:
    filtered_events = apply_filters(events)
    if not filtered_events:
        st.info("No timeline entries match your filters.")
        return

    grouped = group_events_by_year_month(filtered_events)
    for year in sorted(grouped):
        for month, month_events in grouped[year].items():
            st.markdown(f'<div class="timeline-month">{month.upper()} {year}</div>', unsafe_allow_html=True)
            for event in month_events:
                render_event_card(event)


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
        col_info, col_action = st.columns([4, 1])
        with col_info:
            st.markdown(f"**{category}**  \n{entries} entr{'y' if entries == 1 else 'ies'} - {money(amount)}")
        with col_action:
            if st.button("View", key=f"cat-{category}"):
                set_focus("category", category)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    provider_rows, provider_counts = spend_by_provider(events)
    st.markdown('<div class="panel"><div class="panel-title">Top providers</div>', unsafe_allow_html=True)
    for provider, amount in provider_rows[:8]:
        visits = provider_counts[provider]
        label = next((display_provider(event) for event in events if (event["normalized_provider"] or event["hospital_name"]) == provider), provider)
        col_info, col_action = st.columns([4, 1])
        with col_info:
            st.markdown(f"**{label}**  \n{visits} visit{'s' if visits != 1 else ''} - {money(amount)}")
        with col_action:
            if st.button("View", key=f"provider-{provider}"):
                set_focus("provider", provider)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_trends(events) -> None:
    conditions = condition_counts(events)
    st.markdown(
        '<div class="panel"><div class="panel-title">Illness and abnormal findings</div>'
        '<div class="panel-subtitle">Based on extracted diagnoses or notable test results.</div>',
        unsafe_allow_html=True,
    )
    if conditions:
        for name, count in conditions.items():
            col_info, col_action = st.columns([4, 1])
            with col_info:
                st.markdown(f"**{name}**  \n{count} linked report{'s' if count != 1 else ''}")
            with col_action:
                if st.button("Reports", key=f"condition-{name}"):
                    set_focus("condition", name)
                    st.rerun()
    else:
        st.caption("No abnormal findings or illness labels extracted yet.")
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
