from backend.db import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("""
        SELECT e.id, e.event_hash, e.event_type, d.domain_name 
        FROM domain_events e
        JOIN domains d ON e.domain_id = d.id
        LEFT JOIN blockchain_records b ON e.id = b.event_id
        WHERE b.id IS NULL
        ORDER BY e.event_timestamp ASC
        LIMIT 50
    """)
    unanchored = cursor.fetchall()
    from backend.config.event_types import ANCHORABLE_EVENTS
    print("ANCHORABLE_EVENTS:", ANCHORABLE_EVENTS)
    for evt in unanchored:
        print("Event Type:", evt['event_type'])
        print("Is Anchorable?", evt['event_type'] in ANCHORABLE_EVENTS)
