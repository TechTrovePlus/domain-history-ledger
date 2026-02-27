import sqlite3

def init_db():
    conn = sqlite3.connect('backend/dns_guard.db')
    cursor = conn.cursor()

    # Domains table (current snapshot)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_name TEXT UNIQUE NOT NULL,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            current_status TEXT CHECK (
                current_status IN ('UNKNOWN', 'GREEN', 'YELLOW', 'RED')
            ) NOT NULL
        )
    ''')

    # Domain events (immutable ledger)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER NOT NULL,
            event_type TEXT CHECK (
                event_type IN (
                    'REGISTERED',
                    'OWNERSHIP_CHANGED',
                    'ABUSE_FLAG'
                )
            ) NOT NULL,
            event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            blockchain_tx TEXT,
            integrity_hash TEXT,
            FOREIGN KEY (domain_id) REFERENCES domains(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
