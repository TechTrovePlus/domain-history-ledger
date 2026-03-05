import logging
from backend.db import get_db_cursor

logger = logging.getLogger(__name__)

def get_domain_timeline(domain: str) -> dict:
    """
    Return full verifiable event timeline for a domain from the PostgreSQL ledger.
    """
    
    try:
        with get_db_cursor() as cursor:
            # 1. Ensure domain exists
            cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "domain": domain,
                    "events": [],
                    "message": "Domain not found in DNS Guard database."
                }
                
            domain_id = row["id"]
            
            # 2. Fetch full chronological timeline with blockchain proofs
            cursor.execute(
                """
                SELECT e.event_type, e.event_timestamp AT TIME ZONE 'UTC' as event_time, 
                       e.event_metadata, e.event_hash, 
                       b.tx_hash, b.block_number, b.anchored_at AT TIME ZONE 'UTC' as anchored_at
                FROM domain_events e
                LEFT JOIN blockchain_records b ON e.id = b.event_id
                WHERE e.domain_id = %s
                ORDER BY e.event_timestamp ASC
                """,
                (domain_id,)
            )
            rows = cursor.fetchall()

    except Exception as e:
        logger.error(f"Database error during timeline fetch: {e}")
        return {"error": "Internal database connection error", "status": 500}

    timeline = []
    for r in rows:
        event_dict = {
            "event_type": r["event_type"],
            "date": r["event_time"].isoformat() + "Z" if r["event_time"] else None,
            "event_hash": r["event_hash"],
            "metadata": r["event_metadata"]
        }
        
        # Attach proof if event was cleanly anchored
        if r["tx_hash"]:
            event_dict["blockchain_proof"] = {
                "transaction_hash": r["tx_hash"],
                "block_number": r["block_number"],
                "anchored_at": r["anchored_at"].isoformat() + "Z" if r["anchored_at"] else None
            }
        else:
            event_dict["blockchain_proof"] = None
            
        timeline.append(event_dict)

    return {
        "domain": domain,
        "events": timeline,
        "total_events": len(timeline)
    }
