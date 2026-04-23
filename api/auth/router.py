"""
auth/router.py — Đăng ký, đăng nhập, thông tin user
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from backend.db.connection import get_cursor
from api.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
from api.auth.utils import hash_password, verify_password, create_access_token
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, summary="Đăng ký tài khoản")
def register(req: RegisterRequest):
    with get_cursor() as cur:
        # Kiểm tra username đã tồn tại
        cur.execute("SELECT id FROM users WHERE username = %s", (req.username,))
        if cur.fetchone():
            raise HTTPException(400, "Username đã tồn tại")

        # Tạo user mới
        cur.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
            RETURNING id, role
            """,
            (req.username, req.email, hash_password(req.password)),
        )
        user = cur.fetchone()

    token = create_access_token({
        "user_id": str(user["id"]),
        "username": req.username,
        "role": user["role"],
    })
    return TokenResponse(access_token=token, username=req.username, role=user["role"])


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập")
def login(req: LoginRequest):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, password, role FROM users WHERE username = %s AND is_active = TRUE",
            (req.username,),
        )
        user = cur.fetchone()

    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")

    token = create_access_token({
        "user_id": str(user["id"]),
        "username": req.username,
        "role": user["role"],
    })
    return TokenResponse(access_token=token, username=req.username, role=user["role"])


@router.get("/me", response_model=UserOut, summary="Thông tin user hiện tại")
def get_me(user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, username, email, role, created_at FROM users WHERE id = %s",
            (user["user_id"],),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "User không tìm thấy")
    return UserOut(
        id=str(row["id"]),
        username=row["username"],
        email=row["email"],
        role=row["role"],
        created_at=str(row["created_at"]),
    )
