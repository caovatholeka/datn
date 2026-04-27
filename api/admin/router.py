"""
admin/router.py — Quản lý sản phẩm, users, hội thoại (chỉ admin)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from backend.db.connection import get_cursor
from api.deps import require_admin
from api.admin.schemas import ProductUpdate, PriceUpdate, ProductCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


# ──────────────────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────────────────

@router.get("/users", summary="Danh sách người dùng")
def list_users(admin: dict = Depends(require_admin)):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, u.email, u.role, u.created_at, u.is_active,
                   COUNT(s.id) AS session_count
            FROM users u
            LEFT JOIN chat_sessions s ON s.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
            """
        )
        rows = cur.fetchall()
    return [
        {
            "id": str(r["id"]),
            "username": r["username"],
            "email": r["email"],
            "role": r["role"],
            "is_active": r["is_active"],
            "created_at": str(r["created_at"]),
            "session_count": r["session_count"],
        }
        for r in rows
    ]


# ──────────────────────────────────────────────────────────
# CONVERSATIONS
# ──────────────────────────────────────────────────────────

@router.get("/conversations", summary="Tất cả hội thoại")
def list_conversations(admin: dict = Depends(require_admin)):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.title, s.summary, s.created_at, s.updated_at,
                   u.username, COUNT(m.id) AS message_count
            FROM chat_sessions s
            JOIN users u ON u.id = s.user_id
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id, u.username
            ORDER BY s.updated_at DESC
            LIMIT 100
            """
        )
        rows = cur.fetchall()
    return [
        {
            "id": str(r["id"]),
            "title": r["title"],
            "summary": r["summary"],
            "username": r["username"],
            "message_count": r["message_count"],
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]),
        }
        for r in rows
    ]


@router.get("/conversations/{session_id}", summary="Chi tiết 1 hội thoại")
def get_conversation(session_id: str, admin: dict = Depends(require_admin)):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.role, m.content, m.display_text, m.created_at
            FROM messages m
            WHERE m.session_id = %s
            ORDER BY m.created_at
            """,
            (session_id,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "role": r["role"],
            "content": r["content"],
            "display_text": r["display_text"],
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


# ──────────────────────────────────────────────────────────
# PRODUCTS
# ──────────────────────────────────────────────────────────

@router.get("/products", summary="Danh sách sản phẩm")
def list_products(admin: dict = Depends(require_admin)):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.name, p.brand, p.category, p.status,
                   pr.price, pr.discount,
                   COALESCE(SUM(i.stock), 0) AS total_stock
            FROM products p
            LEFT JOIN prices pr ON pr.product_id = p.id
            LEFT JOIN inventory i ON i.product_id = p.id
            GROUP BY p.id, pr.price, pr.discount
            ORDER BY p.brand, p.name
            """
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.post("/products", summary="Thêm sản phẩm mới")
def create_product(body: ProductCreate, admin: dict = Depends(require_admin)):
    import time
    product_id = f"PROD-{int(time.time() * 1000) % 100000:05d}"
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO products (id, name, brand, category, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (product_id, body.name, body.brand, body.category, body.status),
        )
        cur.execute(
            "INSERT INTO prices (product_id, price, discount) VALUES (%s, %s, %s)",
            (product_id, body.price, body.discount or 0),
        )
    return {"created": True, "product_id": product_id}


@router.delete("/products/{product_id}", summary="Xóa sản phẩm")
def delete_product(product_id: str, admin: dict = Depends(require_admin)):
    with get_cursor() as cur:
        # Xóa theo thứ tự: inventory → prices → products
        cur.execute("DELETE FROM inventory WHERE product_id = %s", (product_id,))
        cur.execute("DELETE FROM prices WHERE product_id = %s", (product_id,))
        cur.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Sản phẩm không tồn tại")
    return {"deleted": True, "product_id": product_id}


@router.put("/products/{product_id}", summary="Cập nhật thông tin sản phẩm")
def update_product(
    product_id: str,
    body: ProductUpdate,
    admin: dict = Depends(require_admin),
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "Không có trường nào để cập nhật")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [product_id]

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE products SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING id",
            values,
        )
        if not cur.fetchone():
            raise HTTPException(404, "Sản phẩm không tồn tại")
    return {"updated": True, "product_id": product_id}


@router.put("/products/{product_id}/price", summary="Cập nhật giá sản phẩm")
def update_price(
    product_id: str,
    body: PriceUpdate,
    admin: dict = Depends(require_admin),
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "Không có trường nào để cập nhật")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [product_id]

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE prices SET {set_clause}, updated_at = NOW() WHERE product_id = %s RETURNING product_id",
            values,
        )
        if not cur.fetchone():
            raise HTTPException(404, "Giá sản phẩm không tồn tại")
    return {"updated": True, "product_id": product_id}


# ──────────────────────────────────────────────────────────
# DASHBOARD STATS
# ──────────────────────────────────────────────────────────

@router.get("/stats", summary="Thống kê tổng quan")
def get_stats(admin: dict = Depends(require_admin)):
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        total_users = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM chat_sessions")
        total_sessions = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM messages")
        total_messages = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM products")
        total_products = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM chat_sessions WHERE updated_at > NOW() - INTERVAL '24 hours'"
        )
        active_today = cur.fetchone()["cnt"]

    return {
        "total_users":    total_users,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_products": total_products,
        "active_today":   active_today,
    }
