import logging
import threading
import json
import re
from urllib.parse import urlparse
import tldextract
from datetime import datetime, timezone
from dateutil.parser import parse
from backend.db import get_db_cursor
from backend.trust.trust_engine import TrustEngine
from backend.ingestion.cold_start import ColdStartOrchestrator
from backend.blockchain.ledger import Ledger
from backend.config.event_types import ORCHESTRATION_FAILED

logger = logging.getLogger(__name__)

def run_cold_start_background(target_domain):
    try:
        orchestrator = ColdStartOrchestrator()
        orchestrator.process_new_domain(target_domain)
    except Exception as e:
        import traceback
        logger.error(f"Background Cold Start Thread failed for {target_domain}: {e}")
        logger.error(traceback.format_exc())
        
        # Last-resort parachute in case orchestrator crashes completely
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (target_domain,))
                row = cursor.fetchone()
                if row:
                    domain_id = row["id"]
                    now = datetime.utcnow().isoformat() + "Z"
                    metadata = {"error": "Critical thread crash: " + str(e), "failed_at": now}
                    
                    e_hash = Ledger.generate_event_hash(
                        target_domain, ORCHESTRATION_FAILED, metadata, now, "0"*64
                    )
                    
                    cursor.execute(
                        """INSERT INTO domain_events 
                           (domain_id, event_type, event_metadata, event_hash, previous_event_hash, event_timestamp) 
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (domain_id, ORCHESTRATION_FAILED, json.dumps(metadata), e_hash, "0"*64, now)
                    )
                    logger.info(f"[{target_domain}] Last-resort ORCHESTRATION_FAILED event written successfully.")
        except Exception as db_e:
            logger.error(f"[{target_domain}] FATAL: Could not write last-resort event. {db_e}")

def normalize_domain(raw_input: str) -> str:
    """
    Normalizes raw user input into a clean registrable domain.
    Strips schemes, paths, ports, and reduces subdomains to the base domain
    using the rigorous tldextract library.
    """
    if not raw_input:
        return ""
        
    raw_input = str(raw_input).strip().lower()
    
    # Use tldextract to reliably determine the registrable domain
    ext = tldextract.extract(raw_input)
    
    # Reconstruct the normalized domain
    # If there's no domain (e.g. just an IP or invalid string), it falls back safely.
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
        
    return raw_input

def search_domain(domain: str) -> dict:
    """
    Search domain reputation. If missing, triggers a Cold Start intelligence gathering 
    routine synchronously before returning the new ledger state.
    """
    # 0. Normalize the domain input
    domain = normalize_domain(domain)
    
    if not domain or '.' not in domain:
        return {"error": "Invalid domain format", "status": 400}
    
    # 1. Ensure domain exists, Cold Start if not
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, first_seen, active_trust_score FROM domains WHERE domain_name = %s", (domain,))
            row = cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error during search: {e}")
        return {"error": "Internal database connection error", "status": 500}

    if not row:
        logger.info(f"[{domain}] Not found in DB. Triggering asynchronous Cold Start Orchestrator...")
        
        # 1. Immediately insert minimal placeholder to lock the domain and prevent duplicate schedules
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    "INSERT INTO domains (domain_name) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id",
                    (domain,)
                )
                inserted = cursor.fetchone()
                
        except Exception as e:
            logger.error(f"Database error during placeholder insert: {e}")
            return {"error": "Internal database connection error", "status": 500}
            
        # 2. Push domain into asynchronous background queue (lightweight worker thread)

        # Only start a new thread if we actually inserted the placeholder (idempotent scheduling)
        # If it was already there (another request hit exactly at the same time), we just return SCAN_QUEUED
        if inserted:
            worker = threading.Thread(target=run_cold_start_background, args=(domain,), daemon=True)
            worker.start()

        # 3. Return HTTP 202 Accepted payload
        return {
            "status": "SCAN_QUEUED",
            "domain": domain,
            "message": "Cold Start intelligence routine has been scheduled."
        }
    
    # Check if the domain is still being processed by the worker (no events yet)
    domain_id = row["id"]
    
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM domain_events WHERE domain_id = %s", (domain_id,))
        event_count = cursor.fetchone()["cnt"]
        
    if event_count == 0:
        # Check if the placeholder is stale
        first_seen = row["first_seen"]
        
        if isinstance(first_seen, str):
            first_seen_dt = parse(first_seen)
            if first_seen_dt.tzinfo is None:
                first_seen_dt = first_seen_dt.replace(tzinfo=timezone.utc)
        else:
            first_seen_dt = first_seen
            if first_seen_dt.tzinfo is None:
                first_seen_dt = first_seen_dt.replace(tzinfo=timezone.utc)

        age_seconds = (datetime.now(timezone.utc) - first_seen_dt).total_seconds()
        
        if age_seconds > 120:
            logger.warning(f"[{domain}] found stuck in SCAN_QUEUED for {age_seconds}s. Respawning Cold Start thread.")
            worker = threading.Thread(target=run_cold_start_background, args=(domain,), daemon=True)
            worker.start()
            
            # Immediately update first_seen so we don't spam threads while we wait
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("UPDATE domains SET first_seen = NOW() WHERE id = %s", (domain_id,))
                
            return {
                "status": "SCAN_QUEUED",
                "domain": domain,
                "message": "Cold Start stalled previously. Routine has been restarted."
            }

        return {
            "status": "SCAN_QUEUED",
            "domain": domain,
            "message": "Cold Start intelligence routine has been scheduled and is currently running."
        }

    # 2. Fetch full event history for scoring Engine
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT e.event_type, e.event_timestamp AT TIME ZONE 'UTC' as event_time, e.event_metadata, 
                   e.event_hash, b.tx_hash, b.block_number
            FROM domain_events e
            LEFT JOIN blockchain_records b ON e.id = b.event_id
            WHERE e.domain_id = %s
            ORDER BY e.event_timestamp ASC
            """,
            (domain_id,)
        )
        rows = cursor.fetchall()
        
    events = []
    blockchain_proofs_count = 0
    domain_exists = True
    
    for r in rows:
        events.append(dict(r))
        if r["tx_hash"]:
            blockchain_proofs_count += 1
        if r["event_type"] == "DOMAIN_NON_EXISTENT_AT_QUERY":
            domain_exists = False

    # 3. Compute dynamic trust score
    trust_evaluation = TrustEngine.calculate_score(events)

    return {
        "domain": domain,
        "domain_exists": domain_exists,
        "status": "UNKNOWN" if not domain_exists else ("TRUSTED" if trust_evaluation["is_trusted"] else "UNTRUSTED"),
        "is_trusted": trust_evaluation["is_trusted"],
        "final_score": "N/A" if not domain_exists else trust_evaluation["final_score"],
        "penalties": [] if not domain_exists else trust_evaluation["penalties"],
        "event_count": len(events),
        "anchored_proofs": blockchain_proofs_count
    }
