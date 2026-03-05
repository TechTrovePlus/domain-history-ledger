from backend.config.event_types import (
    RE_REGISTRATION, REGISTRAR_TRANSFER, DOMAIN_DROPPED,
    STATUS_CHANGE, NAMESERVER_CHANGE
)

class DiffEngine:
    """
    Deterministically derives lifecycle events by comparing a previous RDAP snapshot
    with a new RDAP snapshot.
    """

    @staticmethod
    def compare(old_snapshot: dict, new_snapshot: dict) -> list:
        """
        Takes two normalized RDAP dictionaries and returns a list of event dictionaries.
        """
        events = []

        # 1. Check if Domain Dropped
        if old_snapshot and old_snapshot.get("exists") and not new_snapshot.get("exists"):
            events.append({
                "type": DOMAIN_DROPPED,
                "metadata": {
                    "previous_expiration": old_snapshot.get("expiration_date")
                }
            })
            return events # If dropped, no other state changes matter

        # If previous snapshot didn't exist, we don't emit a Re-registration here, 
        # it's handled by Cold Start or standard Registration ingestion.
        if not old_snapshot or not old_snapshot.get("exists"):
            return events

        # 2. Re-Registration (Creation date is newer than previous snapshot's)
        old_creation = old_snapshot.get("creation_date")
        new_creation = new_snapshot.get("creation_date")
        
        if old_creation and new_creation and new_creation > old_creation:
            # Domain was dropped and re-registered between our fetch cycles
            events.append({
                "type": DOMAIN_DROPPED,
                "metadata": {"implied": True, "reason": "newer_creation_date_observed"}
            })
            events.append({
                "type": RE_REGISTRATION,
                "metadata": {"previous_creation": old_creation, "new_creation": new_creation}
            })
            return events # Treat as full reset, other changes are part of new registration

        # 3. Registrar Transfer
        old_registrar = old_snapshot.get("registrar")
        new_registrar = new_snapshot.get("registrar")
        if old_registrar and new_registrar and old_registrar != new_registrar:
            events.append({
                "type": REGISTRAR_TRANSFER,
                "metadata": {"from": old_registrar, "to": new_registrar}
            })

        # 4. Nameserver Change
        old_ns = set(old_snapshot.get("nameservers", []))
        new_ns = set(new_snapshot.get("nameservers", []))
        if old_ns != new_ns:
            events.append({
                "type": NAMESERVER_CHANGE,
                "metadata": {
                    "added": list(new_ns - old_ns),
                    "removed": list(old_ns - new_ns)
                }
            })

        # 5. Status Change
        old_status = set(old_snapshot.get("status", []))
        new_status = set(new_snapshot.get("status", []))
        if old_status != new_status:
            events.append({
                "type": STATUS_CHANGE,
                "metadata": {
                    "added": list(new_status - old_status),
                    "removed": list(old_status - new_status)
                }
            })

        return events
