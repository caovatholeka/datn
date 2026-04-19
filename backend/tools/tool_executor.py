"""
10. tool_executor.py
Bộ điều phối trung tâm - orchestration layer.
Kết hợp Intent Router + Product Resolver + Business Tools thành một luồng xử lý hoàn chỉnh.
"""
from ..router.intent_router import detect_intent
from ..tools.tool_registry import TOOLS


class ToolExecutor:
    """
    Điều phối toàn bộ luồng Tool Calling:
    1. Detect intent
    2. Resolve product_id
    3. Gọi tool nghiệp vụ phù hợp
    4. Tổng hợp và trả về kết quả chuẩn hóa
    """

    def execute(self, query: str) -> dict:
        """
        Entry point duy nhất - nhận query thô, trả về kết quả có cấu trúc.
        
        Returns:
            {
                "status": "success" | "need_clarification" | "error",
                "intent": str,
                "data": dict,
                "message": str
            }
        """
        try:
            # ---- BƯỚC 1: Phát hiện ý định ----
            intent = detect_intent(query)

            # ---- BƯỚC 2: Phân giải sản phẩm (luôn chạy trước) ----
            resolver = TOOLS["resolve_product"]
            resolve_result = resolver.run(query=query)

            # ---- BƯỚC 3: Xử lý kết quả phân giải ----
            if resolve_result["status"] == "not_found":
                return {
                    "status": "not_found",
                    "intent": intent,
                    "data": {},
                    "message": resolve_result.get("message", "Không tìm thấy sản phẩm.")
                }

            if resolve_result["status"] == "multiple":
                # Yêu cầu người dùng làm rõ sản phẩm
                return {
                    "status": "need_clarification",
                    "intent": intent,
                    "data": {
                        "candidates": resolve_result.get("candidates", [])
                    },
                    "message": resolve_result.get("message", "Tìm thấy nhiều sản phẩm phù hợp, vui lòng chỉ định rõ hơn.")
                }

            # Resolve thành công
            product_id: str = resolve_result["product_id"]
            product_name: str = resolve_result["name"]
            combined_data: dict = {
                "product_id": product_id,
                "product_name": product_name,
                "intent": intent,
            }

            # ---- BƯỚC 4: Gọi tool nghiệp vụ theo intent ----
            if intent == "unknown":
                # Không có intent rõ ràng: trả về info sản phẩm cơ bản
                return {
                    "status": "success",
                    "intent": intent,
                    "data": combined_data,
                    "message": f"Đã xác định sản phẩm '{product_name}' nhưng không rõ bạn muốn hỏi gì. Bạn muốn hỏi giá hay tồn kho?"
                }

            if intent in ("check_stock", "check_stock_and_price"):
                stock_result = TOOLS["get_stock"].run(product_id=product_id)
                combined_data["stock_info"] = stock_result

            if intent in ("check_price", "check_stock_and_price"):
                price_result = TOOLS["get_price_and_promo"].run(product_id=product_id)
                combined_data["price_info"] = price_result

            # ---- BƯỚC 5: Tổng hợp message phản hồi ----
            message = self._build_message(intent, product_name, combined_data)

            return {
                "status": "success",
                "intent": intent,
                "data": combined_data,
                "message": message
            }

        except Exception as e:
            return {
                "status": "error",
                "intent": "unknown",
                "data": {},
                "message": f"Lỗi hệ thống không mong đợi: {str(e)}"
            }

    def _build_message(self, intent: str, product_name: str, data: dict) -> str:
        """Xây dựng câu trả lời tự nhiên từ kết quả của các tools."""
        parts = [f"Sản phẩm: {product_name}"]

        stock_info = data.get("stock_info", {})
        price_info = data.get("price_info", {})

        if stock_info.get("status") == "success":
            total = stock_info.get("total_stock", stock_info.get("stock"))
            if isinstance(total, int):
                if total > 0:
                    parts.append(f"Tồn kho: {total} sản phẩm có sẵn.")
                else:
                    parts.append("Tồn kho: Hết hàng.")
            elif isinstance(total, list):
                breakdown = ", ".join(
                    f"{r['warehouse']}: {r['stock']}" for r in total
                )
                parts.append(f"Tồn kho theo kho: {breakdown}.")
        elif stock_info:
            parts.append(f"Tồn kho: {stock_info.get('message', 'Không có thông tin.')}")

        if price_info.get("status") == "success":
            price = price_info.get("price", 0)
            discount = price_info.get("discount", 0)
            final = price_info.get("final_price", price)
            currency = price_info.get("currency", "VND")
            if discount > 0:
                parts.append(
                    f"Giá: {price:,.0f} {currency} (giảm {discount}%) → "
                    f"Giá cuối: {final:,.0f} {currency}."
                )
            else:
                parts.append(f"Giá: {final:,.0f} {currency}.")
        elif price_info:
            parts.append(f"Giá: {price_info.get('message', 'Không có thông tin.')}")

        return " | ".join(parts)
