import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.db import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("SELECT domain_name FROM domains LIMIT 10")
    print("Domains in DB:", [r["domain_name"] for r in cursor.fetchall()])
