import hashlib
import json
from datetime import datetime

class Ledger:
    """
    Core integrity engine for the append-only cryptographic ledger.
    """

    @staticmethod
    def generate_snapshot_hash(domain: str, snapshot_data: dict, previous_hash: str) -> str:
        """
        Generates a SHA-256 hash for an RDAP snapshot.
        """
        payload = {
            "domain": domain,
            "data": snapshot_data,
            "previous_hash": previous_hash
        }
        json_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_event_hash(
        domain: str, 
        event_type: str, 
        event_metadata: dict, 
        timestamp: str, 
        previous_event_hash: str
    ) -> str:
        """
        Generates the chain hash for a specific lifecycle or intelligence event.
        Implementation of the specification rule:
        event_hash = SHA256(domain + event_type + timestamp + previous_event_hash + metadata)
        """
        payload = {
            "domain": domain,
            "event_type": event_type,
            "timestamp": timestamp,
            "previous_event_hash": previous_event_hash,
            "metadata": event_metadata
        }
        json_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
