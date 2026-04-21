"""
query_classifier.py
Phân loại ý định câu hỏi người dùng thành intent + sub_intent.

Phiên bản: LLM-based (thay thế hoàn toàn keyword matching).
→ Hiểu ngữ nghĩa tự nhiên, không bị giòn bởi cách dùng từ.
→ LLM trả về structured JSON → Orchestrator dùng để route.
"""
from .llm_classifier import classify_with_llm


def classify_query(query: str, conversation_history: list | None = None) -> dict:
    """
    Phân loại câu hỏi → intent + sub_intent bằng LLM.

    Args:
        query:                Câu hỏi thô của người dùng.
        conversation_history: Lịch sử hội thoại [{role, content}] từ Streamlit session.

    Returns:
        {
            "intent":          "rag" | "tool" | "hybrid" | "greeting" | "unknown",
            "sub_intent":      str,       # sub-intent chính (phần tử đầu tiên)
            "all_sub_intents": list[str], # tất cả sub-intents detect được
            "matched_keywords": list[str] # tên sản phẩm trích xuất (compat field)
            "product_hint":    str | None # tên sản phẩm/brand nếu có
            "confidence":      str        # high | medium | low
        }
    """
    result = classify_with_llm(query, conversation_history)


    intent       = result["intent"]
    sub_intents  = result["sub_intents"]
    product_hint = result["product_hint"]
    confidence   = result["confidence"]

    # Chọn sub_intent chính (phần tử đầu tiên hoặc "unknown")
    sub_intent = sub_intents[0] if sub_intents else "unknown"

    return {
        "intent":           intent,
        "sub_intent":       sub_intent,
        "all_sub_intents":  sub_intents,
        "matched_keywords": [product_hint] if product_hint else [],  # backward compat
        "product_hint":     product_hint,
        "confidence":       confidence,
    }
