# backend/ingestion/ingest_wave_1.py

import json
import sqlite3
from pathlib import Path

from backend.config.event_types import REGISTERED
from backend.config.demo_domains import DEMO_DOMAIN_SET

DB_PATH = "backend/dns_guard.db"
WAVE_FILE = "backend/data/registrar_feed_1.json"


def ingest_wave_1():
    with open(WAVE_FILE, "r") as f:
        records = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for record in records:
        domain = record["domain"]
        event_type = record["event"]
        event_date = record["date"]
        source = record["source"]

        # Safety checks
        # if domain not in DEMO_DOMAIN_SET:
        #     raise ValueError(f"Unknown demo domain: {domain}")

        if event_type != REGISTERED:
            raise ValueError("Wave 1 may contain REGISTERED events only")

        # Insert domain if not exists
        cursor.execute(
            """
            INSERT OR IGNORE INTO domains (domain_name, first_seen, current_status)
            VALUES (?, ?, ?)
            """,
            (domain, event_date, "UNKNOWN")
        )

        # Get domain_id
        cursor.execute(
        "SELECT id FROM domains WHERE domain_name = ?",
        (domain,)
        )
        row = cursor.fetchone()

        if row is None:
             raise RuntimeError(f"Failed to fetch domain_id for {domain}")

        domain_id = row[0]

        # Insert event (append-only)
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
                event_type,
                event_date,
                "Domain registered",
            )
        )

    conn.commit()
    conn.close()

    print("[Wave 1] Registrar feed ingested successfully.")


if __name__ == "__main__":
    ingest_wave_1()
