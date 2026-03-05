import sys
import os
import requests
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.trust.wayback_oracle import WaybackOracle
from backend.ingestion.cold_start import ColdStartOrchestrator

def run_phase5():
    print("=== Phase 5: Failure Simulation Results ===")
    domain = "testdomain.com"
    
    # Simulate 503
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 503
        res = WaybackOracle.get_earliest_snapshot(domain)
        print(f"503 Response handling -> returns: {res} (Expected None)")

    # Simulate Timeout
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        res = WaybackOracle.get_earliest_snapshot(domain)
        print(f"Timeout handling -> returns: {res} (Expected None)")

    # Simulate Empty Response
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        res = WaybackOracle.get_earliest_snapshot(domain)
        print(f"Empty Response handling -> returns: {res} (Expected None)")

if __name__ == "__main__":
    run_phase5()
