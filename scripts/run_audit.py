import sys
import os
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.trust.trust_engine import TrustEngine
from backend.api.search import search_domain
from backend.db import get_db_cursor
from backend.config.event_types import ABUSE_HISTORY_DETECTED, ACTIVE_THREAT_DETECTED

def run_phase1():
    print("=== Phase 1: TrustEngine Direct Verification ===")
    
    # Test A: Clean Case
    res_a = TrustEngine.calculate_score([])
    print(f"Clean Case -> final_score: {res_a['final_score']}, is_trusted: {res_a['is_trusted']}")
    
    # Test B: Mid Score Case (Score 80)
    # domain_age_years > 10 gives penalty of 20
    res_b = TrustEngine.calculate_score([
        {'event_type': ABUSE_HISTORY_DETECTED, 'event_metadata': {'domain_age_years': 15}}
    ])
    print(f"Mid Case -> final_score: {res_b['final_score']}, is_trusted: {res_b['is_trusted']}")
    
    # Test C: Low Score Case (Score 10)
    # active threat gives penalty of 90
    res_c = TrustEngine.calculate_score([
        {'event_type': ACTIVE_THREAT_DETECTED, 'event_metadata': {}}
    ])
    print(f"Low Case -> final_score: {res_c['final_score']}, is_trusted: {res_c['is_trusted']}")

def run_phase2():
    print("\n=== Phase 2: API Layer Verification ===")
    domains = ["google.com", "discord.com", "quicrob.com"]
    
    for d in domains:
        res = search_domain(d)
        print(f"Domain: {d}")
        print(f"Raw Response: {json.dumps(res)}")

def run_phase4():
    print("\n=== Phase 4: Database Check ===")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT d.domain_name, th.active_trust_score, th.is_trusted 
                FROM domains d
                JOIN trust_history th ON d.id = th.domain_id
                WHERE d.domain_name IN ('google.com', 'discord.com', 'quicrob.com')
                ORDER BY th.id DESC LIMIT 10
            """)
            rows = cursor.fetchall()
            if not rows:
                print("No rows found in trust_history for these domains.")
            for row in rows:
                print(f"{row['domain_name']} -> score: {row['active_trust_score']}, is_trusted: {row['is_trusted']}")
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    run_phase1()
    run_phase2()
    run_phase4()
