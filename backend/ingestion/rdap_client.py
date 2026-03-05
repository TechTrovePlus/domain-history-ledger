import requests
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RDAPClient:
    """
    Authoritative RDAP client with dynamic TLD routing and exponential backoff.
    """
    IANA_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"

    def __init__(self):
        self._tld_registry = {}
        self._load_iana_bootstrap()

    def _load_iana_bootstrap(self):
        """Fetches and builds the TLD to RDAP server mapping."""
        try:
            from backend.config import settings
            response = requests.get(self.IANA_BOOTSTRAP_URL, timeout=settings.RDAP_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # The 'services' list contains lists where [0] is a list of TLDs, and [1] is a list of URLs
            for service in data.get("services", []):
                tlds = service[0]
                urls = service[1]
                if not urls:
                    continue
                    
                primary_url = urls[0] # Prefer the first URL (usually HTTPS)
                for tld in tlds:
                    # Clean TLD (remove leading dot if present)
                    clean_tld = tld.strip(".")
                    self._tld_registry[clean_tld] = primary_url
            
            logger.info(f"Loaded {len(self._tld_registry)} TLDs from IANA bootstrap registry.")
        except Exception as e:
            logger.error(f"Failed to load IANA RDAP bootstrap data: {e}")
            # We could fallback to a hardcoded mapping for common TLDs if needed
            self._fallback_mappings()

    def _fallback_mappings(self):
        self._tld_registry.update({
            "com": "https://rdap.verisign.com/com/v1/",
            "net": "https://rdap.verisign.com/net/v1/",
            "org": "https://rdap.publicinterestregistry.net/rdap/",
            "io": "https://rdap.donuts.co/rdap/",
            "co": "https://rdap.nic.co/"
        })

    def get_rdap_server_for_domain(self, domain: str) -> str:
        """Determines the authoritative RDAP server for a domain."""
        parts = domain.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid domain format: {domain}")
        
        tld = parts[-1].lower()
        base_url = self._tld_registry.get(tld)
        
        if not base_url:
            raise ValueError(f"No RDAP server found for TLD: .{tld}")
        
        return base_url

    def fetch_domain_state(self, domain: str, max_retries: int = 3) -> dict:
        """
        Fetches the complete RDAP response for a domain.
        Uses exponential backoff for rate limiting (429).
        """
        base_url = self.get_rdap_server_for_domain(domain)
        # Ensure base_url ends with a slash before appending 'domain/'
        if not base_url.endswith('/'):
            base_url += '/'
        query_url = f"{base_url}domain/{domain}"

        retries = 0
        backoff_time = 2  # initial backoff in seconds

        while retries <= max_retries:
            try:
                from backend.config import settings
                # Some registries strictly require User-Agent
                headers = {"User-Agent": "DNSGuard/1.0", "Accept": "application/rdap+json"}
                response = requests.get(query_url, headers=headers, timeout=settings.RDAP_TIMEOUT)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Domain not found, returning explicitly to handle DOMAIN_DROPPED logic
                    return {"error": "not_found", "status_code": 404}
                elif response.status_code == 429:
                    logger.warning(f"Rate limited by {base_url}. Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                    retries += 1
                    backoff_time *= 2  # Exponential backoff
                    continue
                else:
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                logger.error(f"RDAP request failed for {domain}: {e}")
                if retries < max_retries:
                    time.sleep(backoff_time)
                    retries += 1
                    backoff_time *= 2
                    continue
                else:
                    return {"error": str(e), "status_code": 500}

        return {"error": "max_retries_exceeded", "status_code": 429}

# Usage example
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = RDAPClient()
    print("Fetching google.com...")
    result = client.fetch_domain_state("google.com")
    print(result.keys() if "error" not in result else result)
