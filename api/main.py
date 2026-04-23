"""
main.py — FastAPI app entry point
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth.router  import router as auth_router
from api.chat.router  import router as chat_router
from api.admin.router import router as admin_router

app = FastAPI(
    title="DATN Chatbot API",
    description="API cho Chatbot Bán Hàng Điện Tử — RAG + Tool Calling + Persistent Memory",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)

# CORS — cho phép Next.js frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "DATN Chatbot API đang chạy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    from backend.db.connection import test_connection
    db_ok = test_connection()
    return {"api": "ok", "database": "ok" if db_ok else "error"}
