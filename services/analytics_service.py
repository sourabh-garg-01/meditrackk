from collections import Counter, defaultdict
from datetime import date


CONDITION_KEYWORDS = [
    "pid",
    "adenomyoma",
    "evolving fibroid",
    "nabothian cysts",
    "fibroid",
    "cyst",
    "diabetes",
    "hypertension",
    "thyroid",
    "anemia",
]


def total_spend(events) -> float:
    return sum(float(event["amount"] or 0) for event in events)


def date_range(events) -> tuple[str, str]:
    if not events:
        return "-", "-"
    dates = sorted(event["event_date"] for event in events)
    return dates[0], dates[-1]


def spend_by_category(events):
    totals = defaultdict(float)
    counts = Counter()
    for event in events:
        category = event["event_type"] or "Other"
        totals[category] += float(event["amount"] or 0)
        counts[category] += 1
    return sorted(totals.items(), key=lambda item: item[1], reverse=True), counts


def spend_by_provider(events):
    totals = defaultdict(float)
    counts = Counter()
    for event in events:
        provider = event["hospital_name"] or "Unknown provider"
        totals[provider] += float(event["amount"] or 0)
        counts[provider] += 1
    return sorted(totals.items(), key=lambda item: item[1], reverse=True), counts


def condition_counts(events):
    counts = Counter()
    for event in events:
        text = f"{event['event_title']} {event['ocr_text'] or ''}".lower()
        for condition in CONDITION_KEYWORDS:
            if condition in text:
                counts[condition.title()] += 1
    return counts


def monthly_spend(events):
    totals = defaultdict(float)
    for event in events:
        month = date.fromisoformat(event["event_date"]).strftime("%b %y")
        totals[month] += float(event["amount"] or 0)
    return dict(sorted(totals.items()))
