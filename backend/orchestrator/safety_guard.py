"""
safety_guard.py
Bộ lọc an toàn tối giản: CHỈ chặn nội dung nguy hiểm/vi phạm pháp luật.

Triết lý thiết kế:
  - Safety guard KHÔNG phân loại intent — đó là việc của LLM Classifier.
  - Safety guard KHÔNG dựa vào độ dài hay keyword domain — dễ false positive.
  - Safety guard CHỈ chặn nội dung có thể gây hại thực sự (black list ngắn, rõ ràng).
  - Mọi thứ còn lại (off-topic, ngắn, mơ hồ) → để LLM Classifier xử lý với "unknown" intent.
"""

# ============================================================
# BLACKLIST — nội dung nguy hiểm/vi phạm, luôn chặn
# ============================================================
_BLOCKED_TOPICS: list[str] = [
    # An ninh mạng / tấn công
    "hack", "crack", "exploit", "sql injection", "xss", "ddos",
    "brute force", "keylogger", "malware", "phishing", "bypass",

    # Vũ khí / tệ nạn
    "vũ khí", "bom", "khủng bố", "ma túy", "chất nổ",

    # Nội dung người lớn / vi phạm
    "khiêu dâm", "18+", "casino", "cờ bạc", "lừa đảo", "scam",
]


def is_safe_query(query: str) -> tuple[bool, str]:
    """
    Kiểm tra query có chứa nội dung bị cấm không.

    Returns:
        (True, "")            — an toàn, cho phép đi tiếp
        (False, reason)       — bị chặn, kèm lý do

    Lưu ý:
        - Câu rỗng hoàn toàn bị chặn để tránh gọi LLM thừa.
        - Mọi trường hợp còn lại (ngắn, lạ, off-topic) đều cho qua → LLM quyết định.
    """
    q = query.strip()

    # Chặn câu rỗng hoàn toàn (không tốn LLM call)
    if not q:
        return False, "Vui lòng nhập nội dung câu hỏi."

    q_lower = q.lower()

    # Kiểm tra blacklist
    for blocked in _BLOCKED_TOPICS:
        if blocked in q_lower:
            return False, (
                "Câu hỏi của bạn không thuộc phạm vi hỗ trợ của hệ thống. "
                "Tôi chỉ tư vấn về sản phẩm điện tử và dịch vụ mua sắm."
            )

    # Mọi thứ còn lại → để AI phân tích
    return True, ""
