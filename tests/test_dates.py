import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.ingestion.cold_start import ColdStartOrchestrator

def test_dates():
    print("=== Test Case: discord.com ===")
    rdap_creation_date = "2015-05-23T16:03:00Z"
    wayback_earliest = "2015-05-25T11:22:33Z"
    
    print(f"RDAP creation: {rdap_creation_date}")
    print(f"Wayback earliest: {wayback_earliest}")
    
    rdap_dt = datetime.strptime(rdap_creation_date, "%Y-%m-%dT%H:%M:%SZ")
    wayback_dt = datetime.strptime(wayback_earliest, "%Y-%m-%dT%H:%M:%SZ")
    
    print(f"Discontinuity triggered? {'Yes' if wayback_dt < rdap_dt else 'No'}")

if __name__ == "__main__":
    test_dates()
