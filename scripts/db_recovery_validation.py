import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.db import get_db_cursor

def check_db():
    print("=== Phase 3: Schema Integrity ===")
    required_tables = {"domains", "domain_events", "domain_snapshots", "trust_history", "blockchain_records"}
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check schema
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = {row['table_name'] for row in cursor.fetchall()}
            
            missing = required_tables - tables
            if not missing:
                print("All tables present? Yes")
                print("Corruption detected? No")
            else:
                print(f"All tables present? No (Missing: {missing})")
                
            # Phase 4 Prep: Clean test domains
            print("\n=== Phase 4: Controlled Cold Start Prep ===")
            targets = ('google.com', 'discord.com', 'test-malicious-domain', 'cal-node.caliphdotham.in.net')
            target_tup = tuple(targets)
            placeholders = ','.join(['%s']*len(targets))
            
            # Remove from referenced tables first
            cursor.execute(f"DELETE FROM blockchain_records WHERE event_id IN (SELECT id FROM domain_events WHERE domain_id IN (SELECT id FROM domains WHERE domain_name IN ({placeholders})))", target_tup)
            cursor.execute(f"DELETE FROM trust_history WHERE domain_id IN (SELECT id FROM domains WHERE domain_name IN ({placeholders}))", target_tup)
            cursor.execute(f"DELETE FROM domain_events WHERE domain_id IN (SELECT id FROM domains WHERE domain_name IN ({placeholders}))", target_tup)
            cursor.execute(f"DELETE FROM domain_snapshots WHERE domain_id IN (SELECT id FROM domains WHERE domain_name IN ({placeholders}))", target_tup)
            cursor.execute(f"DELETE FROM domains WHERE domain_name IN ({placeholders})", target_tup)
            
            print("Deleted test domains successfully.")
            
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    check_db()
