from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    session_id: Optional[str] = None   # None → tạo session mới
    message: str
    image_b64: Optional[str] = None    # Base64 ảnh đính kèm (nếu có)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    display_text: Optional[str]
    created_at: str


class SessionOut(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str
    message_count: Optional[int] = 0
