import sys; sys.path.insert(0,'.')
from backend.db.connection import get_cursor

with get_cursor() as cur:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
    cols = [r['column_name'] for r in cur.fetchall()]
    print("users columns:", cols)
