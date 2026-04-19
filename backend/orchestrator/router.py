"""
router.py
Bộ định tuyến: dựa trên classification result → quyết định dùng RAG, Tool hay Hybrid.
"""
from typing import Literal

RouteType = Literal["rag", "tool", "hybrid", "reject"]

_TOOL_SUB_INTENTS = {"check_price", "check_stock"}
_RAG_SUB_INTENTS  = {"policy", "product_info", "recommendation", "faq"}


def decide_route(classification: dict) -> RouteType:
    """
    Nhận kết quả từ query_classifier và trả về route thực thi.

    FIX: Nếu cả 2 sub_intent đều là tool-type (ví dụ check_stock + check_price)
    → Route về 'tool' và để ToolExecutor xử lý (đã hỗ trợ check_stock_and_price).
    Chỉ dùng 'hybrid' khi có ít nhất 1 RAG intent + 1 Tool intent cùng lúc.
    """
    intent:     str = classification.get("intent", "unknown")
    sub_intent: str = classification.get("sub_intent", "unknown")
    # Orchestrator gửi toàn bộ sub_intents nếu đã detect được nhiều
    all_subs: set = set(classification.get("all_sub_intents", [sub_intent]))

    if intent == "unknown" and sub_intent == "unknown":
        return "reject"

    # Nếu được đánh dấu hybrid nhưng toàn bộ là tool intents → đưa về tool
    if intent == "hybrid":
        has_tool = bool(all_subs & _TOOL_SUB_INTENTS)
        has_rag  = bool(all_subs & _RAG_SUB_INTENTS)
        if has_tool and not has_rag:
            return "tool"
        return "hybrid"

    if intent == "tool":   return "tool"
    if intent == "rag":    return "rag"

    # Fallback theo sub_intent
    _sub_to_route: dict[str, RouteType] = {
        "check_price":    "tool",
        "check_stock":    "tool",
        "policy":          "rag",
        "product_info":    "rag",
        "recommendation":  "rag",
        "faq":             "rag",
    }
    return _sub_to_route.get(sub_intent, "reject")
