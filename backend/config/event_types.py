# backend/config/event_types.py

"""
Locked event vocabulary for DNS Guard V2.
These are the ONLY event types allowed in the system.
"""

# Registrar / lifecycle events
REGISTERED = "REGISTERED"
OWNERSHIP_CHANGED = "OWNERSHIP_CHANGED"
EXPIRED = "EXPIRED"
RE_REGISTERED = "RE_REGISTERED"

# Security / abuse events
# V1-compatible abuse event type
ABUSE_FLAG = "ABUSE_FLAG"


# ---- Canonical collections ----

# All allowed event types
ALL_EVENT_TYPES = {
    REGISTERED,
    OWNERSHIP_CHANGED,
    EXPIRED,
    RE_REGISTERED,
    ABUSE_FLAG,
}

# Events that affect long-term trust
TRUST_RELEVANT_EVENTS = {
    OWNERSHIP_CHANGED,
    ABUSE_FLAG,
}

# Events eligible for blockchain anchoring
ANCHORABLE_EVENTS = {
    OWNERSHIP_CHANGED,
    ABUSE_FLAG,
}
