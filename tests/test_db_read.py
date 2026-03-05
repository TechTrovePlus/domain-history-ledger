import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.db import get_db_cursor
from backend.trust.trust_engine import TrustEngine

def test_db_read():
    domain = 'discord.com'
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain,))
        domain_row = cursor.fetchone()
        if not domain_row:
            print("Domain not found")
            return
            
        domain_id = domain_row['id']
        
        cursor.execute("SELECT event_type, event_metadata FROM domain_events WHERE domain_id = %s ORDER BY id ASC", (domain_id,))
        events = cursor.fetchall()
        
        print("Events fetched:", events)
        
        trust_calc = TrustEngine.calculate_score(events)
        print("trust_calc['is_trusted'] =", trust_calc['is_trusted'])

if __name__ == "__main__":
    test_db_read()
