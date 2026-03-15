from backend.db import get_db_connection

def init_db():
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    # domains table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id SERIAL PRIMARY KEY,
            domain_name VARCHAR(255) UNIQUE NOT NULL,
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            active_trust_score INTEGER DEFAULT 100,
            monitored BOOLEAN DEFAULT TRUE
        );
    ''')

    # domain_snapshots table (immutable)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_snapshots (
            id SERIAL PRIMARY KEY,
            domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
            snapshot_data JSONB NOT NULL,
            snapshot_hash VARCHAR(64) UNIQUE NOT NULL,
            previous_snapshot_hash VARCHAR(64),
            retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # domain_events table (core ledger)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_events (
            id SERIAL PRIMARY KEY,
            domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
            event_type VARCHAR(100) NOT NULL,
            event_metadata JSONB NOT NULL,
            event_hash VARCHAR(64) UNIQUE NOT NULL,
            previous_event_hash VARCHAR(64),
            event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # trust_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trust_history (
            id SERIAL PRIMARY KEY,
            domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
            score_change INTEGER NOT NULL,
            reason_summary TEXT NOT NULL,
            event_id INTEGER REFERENCES domain_events(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # blockchain_records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blockchain_records (
            id SERIAL PRIMARY KEY,
            event_id INTEGER UNIQUE NOT NULL REFERENCES domain_events(id) ON DELETE CASCADE,
            tx_hash VARCHAR(66) NOT NULL,
            block_number INTEGER NOT NULL,
            anchored_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.close()
    conn.close()
    print("PostgreSQL Database initialized successfully.")

if __name__ == "__main__":
    init_db()
