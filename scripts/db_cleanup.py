import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.db import get_db_cursor

domains_to_clean = ['discord.com', 'google.com', 'quicrob.com']

def clean_database():
    print("[DATABASE CLEANUP]")
    try:
        with get_db_cursor(commit=True) as cursor:
            # Get IDs
            placeholders = ','.join(['%s'] * len(domains_to_clean))
            cursor.execute(f"SELECT id, domain_name FROM domains WHERE domain_name IN ({placeholders})", tuple(domains_to_clean))
            rows = cursor.fetchall()
            
            if not rows:
                print("No target domains found to delete.")
                return True
                
            domain_ids = [r['id'] for r in rows]
            found_names = [r['domain_name'] for r in rows]
            print(f"Found domains to clean: {', '.join(found_names)}")
            
            id_placeholders = ','.join(['%s'] * len(domain_ids))
            id_tuple = tuple(domain_ids)
            
            # FK-safe order: blockchain_records (if fk to events), trust_history (fk to domain), domain_events (fk to domain), domain_snapshots (fk to domain), domains
            # We don't have blockchain_records tied to domains normally, they tie to events, but let's delete trust_history first
            cursor.execute(f"DELETE FROM trust_history WHERE domain_id IN ({id_placeholders})", id_tuple)
            print(f"Deleted trust_history records.")
            
            # Actually, blockchain records reference domain_events.id, so we need to delete them first
            cursor.execute(f"""
                DELETE FROM blockchain_records 
                WHERE event_id IN (SELECT id FROM domain_events WHERE domain_id IN ({id_placeholders}))
            """, id_tuple)
            print(f"Deleted blockchain_records.")
            
            cursor.execute(f"DELETE FROM domain_events WHERE domain_id IN ({id_placeholders})", id_tuple)
            print(f"Deleted domain_events records.")
            
            cursor.execute(f"DELETE FROM domain_snapshots WHERE domain_id IN ({id_placeholders})", id_tuple)
            print(f"Deleted domain_snapshots records.")
            
            cursor.execute(f"DELETE FROM domains WHERE id IN ({id_placeholders})", id_tuple)
            print(f"Deleted domains records.")
            
            # Verification
            cursor.execute(f"SELECT COUNT(*) as c FROM domains WHERE domain_name IN ({placeholders})", tuple(domains_to_clean))
            count = cursor.fetchone()['c']
            print(f"Verification query results: Remaining target domains = {count}")
            
        print("Domains removed: " + ", ".join(found_names))
        return True
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    clean_database()
