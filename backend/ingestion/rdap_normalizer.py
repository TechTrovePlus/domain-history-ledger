import json
from datetime import datetime

class RDAPNormalizer:
    """
    Normalizes deeply nested, registry-specific RDAP JSON responses into a consistent schema 
    for the diff engine and database storage.
    """
    
    @staticmethod
    def normalize(rdap_json: dict) -> dict:
        """
        Takes raw RDAP JSON and returns a normalized dictionary.
        Returns empty fields internally if data is missing, rather than failing.
        """
        # If the domain was dropped/not found
        if rdap_json.get("error") == "not_found" or rdap_json.get("status_code") == 404:
            return {
                "exists": False,
                "domain": None,
                "status": ["DROPPED"],
                "registrar": None,
                "creation_date": None,
                "expiration_date": None,
                "updated_date": None,
                "nameservers": []
            }

        handle = rdap_json.get("handle")
        domain_name = rdap_json.get("ldhName", "").lower()
        status = rdap_json.get("status", [])

        # Extract dates from events
        events = rdap_json.get("events", [])
        creation_date = RDAPNormalizer._extract_event_date(events, "registration")
        expiration_date = RDAPNormalizer._extract_event_date(events, "expiration")
        updated_date = RDAPNormalizer._extract_event_date(events, "last changed")

        # Extract nameservers
        nameservers = []
        for ns in rdap_json.get("nameservers", []):
            if "ldhName" in ns:
                nameservers.append(ns["ldhName"].lower())

        # Extract Registrar from entities
        registrar = None
        for entity in rdap_json.get("entities", []):
            if "registrar" in entity.get("roles", []):
                # Vcard array format: ["vcard", [["fn", {}, "text", "GoDaddy.com, LLC"]]]
                vcard = entity.get("vcardArray", [])
                if vcard and len(vcard) > 1:
                    for properties in vcard[1]:
                        if properties[0] == "fn":
                            registrar = properties[3]
                            break
                break

        return {
            "exists": True,
            "domain": domain_name,
            "status": sorted(status), # sort for deterministic diffing
            "registrar": registrar,
            "creation_date": creation_date,
            "expiration_date": expiration_date,
            "updated_date": updated_date,
            "nameservers": sorted(nameservers)
        }

    @staticmethod
    def _extract_event_date(events: list, event_action: str) -> str:
        """Helper to extract action timestamps from RDAP event list."""
        for event in events:
            if event.get("eventAction", "").lower() == event_action:
                return event.get("eventDate")
        return None

if __name__ == "__main__":
    from rdap_client import RDAPClient
    client = RDAPClient()
    raw = client.fetch_domain_state("github.com")
    normalized = RDAPNormalizer.normalize(raw)
    print(json.dumps(normalized, indent=2))
