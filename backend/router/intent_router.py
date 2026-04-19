"""
9. intent_router.py
Bộ định tuyến ý định dựa trên keyword matching.
Phân loại câu hỏi → quyết định tools nào cần được gọi.
"""


# Từ điển từ khóa định nghĩa mỗi ý định
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "check_stock": [
        "còn hàng", "tồn kho", "còn không", "còn bao nhiêu", "hết hàng",
        "có sẵn", "kho", "in stock", "available", "stock", "có hàng không",
        "còn máy", "nhập hàng", "bao giờ có"
    ],
    "check_price": [
        "giá", "bao nhiêu tiền", "giá bán", "giá bao nhiêu", "bao nhiêu",
        "price", "cost", "mua giá", "khuyến mãi", "discount", "giảm giá",
        "ưu đãi", "flash sale", "promotion", "tiền"
    ],
    "product_search": [
        "có không", "tìm", "tìm kiếm", "có bán", "mua", "muốn mua",
        "search", "bán không", "có sản phẩm", "có máy", "sản phẩm nào",
    ],
}

_STOCK_KW = set(_INTENT_KEYWORDS["check_stock"])
_PRICE_KW = set(_INTENT_KEYWORDS["check_price"])
_SEARCH_KW = set(_INTENT_KEYWORDS["product_search"])


def detect_intent(query: str) -> str:
    """
    Phân tích ý định của câu hỏi.

    Returns:
        "check_stock"           - Chỉ hỏi về tồn kho.
        "check_price"           - Chỉ hỏi về giá / khuyến mãi.
        "check_stock_and_price" - Hỏi cả tồn kho lẫn giá.
        "product_search"        - Hỏi sản phẩm có tồn tại hay không.
        "unknown"               - Không rõ ý định.
    """
    q = query.lower()
    has_stock = any(kw in q for kw in _STOCK_KW)
    has_price = any(kw in q for kw in _PRICE_KW)
    has_search = any(kw in q for kw in _SEARCH_KW)

    if has_stock and has_price:
        return "check_stock_and_price"
    if has_stock:
        return "check_stock"
    if has_price:
        return "check_price"
    if has_search:
        return "product_search"
    return "unknown"
