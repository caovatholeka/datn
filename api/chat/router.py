"""
chat/router.py — Chat sessions + Streaming SSE
"""
import sys, os, json, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.db.connection import get_cursor
from backend.orchestrator.orchestrator import Orchestrator
from backend.llm.response_generator import generate_response_stream
from backend.memory.memory_manager import MemoryManager
from api.deps import get_current_user
from api.chat.schemas import ChatRequest, SessionOut, MessageOut

router    = APIRouter(prefix="/chat", tags=["Chat"])
_orch     = Orchestrator()   # Singleton — khởi tạo 1 lần
_memory   = MemoryManager()


# ──────────────────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    """Định dạng 1 SSE event."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ──────────────────────────────────────────────────────────
# SESSIONS
# ──────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[SessionOut], summary="Danh sách session của user")
def list_sessions(user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   COUNT(m.id) AS message_count
            FROM chat_sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            WHERE s.user_id = %s
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT 50
            """,
            (user["user_id"],),
        )
        rows = cur.fetchall()
    return [
        SessionOut(
            id=str(r["id"]),
            title=r["title"],
            created_at=str(r["created_at"]),
            updated_at=str(r["updated_at"]),
            message_count=r["message_count"],
        )
        for r in rows
    ]


@router.post("/sessions", summary="Tạo session mới (rỗng)")
def create_session(user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id",
            (user["user_id"], "Cuộc trò chuyện mới"),
        )
        row = cur.fetchone()
    return {"session_id": str(row["id"])}


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut],
            summary="Lấy messages của 1 session")
def get_messages(session_id: str, user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        # Xác nhận session thuộc user
        cur.execute(
            "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, user["user_id"]),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Session không tồn tại")

        cur.execute(
            "SELECT id, role, content, display_text, created_at FROM messages WHERE session_id = %s ORDER BY created_at",
            (session_id,),
        )
        rows = cur.fetchall()
    return [
        MessageOut(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            display_text=r["display_text"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


@router.delete("/sessions/{session_id}", summary="Xoá session")
def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s RETURNING id",
            (session_id, user["user_id"]),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Session không tồn tại hoặc không có quyền xoá")
    return {"deleted": True}


# ──────────────────────────────────────────────────────────
# STREAMING CHAT
# ──────────────────────────────────────────────────────────

@router.post("/send", summary="Gửi tin nhắn (SSE streaming)")
def send_message(req: ChatRequest, user: dict = Depends(get_current_user)):
    """
    SSE stream format:
      data: {"type": "token",   "content": "chunk text"}
      data: {"type": "done",    "session_id": "...", "full_text": "..."}
      data: {"type": "error",   "content": "error message"}
    """

    def event_stream():
        session_id = req.session_id

        try:
            # ── 1. Tạo session nếu chưa có ─────────────────
            with get_cursor() as cur:
                if not session_id:
                    title = req.message[:60] + ("..." if len(req.message) > 60 else "")
                    cur.execute(
                        "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id",
                        (user["user_id"], title),
                    )
                    session_id = str(cur.fetchone()["id"])
                else:
                    cur.execute(
                        "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
                        (session_id, user["user_id"]),
                    )
                    if not cur.fetchone():
                        yield _sse({"type": "error", "content": "Session không tồn tại"})
                        return

            # ── 2. Load lịch sử messages (window 8) ────────
            with get_cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content FROM messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 8
                    """,
                    (session_id,),
                )
                history = [
                    {"role": r["role"], "content": r["content"]}
                    for r in reversed(cur.fetchall())
                ]

            # ── 3. Load summary ─────────────────────────────
            with get_cursor() as cur:
                cur.execute(
                    "SELECT summary FROM chat_sessions WHERE id = %s", (session_id,)
                )
                row = cur.fetchone()
                summary = row["summary"] if row else ""

            # ── 4. Build context ────────────────────────────
            context = _memory.build_context(history, summary)

            # ── 5. Xử lý ảnh đính kèm (GPT-4o Vision) ──────
            pipeline_query = req.message
            if req.image_b64:
                try:
                    from openai import OpenAI
                    import os
                    _vision = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    vision_resp = _vision.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{req.image_b64}",
                                        "detail": "low"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": "Đây là ảnh sản phẩm điện tử. Hãy nhận dạng tên sản phẩm (thương hiệu, model nếu có). Chỉ trả lời tên sản phẩm, không giải thích thêm."
                                }
                            ]
                        }],
                        max_tokens=60,
                    )
                    product_name = vision_resp.choices[0].message.content.strip()
                    if product_name:
                        pipeline_query = f"[Ảnh sản phẩm: {product_name}] {req.message}"
                except Exception as e:
                    pass  # Vision thất bại → dùng text gốc

            # ── 6. Orchestrator ─────────────────────────────
            orch_result = _orch.handle_query(
                pipeline_query,
                conversation_history=context,
            )

            # ── 7. Streaming response ───────────────────────
            full_text = ""
            for chunk in generate_response_stream(orch_result, query=pipeline_query):
                full_text += chunk
                yield _sse({"type": "token", "content": chunk})

            # ── 8. Lưu messages vào PostgreSQL ─────────────
            with get_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (session_id, role, content, display_text, has_image)
                    VALUES (%s, 'user', %s, %s, %s)
                    """,
                    (session_id, pipeline_query, req.message, bool(req.image_b64)),
                )
                cur.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (%s, 'assistant', %s)",
                    (session_id, full_text),
                )
                cur.execute(
                    "UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s",
                    (session_id,),
                )

            # ── 9. Cập nhật summary nếu cần ────────────────
            all_msgs = history + [
                {"role": "user",      "content": pipeline_query},
                {"role": "assistant", "content": full_text},
            ]
            if _memory.should_summarize(all_msgs):
                new_summary = _memory.summarize(all_msgs, summary)
                with get_cursor() as cur:
                    cur.execute(
                        "UPDATE chat_sessions SET summary = %s WHERE id = %s",
                        (new_summary, session_id),
                    )

            # ── 10. Done event ──────────────────────────────
            yield _sse({"type": "done", "session_id": session_id, "full_text": full_text})

        except Exception as e:
            yield _sse({"type": "error", "content": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
