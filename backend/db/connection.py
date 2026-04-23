"""
connection.py
Quản lý kết nối PostgreSQL 16 cho toàn bộ backend.

Dùng psycopg2 (synchronous) để tương thích với code hiện tại.
FastAPI sẽ dùng asyncpg sau này nếu cần tối ưu throughput.

Các module khác chỉ cần import:
    from backend.db.connection import get_conn, get_cursor
"""
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env"
))


def _build_dsn() -> str:
    """Tạo Data Source Name từ biến môi trường."""
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'datn_chatbot')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')} "
        f"options='-c client_encoding=UTF8'"
    )


def get_conn():
    """
    Trả về một connection mới đến PostgreSQL.
    Caller có trách nhiệm gọi .close() sau khi dùng xong.
    Với code ngắn nên dùng get_cursor() context manager thay thế.
    """
    return psycopg2.connect(
        _build_dsn(),
        cursor_factory=psycopg2.extras.RealDictCursor,  # Kết quả trả về như dict
    )


@contextmanager
def get_cursor(autocommit: bool = False):
    """
    Context manager tiện lợi: tự động commit/rollback và đóng connection.

    Dùng:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            row = cur.fetchone()
    """
    conn = get_conn()
    try:
        if autocommit:
            conn.autocommit = True
        cur = conn.cursor()
        yield cur
        if not autocommit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def test_connection() -> bool:
    """Kiểm tra kết nối tới PostgreSQL. Trả về True nếu thành công."""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✅ Kết nối PostgreSQL thành công: {version['version'][:50]}")
            return True
    except Exception as e:
        print(f"❌ Lỗi kết nối PostgreSQL: {e}")
        return False


if __name__ == "__main__":
    test_connection()
