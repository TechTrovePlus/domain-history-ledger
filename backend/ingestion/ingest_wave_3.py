# backend/ingestion/ingest_wave_3.py

import json
import sqlite3

from backend.config.event_types import (
    OWNERSHIP_CHANGED,
    EXPIRED,
    RE_REGISTERED,
)
from backend.config.demo_domains import DEMO_DOMAIN_SET

DB_PATH = "backend/dns_guard.db"
WAVE_FILE = "backend/data/registrar_feed_2.json"


# Allowed V2 lifecycle events (feed-level validation)
ALLOWED_EVENTS = {
    OWNERSHIP_CHANGED,
    EXPIRED,
    RE_REGISTERED,
}


def ingest_wave_3():
    with open(WAVE_FILE, "r") as f:
        records = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for record in records:
        domain = record["domain"]
        event_type = record["event"]
        event_date = record["date"]
        desc = record["desc"]

        # # Safety checks
        # if domain not in DEMO_DOMAIN_SET:
        #     raise ValueError(f"Unknown demo domain: {domain}")

        if event_type not in ALLOWED_EVENTS:
            raise ValueError(f"Invalid event type for Wave 3: {event_type}")

        # Domain must already exist (from Wave 1)
        cursor.execute(
            "SELECT id FROM domains WHERE domain_name = ?",
            (domain,)
        )
        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(f"Domain not found for lifecycle event: {domain}")

        domain_id = row[0]

        # --- V2 → V1 EVENT TYPE MAPPING ---
        # V1 schema only allows:
        # REGISTERED, OWNERSHIP_CHANGED, ABUSE_FLAG
        if event_type in (EXPIRED, RE_REGISTERED):
            db_event_type = "REGISTERED"
            db_description = f"{event_type}: {desc}"
        else:
            db_event_type = event_type
            db_description = desc

        # Append-only insert (V1-compatible)
        cursor.execute(
            """
            INSERT INTO domain_events (
                domain_id,
                event_type,
                event_time,
                description
            ) VALUES (?, ?, ?, ?)
            """,
            (
                domain_id,
                db_event_type,
                event_date,
                db_description
            )
        )

    conn.commit()
    conn.close()

    print("[Wave 3] Lifecycle and ownership events ingested successfully.")


if __name__ == "__main__":
    ingest_wave_3()
