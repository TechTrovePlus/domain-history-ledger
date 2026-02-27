# backend/api/timeline.py

import sqlite3

DB_PATH = "backend/dns_guard.db"


def get_domain_timeline(domain: str) -> dict:
    """
    Return full event timeline for a domain.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch domain
    cursor.execute(
        "SELECT id FROM domains WHERE domain_name = ?",
        (domain,)
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return {
            "domain": domain,
            "events": [],
            "message": "Domain not found in DNS Guard database."
        }

    domain_id = row[0]

    # Fetch timeline
    cursor.execute(
        """
        SELECT event_type, event_time, description, integrity_hash, blockchain_tx
        FROM domain_events
        WHERE domain_id = ?
        ORDER BY event_time ASC
        """,
        (domain_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    timeline = []

    for event_type, event_time, description, integrity_hash, blockchain_tx in rows:
        timeline.append({
            "event_type": event_type,
            "date": event_time,
            "description": description,
            "blockchain_proof": (
                {
                    "integrity_hash": integrity_hash,
                    "transaction": blockchain_tx
                }
                if integrity_hash and blockchain_tx
                else None
            )
        })

    return {
        "domain": domain,
        "events": timeline
    }
