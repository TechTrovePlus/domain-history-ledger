import logging
import json
from datetime import datetime
from backend.db import get_db_cursor
from backend.ingestion.rdap_client import RDAPClient
from backend.ingestion.rdap_normalizer import RDAPNormalizer
from backend.trust.wayback_oracle import WaybackOracle
from backend.trust.abuse_oracle import AbuseOracle
from backend.blockchain.ledger import Ledger
from backend.blockchain.integrity_hash import generate_snapshot_hash
from backend.config.event_types import (
    INITIAL_BACKGROUND_ASSESSMENT,
    HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION,
    ABUSE_HISTORY_DETECTED,
    DOMAIN_NON_EXISTENT_AT_QUERY
)

logger = logging.getLogger(__name__)

class ColdStartOrchestrator:
    """
    Executes a thorough background investigation on newly encountered domains,
    aggregating present-state RDAP with historical and intelligence oracles.
    """

    def __init__(self):
        self.rdap_client = RDAPClient()

    def process_new_domain(self, domain_name: str, active_threat: bool = False):
        """
        Orchestrates the cold start process.
        """
        logger.info(f"Initiating Cold Start intelligence routine for {domain_name}...")
        events_to_emit = []
        normalized_rdap = {"exists": False}

        try:
            logger.info(f"[{domain_name}] Starting RDAP query...")
            # 1. Authoritative Present-State (RDAP)
            try:
                with get_db_cursor() as cursor:
                    cursor.execute("""
                        SELECT s.snapshot_data, s.retrieved_at 
                        FROM domains d
                        JOIN domain_snapshots s ON d.id = s.domain_id
                        WHERE d.domain_name = %s
                        ORDER BY s.retrieved_at DESC LIMIT 1
                    """, (domain_name,))
                    latest_snap = cursor.fetchone()

                is_cached = False
                if latest_snap and latest_snap.get('retrieved_at'):
                    from datetime import timezone
                    age_hours = (datetime.now(timezone.utc) - latest_snap['retrieved_at']).total_seconds() / 3600
                    if age_hours < 24:
                        is_cached = True

                if is_cached:
                    logger.info(f"[{domain_name}] CACHE HIT: Using stored RDAP snapshot")
                    normalized_rdap = latest_snap['snapshot_data']
                    if isinstance(normalized_rdap, str):
                        normalized_rdap = json.loads(normalized_rdap)
                else:
                    logger.info(f"[{domain_name}] CACHE MISS: Performing RDAP request")
                    raw_rdap = self.rdap_client.fetch_domain_state(domain_name)
                    normalized_rdap = RDAPNormalizer.normalize(raw_rdap)
            except ValueError as e:
                logger.warning(f"[{domain_name}] Invalid domain format gracefully caught: {e}")
                normalized_rdap = {"exists": False}
            except Exception as e:
                logger.error(f"[{domain_name}] Unexpected oracle exception: {e}")
                normalized_rdap = {"exists": False}

            logger.info(f"[{domain_name}] Completed RDAP query.")

            metadata = {"rdap_baseline": normalized_rdap}

            if not normalized_rdap.get("exists"):
                metadata["reason"] = "domain_not_found_on_rdap"
                events_to_emit.append({"type": DOMAIN_NON_EXISTENT_AT_QUERY, "metadata": metadata})
            else:
                # Domain exists, proceed with deeper intelligence gathering
                creation_date_str =                 normalized_rdap.get("creation_date")
                events_to_emit.append({"type": INITIAL_BACKGROUND_ASSESSMENT, "metadata": metadata})

                # 2. Historical Continuity (Wayback Machine)
                logger.info(f"[{domain_name}] Starting Wayback oracle query...")
                earliest_snapshot = WaybackOracle.get_earliest_snapshot(domain_name)
                logger.info(f"[{domain_name}] Completed Wayback oracle query.")
                if earliest_snapshot and creation_date_str:
                    try:
                        # Convert RDAP format YYYY-MM-DDTHH:MM:SSZ
                        rdap_dt = datetime.strptime(creation_date_str, "%Y-%m-%dT%H:%M:%SZ")
                        # Convert Wayback ISO string output YYYY-MM-DDTHH:MM:SSZ
                        wayback_dt = datetime.strptime(earliest_snapshot, "%Y-%m-%dT%H:%M:%SZ")
                        
                        if wayback_dt < rdap_dt:
                            logger.warning(f"[{domain_name}] Historical discontinuity detected: content from {earliest_snapshot} predates registration {creation_date_str}.")
                            events_to_emit.append({
                                "type": HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION,
                                "metadata": {
                                    "earliest_content_timestamp": earliest_snapshot,
                                    "current_registration_timestamp": creation_date_str
                                }
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse dates for discontinuity check on {domain_name}: {e}")

                # 3. Abuse Intelligence (URLhaus)
                logger.info(f"[{domain_name}] Starting URLhaus oracle query...")
                abuse_evidence = AbuseOracle.check_domain_abuse(domain_name)
                logger.info(f"[{domain_name}] Completed URLhaus oracle query.")
                if abuse_evidence and isinstance(abuse_evidence, dict):
                    logger.warning(f"[{domain_name}] Abuse history detected via URLhaus.")
                    
                    # Append domain age context for proportional scoring
                    if creation_date_str:
                        try:
                            from datetime import timezone
                            registered_dt = datetime.fromisoformat(creation_date_str.replace("Z", "+00:00"))
                            age_days = (datetime.now(timezone.utc) - registered_dt).days
                            abuse_evidence["domain_age_years"] = age_days // 365
                        except Exception as e:
                            logger.warning(f"Could not parse creation date {creation_date_str} for domain age: {e}")
                            
                    events_to_emit.append({
                        "type": ABUSE_HISTORY_DETECTED,
                        "metadata": abuse_evidence
                    })
                elif abuse_evidence == "oracle_unavailable":
                    logger.warning(f"[{domain_name}] Abuse oracle unavailable (check API key configuration). Skipping abuse check.")

        except Exception as e:
            import traceback
            logger.error(f"[{domain_name}] Critical failure in Cold Start pipeline: {e}\n{traceback.format_exc()}")
            events_to_emit.append({
                "type": "ORCHESTRATION_FAILED",
                "metadata": {"error": str(e), "failed_at": datetime.utcnow().isoformat() + "Z"}
            })

        # DB Transaction to commit baseline and events
        try:
            with get_db_cursor(commit=True) as cursor:
                # Fetch the domain_id (usually inserted as a placeholder by search.py)
                cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain_name,))
                existing = cursor.fetchone()
                
                if existing:
                    domain_id = existing["id"]
                else:
                    # Create domain record if it somehow doesn't exist yet
                    cursor.execute(
                        "INSERT INTO domains (domain_name) VALUES (%s) RETURNING id",
                        (domain_name,)
                    )
                    domain_id = cursor.fetchone()["id"]

                # Securely hash and append the snapshot
                if normalized_rdap.get("exists"):
                    logger.info(f"[{domain_name}] Inserting RDAP snapshot into domain_snapshots...")
                    # For genesis snapshot, previous is null or '0'*64
                    prev_snap_hash = "0" * 64 
                    snap_hash = generate_snapshot_hash(normalized_rdap)
                    
                    cursor.execute(
                        """INSERT INTO domain_snapshots 
                           (domain_id, snapshot_data, snapshot_hash, previous_snapshot_hash) 
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT (snapshot_hash) DO NOTHING""",
                        (domain_id, json.dumps(normalized_rdap), snap_hash, prev_snap_hash)
                    )

                # Write ledger events
                prev_event_hash = "0" * 64
                logger.info(f"[{domain_name}] Inserting {len(events_to_emit)} events into domain_events...")
                for event in events_to_emit:
                    now = datetime.utcnow().isoformat() + "Z"
                    e_hash = Ledger.generate_event_hash(
                        domain_name, event["type"], event["metadata"], now, prev_event_hash
                    )
                    
                    cursor.execute(
                        """INSERT INTO domain_events 
                           (domain_id, event_type, event_metadata, event_hash, previous_event_hash, event_timestamp) 
                           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                        (domain_id, event["type"], json.dumps(event["metadata"]), e_hash, prev_event_hash, now)
                    )
                    prev_event_hash = e_hash

            logger.info(f"[{domain_name}] Cold Start successfully committed to ledger.")
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to commit Cold Start for {domain_name} to database: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cs = ColdStartOrchestrator()
    cs.process_new_domain("facebook.com")
