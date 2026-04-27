import sys; sys.path.insert(0,'.')
from backend.db.connection import get_cursor

with get_cursor() as cur:
    cur.execute('SELECT id, username, email, role, is_active FROM users ORDER BY created_at')
    rows = cur.fetchall()
    if not rows:
        print('Chua co user nao')
    for r in rows:
        role = r["role"]
        name = r["username"]
        email = r["email"] or "(no email)"
        active = r["is_active"]
        print(f"  [{role}] {name} | {email} | active={active}")
