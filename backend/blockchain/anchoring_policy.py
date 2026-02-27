# backend/blockchain/anchoring_policy.py

from backend.config.event_types import ABUSE_FLAG, OWNERSHIP_CHANGED



ANCHORABLE_EVENT_TYPES = {
    ABUSE_FLAG,
    OWNERSHIP_CHANGED,
}


def should_anchor_event(domain: str, event_type: str) -> bool:
    """
    Decide whether a domain event should be anchored to the blockchain.
    """

    # Only selected high-impact events are anchored
    if event_type not in ANCHORABLE_EVENT_TYPES:
        return False

    return True
