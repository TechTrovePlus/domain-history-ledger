import psycopg2
conn = psycopg2.connect("dbname=dns_guard_db user=dns_guard password=password host=localhost port=5432")
cursor = conn.cursor()
cursor.execute("SELECT * FROM domain_snapshots WHERE snapshot_hash='930b8e72750eefa89a37e583764b85c2cbfb9d45a90ad74a24f0c40687a6c435'")
print(cursor.fetchone())
