from flask import Blueprint, jsonify
from backend.db import get_db_cursor
from backend.blockchain.notary_client import BlockchainNotary
from backend.blockchain.ledger import Ledger
from backend.config.event_types import ANCHORABLE_EVENTS
import logging

logger = logging.getLogger(__name__)

verify_blueprint = Blueprint('verify', __name__)
notary = BlockchainNotary()

@verify_blueprint.route('/verify/<domain>', methods=['GET'])
def verify_ledger(domain):
    try:
        with get_db_cursor() as cursor:
            # Check if domain exists
            cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain,))
            domain_record = cursor.fetchone()
            if not domain_record:
                return jsonify({"error": "Domain not found"}), 404

            # Fetch all events and their blockchain records
            cursor.execute("""
                SELECT 
                    e.event_hash, 
                    e.event_type, 
                    e.event_metadata,
                    e.event_timestamp,
                    b.tx_hash,
                    b.block_number
                FROM domain_events e
                LEFT JOIN blockchain_records b ON e.id = b.event_id
                WHERE e.domain_id = %s
                ORDER BY e.event_timestamp ASC
            """, (domain_record['id'],))
            events = cursor.fetchall()

        if not events:
            return jsonify({
                 "domain": domain,
                 "ledger_integrity": "VALID",
                 "hash_chain_valid": True,
                 "event_count": 0,
                 "events": []
            }), 200

        result_events = []
        is_node_ready = notary.is_ready()
        
        has_anchor_failures = False
        has_unanchored_anchorable_events = False
        
        previous_hash = "0" * 64
        hash_chain_valid = True

        for evt in events:
            event_hash = evt['event_hash']
            event_type = evt['event_type']
            event_metadata = evt['event_metadata']
            
            # 1. Hash Chain Validation
            ts_str = evt['event_timestamp'].isoformat().replace('+00:00', 'Z') if evt['event_timestamp'] else ""
            if ts_str and not ts_str.endswith('Z'):
                ts_str += 'Z'
                
            recomputed_hash = Ledger.generate_event_hash(
                domain, event_type, event_metadata, ts_str, previous_hash
            )
            
            if recomputed_hash != event_hash:
                hash_chain_valid = False
                
            previous_hash = event_hash
            
            is_anchorable = event_type in ANCHORABLE_EVENTS
            
            # DB says it's anchored if there's a tx_hash
            is_anchored_in_db = evt['tx_hash'] is not None
            
            # Verify on-chain if possible
            on_chain_verified = False
            if is_anchored_in_db and is_node_ready:
                 try:
                     hex_hash = "0x" + event_hash
                     # The contract returns a boolean mapping: anchored[hash]
                     on_chain_verified = notary.contract.functions.anchored(notary.w3.to_bytes(hexstr=hex_hash)).call()
                 except Exception as e:
                     logger.warning(f"Error querying on-chain status for {event_hash}: {e}")
                     on_chain_verified = False
            elif is_anchored_in_db and not is_node_ready:
                 # If node is offline, we can't definitively verify or mismatch. 
                 # For safety, say false.
                 on_chain_verified = False
            
            tx_explorer_url = f"http://localhost:8545/tx/{evt['tx_hash']}" if evt['tx_hash'] else None
            
            event_data = {
                "event_hash": event_hash,
                "event_type": event_type,
                "timestamp": ts_str,
                "anchored": is_anchored_in_db,
                "tx_hash": evt['tx_hash'],
                "block_number": evt['block_number'],
                "tx_explorer_url": tx_explorer_url,
                "on_chain_verified": on_chain_verified
            }
            
            result_events.append(event_data)
            
            # Integrity checks
            if is_anchored_in_db and not on_chain_verified and is_node_ready:
                has_anchor_failures = True
                
            if is_anchorable and not is_anchored_in_db:
                has_unanchored_anchorable_events = True
                
        # Determine overall integerity
        if has_anchor_failures:
            ledger_integrity = "MISMATCH"
        elif has_unanchored_anchorable_events:
            ledger_integrity = "PARTIALLY_ANCHORED"
        else:
            ledger_integrity = "VALID"
            
        return jsonify({
            "domain": domain,
            "ledger_integrity": ledger_integrity,
            "hash_chain_valid": hash_chain_valid,
            "event_count": len(result_events),
            "events": result_events
        }), 200

    except Exception as e:
        logger.exception(f"Error verifying ledger for {domain}: {e}")
        return jsonify({"error": "Internal server error during verification"}), 500
