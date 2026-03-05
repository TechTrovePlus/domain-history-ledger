import sys
import os
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.api.search import search_domain
from backend.db import get_db_cursor
from test_online_offline import get_active_malicious_domain

def run_e2e(domain):
    print(f"\n{domain}:")
    
    # Trigger Cold Start async and wait for completion
    res = search_domain(domain)
    attempt = 0
    while res.get('status') == 'SCAN_QUEUED' and attempt < 8:
        time.sleep(3)
        res = search_domain(domain)
        attempt += 1

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain,))
            domain_row = cursor.fetchone()
            if domain_row:
                cursor.execute("SELECT event_type FROM domain_events WHERE domain_id = %s ORDER BY id ASC", (domain_row['id'],))
                events = [row['event_type'] for row in cursor.fetchall()]
                print(f"Events created: {', '.join(events)}")
            else:
                print("Events created: None (Domain not found in DB)")
    except Exception as e:
        print(f"DB Error fetching events: {e}")

    print(f"Final score: {res.get('final_score')}")
    print(f"is_trusted: {res.get('is_trusted')}")

def check_ledger():
    print("\n[Ledger Integrity]")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT domain_id, id, event_hash, previous_event_hash FROM domain_events ORDER BY domain_id ASC, id ASC")
            events = cursor.fetchall()
            
            integrity = "Yes"
            for i in range(1, len(events)):
                if events[i]['domain_id'] == events[i-1]['domain_id']:
                    if events[i]['previous_event_hash'] != events[i-1]['event_hash']:
                        integrity = "No"
                        break
            
            print(f"Hash chain intact? {integrity}")
    except Exception as e:
        print(f"Ledger check failed: {e}")

if __name__ == "__main__":
    print("[Cold Start End-to-End Test]")
    run_e2e("google.com")
    run_e2e("discord.com")
    
    active_domain = get_active_malicious_domain()
    if active_domain:
        run_e2e(active_domain)
    else:
        print("active-malicious-domain: Could not retrieve from URLhaus")
        
    check_ledger()
