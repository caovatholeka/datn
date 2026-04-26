"""
main.py — FastAPI app entry point
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from api.auth.router  import router as auth_router
from api.chat.router  import router as chat_router
from api.admin.router import router as admin_router

app = FastAPI(
    title="DATN Chatbot API",
    description="API cho Chatbot Bán Hàng Điện Tử — RAG + Tool Calling + Persistent Memory",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — cho phép tất cả origins trong môi trường dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler — lộ lỗi thật khi debug
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
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
