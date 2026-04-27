"""Tạo tài khoản admin mặc định."""
import sys; sys.path.insert(0,'.')
import bcrypt
from backend.db.connection import get_cursor

USERNAME = "admin"
PASSWORD = "admin123"   # đổi sau khi vào được

hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

with get_cursor() as cur:
    # Kiểm tra đã tồn tại chưa
    cur.execute("SELECT id FROM users WHERE username = %s", (USERNAME,))
    if cur.fetchone():
        # Cập nhật role thành admin nếu đã có
        cur.execute("UPDATE users SET role = 'admin' WHERE username = %s", (USERNAME,))
        print(f"Đã cập nhật '{USERNAME}' thành admin.")
    else:
        cur.execute(
            "INSERT INTO users (username, password, role, is_active) VALUES (%s, %s, 'admin', TRUE)",
            (USERNAME, hashed)
        )
        print(f"Đã tạo tài khoản admin:")
        print(f"  Username: {USERNAME}")
        print(f"  Password: {PASSWORD}")
