import sqlite3

def seed():
    conn = sqlite3.connect('backend/dns_guard.db')
    cursor = conn.cursor()

    demo_domains = [
        ('google.com', 'GREEN'),
        ('amazon-deals.net', 'YELLOW'),
        ('old-scam-domain.com', 'RED')
    ]

    for domain, status in demo_domains:
        cursor.execute(
            "INSERT OR IGNORE INTO domains (domain_name, current_status) VALUES (?, ?)",
            (domain, status)
        )

    cursor.execute(
        "SELECT id FROM domains WHERE domain_name = 'old-scam-domain.com'"
    )
    domain_id = cursor.fetchone()[0]

    cursor.execute('''
        INSERT INTO domain_events
        (domain_id, event_type, description)
        VALUES (?, ?, ?)
    ''', (
        domain_id,
        'ABUSE_FLAG',
        'Historic phishing campaign detected'
    ))

    conn.commit()
    conn.close()
    print("Demo data seeded.")

if __name__ == "__main__":
    seed()
