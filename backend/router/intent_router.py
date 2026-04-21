"""
intent_router.py
Bộ định tuyến ý định - quyết định tool nào sẽ được gọi bên trong ToolExecutor.

Phiên bản: LLM-based (thay thế keyword matching).
Dùng lại classify_with_llm() để tránh gọi LLM 2 lần.

Lưu ý: Orchestrator đã gọi classify_query() ở Bước 2 và truyền intent vào
ToolExecutor qua luồng. Tuy nhiên, ToolExecutor gọi detect_intent() độc lập.
→ Giữ nguyên signature detect_intent() để không phá vỡ ToolExecutor.
"""
from ..orchestrator.llm_classifier import classify_with_llm


def detect_intent(query: str) -> str:
    """
    Phát hiện sub-intent chi tiết dành cho ToolExecutor.
    Ánh xạ sub_intents từ LLM → intent string mà ToolExecutor hiểu.

    Returns:
        "check_stock"           - Chỉ hỏi tồn kho
        "check_price"           - Chỉ hỏi giá / khuyến mãi
        "check_stock_and_price" - Hỏi cả hai
        "product_search"        - Hỏi sản phẩm có tồn tại
        "unknown"               - Không rõ
    """
    result = classify_with_llm(query)
    sub_intents = set(result.get("sub_intents", []))

    has_stock = "check_stock" in sub_intents
    has_price = "check_price" in sub_intents

    if has_stock and has_price:
        return "check_stock_and_price"
    if has_stock:
        return "check_stock"
    if has_price:
        return "check_price"

    # product_info từ RAG → trong context này là "tìm sản phẩm"
    if "product_info" in sub_intents:
        return "product_search"

    return "unknown"
