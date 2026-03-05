import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WaybackOracle:
    """
    Queries the Internet Archive Wayback Machine CDX API to discover the earliest 
    known content snapshot for a domain.
    Used to detect domain discontinuities (content existing prior to current RDAP registration date).
    """

    CDX_API_URL = "https://web.archive.org/cdx/search/cdx"

    @staticmethod
    def get_earliest_snapshot(domain: str) -> str:
        """
        Returns the earliest snapshot timestamp as an ISO 8601 string, or None if no history exists.
        """
        try:
            from backend.config import settings
            import time
            params = {
                "url": domain,
                "limit": 1,
                "collapse": "urlkey",
                "fl": "timestamp",
                "filter": "statuscode:200"
            }
            
            backoff = 1.5
            for attempt in range(2):
                try:
                    response = requests.get(WaybackOracle.CDX_API_URL, params=params, timeout=settings.WAYBACK_TIMEOUT)
                    
                    if response.status_code == 200 and response.text.strip():
                        # CDX returns plain text format YYYYMMDDhhmmss
                        raw_ts = response.text.strip().split("\n")[0]
                        
                        # Parse YYYYMMDDhhmmss to ISO standard
                        dt = datetime.strptime(raw_ts, "%Y%m%d%H%M%S")
                        return dt.isoformat() + "Z"
                        
                    elif response.status_code >= 500 and attempt == 0:
                        time.sleep(backoff)
                        continue
                    break
                except requests.exceptions.Timeout:
                    if attempt == 0:
                        time.sleep(backoff)
                        continue
                    logger.warning(f"Wayback Machine API timed out for {domain}.")
            
            return None
            
        except Exception as e:
            logger.error(f"Wayback Machine query failed for {domain}: {e}")
            return None

if __name__ == "__main__":
    print(f"Earliest snapshot for google.com: {WaybackOracle.get_earliest_snapshot('google.com')}")
