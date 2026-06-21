from collections import Counter, defaultdict
from datetime import date


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
        provider = event["normalized_provider"] or event["hospital_name"] or "Unknown provider"
        totals[provider] += float(event["amount"] or 0)
        counts[provider] += 1
    return sorted(totals.items(), key=lambda item: item[1], reverse=True), counts


def condition_counts(events):
    counts = Counter()
    for event in events:
        for condition in _split_csv(event["conditions"] or ""):
            counts[condition] += 1
    return counts


def events_for_condition(events, condition: str):
    condition_lower = condition.lower()
    return [
        event
        for event in events
        if condition_lower in [item.lower() for item in _split_csv(event["conditions"] or "")]
    ]


def monthly_spend(events):
    totals = defaultdict(float)
    for event in events:
        month = date.fromisoformat(event["event_date"]).strftime("%b %y")
        totals[month] += float(event["amount"] or 0)
    return dict(sorted(totals.items()))


def _split_csv(value: str) -> list[str]:
    return [item.strip().title() for item in value.split(",") if item.strip()]
