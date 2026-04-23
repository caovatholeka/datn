"""
seed.py
Script khởi tạo schema và import toàn bộ data từ JSON vào PostgreSQL.

Chạy 1 lần duy nhất khi setup lần đầu:
    python -m backend.db.seed

Script này:
  1. Đọc backend/db/schema.sql → tạo tất cả bảng
  2. Import products.json   → table: products
  3. Import price.json      → table: prices
  4. Import inventory.json  → table: inventory
  5. In báo cáo kết quả

An toàn khi chạy lại: dùng INSERT ... ON CONFLICT DO UPDATE (upsert)
"""
import os
import sys
import json

# Đảm bảo import từ thư mục gốc project
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.db.connection import get_cursor, test_connection

DATA_DIR  = os.path.join(ROOT, "data", "raw")
SCHEMA_FILE = os.path.join(ROOT, "backend", "db", "schema.sql")


# ──────────────────────────────────────────────────────────
# BƯỚC 1: Tạo schema
# ──────────────────────────────────────────────────────────

def run_schema():
    """Đọc schema.sql và thực thi để tạo tất cả bảng."""
    print("\n📋 Bước 1: Khởi tạo schema...")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    # Tách từng statement bằng ";" rồi lọc comment lines trong mỗi statement
    # (không thể filter toàn bộ stmt bằng startswith("--") vì sẽ mất CREATE TABLE)
    statements = []
    for raw in sql.split(";"):
        # Bỏ các dòng comment bên trong statement
        clean_lines = [
            line for line in raw.split("\n")
            if not line.strip().startswith("--")
        ]
        cleaned = "\n".join(clean_lines).strip()
        if cleaned:
            statements.append(cleaned)

    with get_cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)

    print("   ✅ Tạo schema thành công (products, prices, inventory, users, chat_sessions, messages)")


# ──────────────────────────────────────────────────────────
# BƯỚC 2: Import products.json
# ──────────────────────────────────────────────────────────

def seed_products():
    """Import products.json → table products (upsert)."""
    print("\n📦 Bước 2: Import sản phẩm...")
    path = os.path.join(DATA_DIR, "products.json")
    with open(path, "r", encoding="utf-8") as f:
        products = json.load(f)

    inserted = updated = 0
    with get_cursor() as cur:
        for p in products:
            cur.execute("""
                INSERT INTO products (id, name, category, brand, specs, warranty, battery, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name     = EXCLUDED.name,
                    category = EXCLUDED.category,
                    brand    = EXCLUDED.brand,
                    specs    = EXCLUDED.specs,
                    warranty = EXCLUDED.warranty,
                    battery  = EXCLUDED.battery,
                    status   = EXCLUDED.status,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted
            """, (
                p["id"],
                p["name"],
                p.get("category", ""),
                p.get("brand", ""),
                p.get("specs", ""),
                p.get("warranty", ""),
                p.get("batery", p.get("battery", "")),  # typo "batery" trong JSON gốc
                p.get("metadata", {}).get("status", "active"),
            ))
            row = cur.fetchone()
            if row and row["inserted"]:
                inserted += 1
            else:
                updated += 1

    print(f"   ✅ {inserted} sản phẩm mới | {updated} sản phẩm cập nhật | Tổng: {len(products)}")


# ──────────────────────────────────────────────────────────
# BƯỚC 3: Import price.json
# ──────────────────────────────────────────────────────────

def seed_prices():
    """Import price.json → table prices (upsert)."""
    print("\n💰 Bước 3: Import giá sản phẩm...")
    path = os.path.join(DATA_DIR, "price.json")
    with open(path, "r", encoding="utf-8") as f:
        prices = json.load(f)

    inserted = updated = 0
    with get_cursor() as cur:
        for p in prices:
            cur.execute("""
                INSERT INTO prices (product_id, price, discount)
                VALUES (%s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    price      = EXCLUDED.price,
                    discount   = EXCLUDED.discount,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted
            """, (
                p["product_id"],
                p["price"],
                p.get("discount", 0),
            ))
            row = cur.fetchone()
            if row and row["inserted"]:
                inserted += 1
            else:
                updated += 1

    print(f"   ✅ {inserted} giá mới | {updated} giá cập nhật | Tổng: {len(prices)}")


# ──────────────────────────────────────────────────────────
# BƯỚC 4: Import inventory.json
# ──────────────────────────────────────────────────────────

def seed_inventory():
    """Import inventory.json → table inventory (upsert theo product_id + warehouse)."""
    print("\n🏪 Bước 4: Import tồn kho...")
    path = os.path.join(DATA_DIR, "inventory.json")
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    skipped = inserted = updated = 0
    with get_cursor() as cur:
        # Lấy danh sách product IDs hợp lệ để kiểm tra trước
        cur.execute("SELECT id FROM products")
        valid_ids = {row["id"] for row in cur.fetchall()}

        for r in records:
            pid = r["product_id"]
            if pid not in valid_ids:
                skipped += 1
                continue  # Bỏ qua record có product_id không tồn tại

            cur.execute("""
                INSERT INTO inventory (product_id, warehouse, stock)
                VALUES (%s, %s, %s)
                ON CONFLICT (product_id, warehouse) DO UPDATE SET
                    stock      = EXCLUDED.stock,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted
            """, (
                pid,
                r.get("warehouse", "Hà Nội"),
                r.get("stock", r.get("quantity", 0)),
            ))
            row = cur.fetchone()
            if row and row["inserted"]:
                inserted += 1
            else:
                updated += 1

    msg = f"   ✅ {inserted} bản ghi mới | {updated} cập nhật | Tổng: {len(records)}"
    if skipped:
        msg += f" | ⚠️ {skipped} bỏ qua (product_id không tồn tại)"
    print(msg)



# ──────────────────────────────────────────────────────────
# BƯỚC 5: Kiểm tra kết quả
# ──────────────────────────────────────────────────────────

def verify():
    """In báo cáo số lượng records trong từng bảng."""
    print("\n📊 Bước 5: Kiểm tra kết quả...")
    tables = ["products", "prices", "inventory", "users", "chat_sessions", "messages"]
    with get_cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
            row = cur.fetchone()
            print(f"   {table:<20} → {row['cnt']:>5} records")


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  DATN Chatbot — Seed Database")
    print("=" * 55)

    # Test kết nối trước
    if not test_connection():
        print("\n❌ Không thể kết nối PostgreSQL. Kiểm tra lại .env!")
        sys.exit(1)

    try:
        run_schema()
        seed_products()
        seed_prices()
        seed_inventory()
        verify()
        print("\n✅ Seed database hoàn thành!\n")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
