import requests
import logging
import time
import csv
from io import StringIO
from urllib.parse import urlparse
from backend.config import settings

logger = logging.getLogger(__name__)

class AbuseOracle:
    """
    Queries URLHaus to check if a domain has a documented history of malware distribution.
    Supports API mode and DEMO mode safely without arbitrary payload downloads.
    """
    
    API_URL = "https://urlhaus-api.abuse.ch/v1/host/"
    
    _demo_cache = None
    _demo_cache_time = 0

    @classmethod
    def _refresh_demo_cache(cls):
        """Fetches the latest CSV from URLhaus and caches it in memory."""
        try:
            logger.info("URLhaus DEMO mode: Refreshing CSV cache...")
            response = requests.get("https://urlhaus.abuse.ch/downloads/csv_recent/", timeout=settings.URLHAUS_TIMEOUT, stream=True)
            if response.status_code == 200:
                import codecs
                stream = codecs.iterdecode(response.iter_lines(), 'utf-8')
                reader = csv.reader((line for line in stream if line and not line.startswith('#')), delimiter=',')
                
                new_cache = {}
                for row in reader:
                    if len(row) > 5:
                        url = row[2]
                        first_seen = row[1]
                        parsed_domain = urlparse(url).netloc.split(':')[0]
                        
                        if parsed_domain not in new_cache:
                            new_cache[parsed_domain] = {
                                "url_count": 0,
                                "first_seen": first_seen,
                                "malware_types": set()
                            }
                        
                        new_cache[parsed_domain]["url_count"] += 1
                        
                        if row[4]:
                            new_cache[parsed_domain]["malware_types"].add(row[4])
                        if row[5]:
                            new_cache[parsed_domain]["malware_types"].update(row[5].split(','))
                
                cls._demo_cache = new_cache
                cls._demo_cache_time = time.time()
                logger.info("URLhaus DEMO mode: Cache refreshed successfully.")
                return True
            else:
                logger.error(f"URLhaus CSV feed returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"URLhaus CSV cache refresh failed: {e}")
            return False

    @classmethod
    def check_domain_abuse(cls, domain: str):
        """
        Queries URLhaus depending on URLHAUS_MODE configuration.
        Returns a dictionary with abuse data, None if clean, or 'oracle_unavailable' on API auth failure.
        """
        if settings.URLHAUS_MODE == "API":
            if not settings.URLHAUS_API_KEY:
                logger.error("URLhaus configuration error: API mode enabled but URLHAUS_API_KEY is not set.")
                return "oracle_unavailable"

            headers = {"Auth-Key": settings.URLHAUS_API_KEY}
            data = {"host": domain}
            backoff = 1.5

            for attempt in range(2):
                try:
                    response = requests.post(
                        cls.API_URL,
                        headers=headers,
                        data=data,
                        timeout=settings.URLHAUS_TIMEOUT
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("query_status") == "ok" and int(result.get("url_count", 0)) > 0:
                            online_count = 0
                            offline_count = 0
                            
                            for url in result.get("urls", []):
                                status = url.get("url_status")
                                if status == "online":
                                    online_count += 1
                                elif status == "offline":
                                    offline_count += 1

                            return {
                                "url_count": int(result.get("url_count", 0)),
                                "online_count": online_count,
                                "offline_count": offline_count,
                                "first_seen": result.get("firstseen"),
                                "malware_types": list(
                                    set([
                                        tag
                                        for url in result.get("urls", [])
                                        for tag in (url.get("tags") or [])
                                    ])
                                ),
                                "oracle": "URLhaus API"
                            }
                        return None

                    elif response.status_code in [401, 403]:
                        logger.error(f"URLhaus configuration error: {response.status_code} Unauthorized.")
                        return "oracle_unavailable"

                    elif response.status_code >= 500 and attempt == 0:
                        time.sleep(backoff)
                        continue

                    return None

                except requests.exceptions.Timeout:
                    if attempt == 0:
                        time.sleep(backoff)
                        continue
                    logger.warning(f"URLhaus API timed out for {domain}.")
            return None

        elif settings.URLHAUS_MODE == "DEMO":
            if not cls._demo_cache or (time.time() - cls._demo_cache_time) > settings.URLHAUS_CACHE_TTL:
                success = cls._refresh_demo_cache()
                if not success and not cls._demo_cache:
                    return None
                    
            domain_data = cls._demo_cache.get(domain)
            if domain_data:
                return {
                    "url_count": domain_data["url_count"],
                    "online_count": 0,
                    "offline_count": domain_data["url_count"],
                    "first_seen": domain_data["first_seen"],
                    "malware_types": list(domain_data["malware_types"]),
                    "oracle": "URLhaus DEMO Cache"
                }
            
            return None
        
        else:
            logger.warning(f"Unknown URLHAUS_MODE: {settings.URLHAUS_MODE}")
            return None

if __name__ == "__main__":
    # Test with a known clean domain 
    print(f"Abuse check for google.com: {AbuseOracle.check_domain_abuse('google.com')}")
