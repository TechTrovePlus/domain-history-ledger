import requests
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.trust.wayback_oracle import WaybackOracle

def manual_test(domain):
    try:
        url = f"http://web.archive.org/cdx/search/cdx?url={domain}&limit=1&collapse=urlkey&fl=timestamp&filter=statuscode:200"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            return resp.text.split('\n')[0].strip()
        return None
    except Exception as e:
        return f"Error: {e}"

def run_phase2():
    print("=== Phase 2: Manual vs Programmatic ===")
    domains = ["discord.com", "google.com", "example-recent-domain.com"]
    for d in domains:
        print(f"\nDomain: {d}")
        manual_ts = manual_test(d)
        print(f"Manual timestamp: {manual_ts}")
        prog_ts = WaybackOracle.get_earliest_snapshot(d)
        print(f"Programmatic timestamp: {prog_ts}")

if __name__ == "__main__":
    run_phase2()
