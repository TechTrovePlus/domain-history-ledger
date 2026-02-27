# backend/blockchain/integrity_hash.py

from eth_utils import keccak


def build_integrity_payload(domain: str, event_type: str, event_date: str) -> str:
    """
    Build the canonical string used for integrity hashing.
    """
    return f"{domain.lower()}|{event_type.upper()}|{event_date}"


def compute_integrity_hash(domain: str, event_type: str, event_date: str) -> str:
    """
    Compute Keccak-256 hash of the canonical integrity payload.
    Returns hex string (0x...).
    """
    payload = build_integrity_payload(domain, event_type, event_date)
    return keccak(text=payload).hex()
