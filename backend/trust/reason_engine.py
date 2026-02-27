# backend/trust/reason_engine.py

from datetime import datetime

from backend.config.event_types import ABUSE_FLAG, OWNERSHIP_CHANGED


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def evaluate_reason(events: list[dict], status: str) -> tuple[str, str]:
    """
    Returns (reason_code, reason_text)
    Events must be ordered chronologically.
    """

    now = max(parse_date(e["event_time"]) for e in events)

    # 🔴 RED
    if status == "RED":
        return (
            "R1_ABUSE_HISTORY",
            "This domain has a verified history of abuse."
        )

    # 🟡 YELLOW
    if status == "YELLOW":
        first_seen = parse_date(events[0]["event_time"])
        if (now - first_seen).days <= 30:
            return (
                "Y1_NEW_DOMAIN",
                "This domain is newly registered and may not yet be trustworthy."
            )

        for e in events:
            if e["event_type"] == OWNERSHIP_CHANGED:
                if (now - parse_date(e["event_time"])).days <= 90:
                    return (
                        "Y2_RECENT_OWNER_CHANGE",
                        "This domain recently changed ownership, which reduces trust temporarily."
                    )

        for e in events:
            if e["description"].startswith("RE_REGISTERED"):
                if (now - parse_date(e["event_time"])).days <= 180:
                    return (
                        "Y3_REREGISTERED_DOMAIN",
                        "This domain was re-registered recently, which can be risky."
                    )

    # 🟢 GREEN
    return (
        "G1_CLEAN_HISTORY",
        "No abuse or suspicious lifecycle events were detected."
    )
