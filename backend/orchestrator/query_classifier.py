"""
query_classifier.py
Phân loại ý định câu hỏi người dùng thành intent + sub_intent.
Rule-based, không cần LLM, dễ mở rộng bằng cách thêm keyword vào dict.
"""
from typing import Literal

# ============================================================
# BẢNG TỪ KHÓA - chỉnh sửa nơi này để thêm domain mới
# ============================================================
_KEYWORD_MAP: dict[str, list[str]] = {
    # Tool intents
    "check_price": [
        "giá", "bao nhiêu tiền", "giá bán", "price", "cost",
        "bao nhiêu", "khuyến mãi", "discount", "giảm giá", "ưu đãi",
        "flash sale", "promotion", "giá niêm yết", "định giá",
    ],
    "check_stock": [
        "còn hàng", "tồn kho", "còn không", "hết hàng", "có sẵn",
        "kho", "in stock", "available", "stock", "còn máy",
        "nhập hàng", "bao giờ có", "còn bán", "có hàng không",
    ],

    # RAG intents
    "policy": [
        "chính sách", "bảo hành", "đổi trả", "quy định", "điều khoản",
        "warranty", "return", "refund", "guarantee", "policy",
        "điều kiện", "cam kết", "hỗ trợ", "dịch vụ sau bán",
    ],
    "product_info": [
        "thông số", "cấu hình", "tính năng", "đặc điểm", "chip",
        "màn hình", "camera", "pin", "dung lượng", "ram", "rom",
        "specs", "feature", "specification", "review", "đánh giá",
        "so sánh", "tốt không", "mạnh không", "dùng tốt không",
    ],
    "recommendation": [
        "gợi ý", "đề xuất", "phù hợp", "nên mua", "tư vấn",
        "cần mua", "recommend", "suggest", "loại nào", "cái nào",
        "sản phẩm nào", "máy nào", "dưới", "trong tầm giá", "tầm tiền",
        "phù hợp với", "dành cho",
    ],
    "faq": [
        "câu hỏi", "faq", "hỏi đáp", "thắc mắc", "hỗ trợ kỹ thuật",
        "cách dùng", "hướng dẫn", "làm sao", "như thế nào", "setup",
        "cài đặt", "kết nối", "sửa chữa",
    ],
}

# Map sub_intent → routing intent (tool / rag)
_ROUTE_MAP: dict[str, Literal["tool", "rag"]] = {
    "check_price":   "tool",
    "check_stock":   "tool",
    "policy":        "rag",
    "product_info":  "rag",
    "recommendation":"rag",
    "faq":           "rag",
}


def classify_query(query: str) -> dict:
    """
    Phân loại câu hỏi → intent + sub_intent.

    Returns:
        {
            "intent":     "rag" | "tool" | "hybrid" | "unknown",
            "sub_intent": "check_stock" | "check_price" | "policy"
                          | "product_info" | "recommendation" | "faq" | "unknown",
            "matched_keywords": list[str]   # debug info
        }
    """
    q = query.lower()
    hits: dict[str, list[str]] = {}  # sub_intent → list matched keywords

    for sub_intent, keywords in _KEYWORD_MAP.items():
        matched = [kw for kw in keywords if kw in q]
        if matched:
            hits[sub_intent] = matched

    if not hits:
        return {"intent": "unknown", "sub_intent": "unknown", "all_sub_intents": [], "matched_keywords": []}

    # Tìm sub_intent có nhiều keyword match nhất
    best_sub = max(hits, key=lambda k: len(hits[k]))

    # Nếu match cả tool lẫn rag → hybrid
    route_types = {_ROUTE_MAP[si] for si in hits}
    if len(route_types) > 1:
        intent = "hybrid"
    else:
        intent = _ROUTE_MAP.get(best_sub, "unknown")

    all_matched = [kw for kws in hits.values() for kw in kws]
    return {
        "intent": intent,
        "sub_intent": best_sub,
        "all_sub_intents": list(hits.keys()),  # Tất cả sub_intents detect được
        "matched_keywords": all_matched,
    }
