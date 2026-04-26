import sys; sys.path.insert(0,'.')
from backend.orchestrator.safety_guard import is_safe_query

tests = ['128gb', '128GB', '256gb', 'iphone 15 128gb', 'thoi', 'ngu a']
for t in tests:
    safe, reason = is_safe_query(t)
    r = reason[:80] if not safe else ""
    print(f"[{t}] safe={safe} {r}")
