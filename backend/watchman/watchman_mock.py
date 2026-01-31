import sqlite3
from datetime import datetime

DB_PATH = "backend/dns_guard.db"

def report_new_phishing_domain(domain_name, description):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Insert domain if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO domains (domain_name, current_status)
        VALUES (?, 'RED')
    """, (domain_name,))

    # 2. Fetch domain ID
    cursor.execute("""
        SELECT id FROM domains WHERE domain_name = ?
    """, (domain_name,))
    domain_id = cursor.fetchone()[0]

    # 3. Insert abuse event
    cursor.execute("""
        INSERT INTO domain_events (
            domain_id,
            event_type,
            event_time,
            description
        ) VALUES (?, ?, ?, ?)
    """, (
        domain_id,
        'ABUSE_FLAG',
        datetime.utcnow(),
        description
    ))

    # 4. Update domain status to RED
    cursor.execute("""
        UPDATE domains
        SET current_status = 'RED'
        WHERE id = ?
    """, (domain_id,))

    conn.commit()
    conn.close()

    print(f"[WATCHMAN] 🚨 Phishing detected and recorded for: {domain_name}")

if __name__ == "__main__":
    report_new_phishing_domain(
        "login-secure-paypal-support.com",
        "Mock phishing site detected impersonating PayPal"
    )
