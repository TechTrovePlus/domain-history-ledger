import os
import time
import json
import logging
from datetime import datetime, timezone
from backend.db import get_db_cursor
from backend.config import settings
from backend.ingestion.rdap_client import RDAPClient
from backend.ingestion.rdap_normalizer import RDAPNormalizer
from backend.ingestion.diff_engine import DiffEngine
from backend.blockchain.ledger import Ledger
from backend.blockchain.integrity_hash import generate_snapshot_hash

logger = logging.getLogger(__name__)

class DiffMonitor:
    def __init__(self):
        self.rdap_client = RDAPClient()

    def run_cycle(self):
        try:
            with get_db_cursor() as cursor:
                # Select monitored domains (could order by oldest retrieved_at in the future)
                cursor.execute("""
                    SELECT id, domain_name 
                    FROM domains 
                    WHERE monitored = TRUE
                    LIMIT %s
                """, (settings.DIFF_BATCH_SIZE,))
                domains = cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch domains for monitoring: {e}")
            return

        for dom in domains:
            domain_id = dom['id']
            domain_name = dom['domain_name']

            try:
                # 1. Load latest snapshot
                with get_db_cursor() as cursor:
                    cursor.execute("""
                        SELECT snapshot_data, snapshot_hash, retrieved_at
                        FROM domain_snapshots 
                        WHERE domain_id = %s 
                        ORDER BY id DESC LIMIT 1
                    """, (domain_id,))
                    latest_snap = cursor.fetchone()
                
                old_snapshot_data = latest_snap['snapshot_data'] if latest_snap else None
                prev_snap_hash = latest_snap['snapshot_hash'] if latest_snap else "0" * 64
                
                if old_snapshot_data and isinstance(old_snapshot_data, str):
                    old_snapshot_data = json.loads(old_snapshot_data)

                # 2. Fetch new RDAP snapshot
                try:
                    is_cached = False
                    if latest_snap and latest_snap.get('retrieved_at'):
                        age_hours = (datetime.now(timezone.utc) - latest_snap['retrieved_at']).total_seconds() / 3600
                        if age_hours < 24:
                            is_cached = True

                    if is_cached:
                        logger.info(f"[{domain_name}] CACHE HIT: Using stored RDAP snapshot")
                        new_snapshot_data = old_snapshot_data
                    else:
                        logger.info(f"[{domain_name}] CACHE MISS: Performing RDAP request")
                        raw_rdap = self.rdap_client.fetch_domain_state(domain_name)
                        new_snapshot_data = RDAPNormalizer.normalize(raw_rdap)
                except ValueError as e:
                    logger.warning(f"[{domain_name}] Invalid domain format gracefully caught: {e}")
                    new_snapshot_data = {"exists": False}
                except Exception as e:
                    logger.error(f"[{domain_name}] RDAP fetch error: {e}")
                    continue

                if not new_snapshot_data:
                    logger.warning(f"[{domain_name}] RDAP snapshot missing – skipping diff.")
                    continue

                snap_hash = generate_snapshot_hash(new_snapshot_data)

                # 3. Hash Check & DiffEngine comparison
                if prev_snap_hash != "0" * 64 and snap_hash == prev_snap_hash:
                    has_changed_snapshot = False
                    events = []
                else:
                    has_changed_snapshot = True
                    events = DiffEngine.compare(old_snapshot_data, new_snapshot_data)

                with get_db_cursor(commit=True) as cursor:
                    if has_changed_snapshot:
                        cursor.execute("""
                            INSERT INTO domain_snapshots 
                            (domain_id, snapshot_data, snapshot_hash, previous_snapshot_hash) 
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (snapshot_hash) DO NOTHING
                        """, (domain_id, json.dumps(new_snapshot_data), snap_hash, prev_snap_hash))

                    # 4. Process events
                    for event in events:
                        # Find the previous event hash
                        cursor.execute("""
                            SELECT event_hash 
                            FROM domain_events 
                            WHERE domain_id = %s 
                            ORDER BY id DESC LIMIT 1
                        """, (domain_id,))
                        prev_evt = cursor.fetchone()
                        prev_event_hash = prev_evt['event_hash'] if prev_evt else "0" * 64

                        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        
                        e_hash = Ledger.generate_event_hash(
                            domain_name, event["type"], event["metadata"], now, prev_event_hash
                        )

                        cursor.execute("""
                            INSERT INTO domain_events 
                            (domain_id, event_type, event_metadata, event_hash, previous_event_hash, event_timestamp) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (domain_id, event["type"], json.dumps(event["metadata"]), e_hash, prev_event_hash, now))
                        
                        logger.info(f"[{domain_name}] Emitted lifecycle event: {event['type']}")
            
            except Exception as e:
                logger.error(f"[{domain_name}] Error during diff monitor cycle: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
            
            time.sleep(settings.RDAP_REQUEST_DELAY)

    def run(self):
        logger.info(f"Starting Diff Monitor. Polling every {settings.DIFF_POLL_INTERVAL} seconds.")
        while True:
            self.run_cycle()
            logger.debug(f"Diff Monitor cycle complete. Sleeping {settings.DIFF_POLL_INTERVAL}s.")
            time.sleep(settings.DIFF_POLL_INTERVAL)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    monitor = DiffMonitor()
    monitor.run()
