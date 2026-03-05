import logging
import time
from backend.db import get_db_cursor
from backend.blockchain.notary_client import BlockchainNotary
from backend.config.event_types import ANCHORABLE_EVENTS
from backend.config import settings

logger = logging.getLogger(__name__)

class AnchoringQueue:
    """
    Asynchronous queue worker that polls for unanchored events and anchors 
    them to the blockchain. Continues gracefully if the blockchain is offline.
    """

    def __init__(self):
        self.notary = BlockchainNotary()

    def process_queue(self):
        """Process all pending unanchored events."""
        if not self.notary.is_ready():
            logger.error("Blockchain node is offline. Queue processing suspended.")
            return

        try:
            with get_db_cursor(commit=True) as cursor:
                # Find events that are anchorable but have no blockchain_record
                cursor.execute("""
                    SELECT e.id, e.event_hash, e.event_type, d.domain_name 
                    FROM domain_events e
                    JOIN domains d ON e.domain_id = d.id
                    LEFT JOIN blockchain_records b ON e.id = b.event_id
                    WHERE b.id IS NULL
                    ORDER BY e.event_timestamp ASC
                    LIMIT 50
                """)
                unanchored_events = cursor.fetchall()
                
                count = 0
                for evt in unanchored_events:
                    domain = evt["domain_name"]
                    evt_type = evt["event_type"]
                    evt_hash = evt["event_hash"]
                    evt_id = evt["id"]

                    if evt_type in ANCHORABLE_EVENTS:
                        try:
                            logger.info(f"Anchoring event {evt_hash} for {domain}...")
                            tx_hash, block_num = self.notary.anchor_event(evt_hash, evt_type)
                            
                            # Insert blockchain record
                            cursor.execute("""
                                INSERT INTO blockchain_records (event_id, tx_hash, block_number)
                                VALUES (%s, %s, %s)
                            """, (evt_id, tx_hash, block_num))
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to anchor event {evt_id}: {e}")
                            # Stop processing batch on continuous failure
                            break

                if count > 0:
                    logger.info(f"Successfully anchored {count} events.")
                else:
                    logger.debug("No anchorable events found in queue.")
                    
        except Exception as e:
            logger.error(f"Queue processing error: {e}")

    def run(self):
        """Worker loop that runs continuously, polling for events."""
        logger.info(f"Starting AnchoringQueue Worker. Polling every {settings.ANCHOR_POLL_INTERVAL} seconds.")
        while True:
            try:
                self.process_queue()
            except Exception as e:
                logger.error(f"Unhandled exception in worker loop: {e}")
            
            logger.debug(f"Sleeping for {settings.ANCHOR_POLL_INTERVAL} seconds...")
            time.sleep(settings.ANCHOR_POLL_INTERVAL)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    queue = AnchoringQueue()
    queue.run()
