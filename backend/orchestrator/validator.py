"""
validator.py
Kiểm tra tính hợp lệ của kết quả trước khi trả về người dùng.
Đảm bảo output không rỗng, không có lỗi ẩn, đủ độ tin cậy.
"""

# Ngưỡng confidence tối thiểu để chấp nhận kết quả Tool Calling
_MIN_CONFIDENCE_THRESHOLD = 0.35


def validate_result(result: dict) -> tuple[bool, str]:
    """
    Kiểm tra kết quả từ Tool Executor hoặc RAG Pipeline.

    Args:
        result: dict kết quả từ tool_executor hoặc rag pipeline

    Returns:
        (True, "")         nếu kết quả hợp lệ
        (False, reason)    nếu có vấn đề, kèm lý do cụ thể
    """
    if not isinstance(result, dict):
        return False, "Kết quả không phải là dictionary hợp lệ."

    status = result.get("status", "")

    # 1. Kiểm tra status rõ ràng là lỗi
    if status in ("error",):
        msg = result.get("message", "Có lỗi xảy ra trong quá trình xử lý.")
        return False, f"Tool/RAG trả về lỗi: {msg}"

    # 2. Kiểm tra kết quả cần làm rõ - vẫn hợp lệ nhưng cần xử lý đặc biệt
    if status == "need_clarification":
        return True, ""  # Hợp lệ, orchestrator sẽ xử lý clarification

    # 3. Kiểm tra data rỗng
    data = result.get("data", {})
    if status == "success" and not data:
        return False, "Kết quả trả về rỗng dù status là success."

    # 4. Kiểm tra confidence nếu có
    if "confidence" in result:
        confidence = result.get("confidence")
        if confidence is not None and isinstance(confidence, (int, float)):
            if confidence < _MIN_CONFIDENCE_THRESHOLD:
                return False, (
                    f"Độ tin cậy kết quả ({confidence:.2f}) thấp hơn ngưỡng "
                    f"cho phép ({_MIN_CONFIDENCE_THRESHOLD})."
                )

    # 5. Kiểm tra nested data có tool errors
    if isinstance(data, dict):
        stock_info = data.get("stock_info", {})
        price_info = data.get("price_info", {})
        if stock_info.get("status") == "error" and price_info.get("status") == "error":
            return False, "Cả stock và price đều báo lỗi."

    return True, ""


def validate_rag_result(context: str) -> tuple[bool, str]:
    """
    Kiểm tra kết quả từ RAG Pipeline (context string).

    Returns:
        (True, "")         nếu context có nội dung
        (False, reason)    nếu context rỗng hoặc không hữu ích
    """
    if not context or not context.strip():
        return False, "RAG Pipeline không trả về thông tin hữu ích nào."

    if len(context.strip()) < 20:
        return False, "Context RAG quá ngắn, có thể không đủ thông tin."

    return True, ""
