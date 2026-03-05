import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.db import get_db_cursor

from backend.trust.trust_engine import TrustEngine

def run_db():
    try:
        with get_db_cursor() as cursor:
            for d in ["google.com", "discord.com"]:
                cursor.execute("""
                    SELECT 
                        de.event_type,
                        de.event_metadata,
                        de.event_timestamp
                    FROM domains d
                    LEFT JOIN domain_events de ON d.id = de.domain_id
                    WHERE d.domain_name = %s
                """, (d,))
                rows = cursor.fetchall()
                if not rows:
                    print(f"\n{d}:\nEvents created: None\nFinal score: None\nis_trusted: None")
                    continue
                
                events = list({r['event_type'] for r in rows if r['event_type']})
                
                # Dynamically calculate just like search.py
                calc_events = [dict(r) for r in rows if r['event_type']]
                score_dict = TrustEngine.calculate_score(calc_events) if calc_events else None
                
                score = score_dict['final_score'] if score_dict else None
                trusted = score_dict['is_trusted'] if score_dict else None
                
                print(f"\n{d}:")
                print(f"Events created: {', '.join(events)}")
                print(f"Final score: {score}")
                print(f"is_trusted: {trusted}")

            # Now fetch the malicious domain
            cursor.execute("""
                    SELECT 
                        d.domain_name,
                        de.event_type,
                        de.event_metadata,
                        de.event_timestamp
                    FROM domains d
                    LEFT JOIN domain_events de ON d.id = de.domain_id
                    WHERE de.event_type = 'ABUSE_HISTORY_DETECTED' OR de.event_type = 'ACTIVE_THREAT_DETECTED'
            """)
            rows = cursor.fetchall()
            if rows:
                d = rows[0]['domain_name']
                # Grab all events for this specific domain
                cursor.execute("""
                    SELECT 
                        de.event_type,
                        de.event_metadata,
                        de.event_timestamp
                    FROM domains d
                    LEFT JOIN domain_events de ON d.id = de.domain_id
                    WHERE d.domain_name = %s
                """, (d,))
                dom_rows = cursor.fetchall()

                events = list({r['event_type'] for r in dom_rows if r['event_type']})
                calc_events = [dict(r) for r in dom_rows if r['event_type']]
                score_dict = TrustEngine.calculate_score(calc_events) if calc_events else None
                
                score = score_dict['final_score'] if score_dict else None
                trusted = score_dict['is_trusted'] if score_dict else None
                
                print(f"\nactive-malicious-domain ({d}):")
                print(f"Events created: {', '.join(events)}")
                print(f"Final score: {score}")
                print(f"is_trusted: {trusted}")
                
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    run_db()
