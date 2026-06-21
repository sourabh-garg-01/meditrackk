from collections import defaultdict
from datetime import date
from pathlib import Path

from meditrackk_data.database import fetch_documents


def get_timeline_events():
    return fetch_documents()


def group_events_by_year_month(events):
    grouped = defaultdict(lambda: defaultdict(list))
    for event in events:
        event_date = date.fromisoformat(event["event_date"])
        grouped[event_date.year][event_date.strftime("%b")].append(event)
    return grouped


def get_document_url(document_path: str) -> str:
    return Path(document_path).as_posix()
