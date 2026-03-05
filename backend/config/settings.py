import os
from dotenv import load_dotenv

load_dotenv()

# Options: DEMO, LIVE
DNS_GUARD_ENV = os.getenv("DNS_GUARD_ENV", "DEMO").upper()

# Database Configs
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "dns_guard")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "dns_guard_db")

# Blockchain Configs
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6")

# Oracle Configs
WAYBACK_TIMEOUT = int(os.getenv("WAYBACK_TIMEOUT", "10"))
URLHAUS_TIMEOUT = int(os.getenv("URLHAUS_TIMEOUT", "10"))
URLHAUS_API_KEY = os.getenv("URLHAUS_API_KEY", "")
URLHAUS_CACHE_TTL = int(os.getenv("URLHAUS_CACHE_TTL", "600"))
URLHAUS_MODE = os.getenv("URLHAUS_MODE", "DEMO").upper()
RDAP_TIMEOUT = int(os.getenv("RDAP_TIMEOUT", "10"))
RDAP_MAX_RETRIES = int(os.getenv("RDAP_MAX_RETRIES", "3"))

# Worker Configs
ANCHOR_POLL_INTERVAL = int(os.getenv("ANCHOR_POLL_INTERVAL", "15"))
DIFF_POLL_INTERVAL = int(os.getenv("DIFF_POLL_INTERVAL", "86400"))
RDAP_REQUEST_DELAY = int(os.getenv("RDAP_REQUEST_DELAY", "1"))
DIFF_BATCH_SIZE = int(os.getenv("DIFF_BATCH_SIZE", "50"))

def is_live() -> bool:
    return DNS_GUARD_ENV == "LIVE"

def is_demo() -> bool:
    return DNS_GUARD_ENV == "DEMO"
