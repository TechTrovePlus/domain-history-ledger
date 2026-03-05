import hashlib
import json

def generate_snapshot_hash(snapshot: dict) -> str:
    """
    Generates a deterministic SHA256 integrity hash from an RDAP snapshot dictionary.
    Ensures identical snapshots always produce identical hashes.
    """
    json_str = json.dumps(snapshot, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
