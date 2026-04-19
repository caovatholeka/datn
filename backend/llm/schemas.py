"""
schemas.py
Định nghĩa TypedDict cho input/output của LLM Layer.
Cung cấp type safety và auto-completion.
"""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class OrchestratorOutput(TypedDict, total=False):
    """Output schema từ Orchestrator - input vào LLM Layer."""
    status:     str                # "success" | "need_clarification" | "rejected" | "error" | "not_found"
    intent:     str                # "tool" | "rag" | "hybrid" | "unknown"
    sub_intent: str                # "check_price" | "check_stock" | "policy" | ...
    route:      str                # "tool" | "rag" | "hybrid" | "reject"
    data:       Dict[str, Any]     # Dữ liệu nghiệp vụ (stock_info, price_info, context, candidates...)
    message:    str                # Thông điệp tóm tắt từ orchestrator


class LLMResponse(TypedDict):
    """Output schema từ LLM Layer trả về cho client."""
    text:   str    # Câu trả lời tự nhiên bằng tiếng Việt
    status: str    # Mirror từ OrchestratorOutput.status
    prompt: str    # Prompt đã build (dùng cho debug/logging)


class PromptComponents(TypedDict):
    """Các thành phần được build trước khi gộp thành final prompt."""
    system_prompt:  str    # BASE RULES (invariant)
    user_prompt:    str    # Template đã điền biến
    template_name:  str    # Tên template đã dùng ("success", "clarification", ...)
