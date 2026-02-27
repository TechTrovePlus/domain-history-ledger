# backend/ingestion/ingest_wave_2.py

import json
import sqlite3

from backend.config.event_types import ABUSE_FLAG
from backend.config.demo_domains import DEMO_DOMAIN_SET
from backend.blockchain.notary_client import BlockchainNotary

DB_PATH = "backend/dns_guard.db"
WAVE_FILE = "backend/data/abuse_feed_1.json"


def ingest_wave_2():
    with open(WAVE_FILE, "r") as f:
        records = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔗 Initialize blockchain notary ONCE
    notary = BlockchainNotary()

    for record in records:
        domain = record["domain"]
        event_type = record["event"]
        event_date = record["date"]
        desc = record["desc"]

        # # Safety checks
        # if domain not in DEMO_DOMAIN_SET:
        #     raise ValueError(f"Unknown demo domain: {domain}")

        if event_type != ABUSE_FLAG:
            raise ValueError("Wave 2 may contain ABUSE_FLAG events only")

        # Fetch domain_id (must already exist from Wave 1)
        cursor.execute(
            "SELECT id FROM domains WHERE domain_name = ?",
            (domain,)
        )
        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(f"Domain not found for abuse event: {domain}")

        domain_id = row[0]

        # 🔐 Anchor abuse event on blockchain (selective)
        integrity_hash, tx_hash = notary.anchor_event(
            domain,
            event_type,
            event_date
        )

        # Append-only insert WITH blockchain proof
        cursor.execute(
            """
            INSERT INTO domain_events (
                domain_id,
                event_type,
                event_time,
                description,
                integrity_hash,
                blockchain_tx
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                domain_id,
                event_type,
                event_date,
                desc,
                integrity_hash,
                tx_hash
            )
        )

    conn.commit()
    conn.close()

    print("[Wave 2] Historic abuse ingested and anchored successfully.")


if __name__ == "__main__":
    ingest_wave_2()
