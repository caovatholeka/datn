"""
safety_guard.py
Bộ lọc an toàn: chặn câu hỏi ngoài phạm vi hệ thống bán hàng.
Chạy trước tất cả các xử lý khác trong pipeline.
"""

# ============================================================
# BLACKLIST DOMAINS - các chủ đề hoàn toàn cấm
# ============================================================
_BLOCKED_TOPICS: list[str] = [
    # An ninh mạng / hack
    "hack", "crack", "exploit", "sql injection", "xss", "ddos",
    "brute force", "keylogger", "malware", "virus", "phishing",
    "bypass", "reverse engineer", "decompile",

    # Chính trị / nhạy cảm
    "chính trị", "đảng", "bầu cử", "biểu tình", "chiến tranh",
    "vũ khí", "bom", "khủng bố", "ma túy",

    # Nội dung người lớn / không phù hợp
    "sex", "khiêu dâm", "18+", "casino", "cờ bạc", "lừa đảo",
    "scam", "gian lận",

    # Câu hỏi cá nhân/không liên quan
    "bạch tuộc", "thời tiết hôm nay", "tử vi", "xem bói",
    "nấu ăn", "côn trùng",
]

# ============================================================
# WHITELIST SIGNALS - đảm bảo câu có từ liên quan shop không bị block
# ============================================================
_DOMAIN_SIGNALS: list[str] = [
    # Thiết bị điện tử
    "iphone", "samsung", "laptop", "macbook", "điện thoại", "máy tính",
    "tablet", "ipad", "android", "ios", "xiaomi", "oppo", "vivo",
    # Hành động mua bán
    "mua", "bán", "giá", "tồn kho", "hàng", "kho", "bảo hành", "đổi trả",
    "sản phẩm", "thiết bị", "máy", "cấu hình", "specs",
]

# Nếu query quá ngắn và không có tín hiệu domain → coi là off-topic
_MIN_QUERY_LENGTH = 3


def is_safe_query(query: str) -> tuple[bool, str]:
    """
    Kiểm tra query có an toàn và trong phạm vi hệ thống không.

    Returns:
        (True, "") nếu an toàn
        (False, reason) nếu bị chặn, kèm lý do
    """
    q = query.lower().strip()

    # 1. Quá ngắn → từ chối
    if len(q.split()) < _MIN_QUERY_LENGTH:
        return False, "Câu hỏi quá ngắn. Vui lòng cung cấp thêm thông tin."

    # 2. Kiểm tra blacklist - chặn nếu có từ khóa cấm
    for blocked in _BLOCKED_TOPICS:
        if blocked in q:
            return False, (
                f"Câu hỏi của bạn không thuộc phạm vi hỗ trợ của hệ thống. "
                f"Tôi chỉ có thể tư vấn về sản phẩm điện tử và dịch vụ mua sắm."
            )

    # 3. Câu hỏi không có tín hiệu domain nào → có thể off-topic
    # Tuy nhiên không block cứng vì người dùng có thể hỏi bằng nhiều cách
    # → Để Orchestrator xử lý qua "unknown" intent thay vì block ngay
    return True, ""
