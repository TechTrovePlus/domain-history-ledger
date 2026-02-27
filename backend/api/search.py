# backend/api/search.py

import sqlite3

from backend.trust.status_engine import evaluate_status
from backend.trust.reason_engine import evaluate_reason

DB_PATH = "backend/dns_guard.db"


def search_domain(domain: str) -> dict:
    """
    Search domain reputation and return current status, reason, and proof.
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
            "status": "UNKNOWN",
            "reason_code": None,
            "reason": "Domain not found in DNS Guard database.",
            "blockchain_proof": None
        }

    domain_id = row[0]

    # Fetch full event history (chronological)
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

    # Normalize events for trust engines
    events = []
    blockchain_proof = None

    for event_type, event_time, description, integrity_hash, blockchain_tx in rows:
        events.append({
            "event_type": event_type,
            "event_time": event_time,
            "description": description
        })

        # Capture proof if exists
        if integrity_hash and blockchain_tx:
            blockchain_proof = {
                "integrity_hash": integrity_hash,
                "transaction": blockchain_tx
            }

    # Evaluate trust
    status = evaluate_status(events)
    reason_code, reason_text = evaluate_reason(events, status)

    return {
        "domain": domain,
        "status": status,
        "reason_code": reason_code,
        "reason": reason_text,
        "blockchain_proof": blockchain_proof
    }
