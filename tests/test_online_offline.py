import sys
import os
import requests
import csv
from io import StringIO
from urllib.parse import urlparse
import time
import json
import logging

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.trust.trust_engine import TrustEngine
from backend.api.search import search_domain
from backend.config.event_types import ABUSE_HISTORY_DETECTED

# Suppress debug logs
logging.basicConfig(level=logging.WARNING)

def get_active_malicious_domain():
    print("Fetching active malicious domain from URLhaus...")
    response = requests.get("https://urlhaus.abuse.ch/downloads/csv_recent/")
    if response.status_code == 200:
        f = StringIO(response.text)
        reader = csv.reader((line for line in f if not line.startswith('#')), delimiter=',')
        for row in reader:
            if len(row) > 5 and row[3] == "online":
                url_string = row[2]
                parsed_domain = urlparse(url_string).netloc.split(':')[0]
                # exclude IP addresses to only test proper domains
                if any(c.isalpha() for c in parsed_domain):
                    return parsed_domain
    return None

def test_api(domain, expected_desc):
    print(f"\nEvaluating: {domain} ({expected_desc})")
    
    # Trigger Cold Start async and wait for completion
    res = search_domain(domain)
    attempt = 0
    while res.get('status') == 'SCAN_QUEUED' and attempt < 8:
        time.sleep(3)
        res = search_domain(domain)
        attempt += 1

    print(f"Events created: {res.get('event_count')}")
    print(f"Final score: {res.get('final_score')}")
    print(f"is_trusted: {res.get('is_trusted')}")
    # Display the penalties to confirm
    for pen in res.get('penalties', []):
        if pen['type'] == ABUSE_HISTORY_DETECTED:
            print(f"Penalty details: {pen}")

def test_backward_compatibility():
    print("\nEvaluating: Backward Compatibility")
    # Simulate an old event lacking online_count and offline_count
    old_event = {
        "event_type": ABUSE_HISTORY_DETECTED,
        "event_metadata": {
            "url_count": 2,
            "domain_age_years": 1,
            "malware_types": ["botnet"],
            "oracle": "URLhaus API"
        }
    }
    
    try:
        calc = TrustEngine.calculate_score([old_event])
        print("Crash observed? No")
        for p in calc.get('penalties', []):
            if p.get('type') == ABUSE_HISTORY_DETECTED:
                print(f"Fallback mapping penalty: {p.get('penalty')} (Expected 40)")
    except Exception as e:
        print(f"Crash observed? Yes ({e})")

def run_tests():
    print("=== Phase 3: Testing Requirements ===")
    
    # 1. Google (Clean)
    test_api("google.com", "clean")
    
    # 2. Discord (Historical)
    test_api("discord.com", "historical abuse, likely offline")
    
    # 3. Active Threat
    active_domain = get_active_malicious_domain()
    if active_domain:
        test_api(active_domain, "active malicious host")
    else:
        print("Could not find a valid online malicious domain from URLhaus.")

    # 4. Backward Compatibility
    test_backward_compatibility()

if __name__ == "__main__":
    run_tests()
