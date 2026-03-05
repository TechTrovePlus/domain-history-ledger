import psycopg2
import json

def test():
    conn = psycopg2.connect("dbname=dns_guard_db user=dns_guard password=password host=localhost port=5432")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM domains WHERE domain_name='carrier-packets-docs.com'")
    domain = cursor.fetchone()
    if not domain:
        print("Domain not found")
        return
    d_id = domain[0]
    cursor.execute("SELECT * FROM domain_snapshots WHERE domain_id=%s", (d_id,))
    print(f"Snapshots: {cursor.fetchall()}")
    cursor.execute("SELECT * FROM domain_events WHERE domain_id=%s", (d_id,))
    print(f"Events: {cursor.fetchall()}")

test()
