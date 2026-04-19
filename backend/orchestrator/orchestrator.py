"""
orchestrator.py
Lớp điều phối trung tâm (Core Orchestration Layer).
Gắn kết toàn bộ pipeline: Classify → Safety → Route → Execute → Validate → Return.

Kiến trúc luồng:
  User Query
      ↓
  [SafetyGuard]   ← Chặn query độc hại / off-topic
      ↓
  [QueryClassifier] ← intent + sub_intent
      ↓
  [Router]          ← tool | rag | hybrid | reject
      ↓
  [ToolExecutor / RAG / Both]  ← Execute
      ↓
  [Validator]       ← Kiểm tra kết quả
      ↓
  Structured Output (JSON)
"""
import sys
import os

from .query_classifier import classify_query
from .safety_guard import is_safe_query
from .router import decide_route
from .validator import validate_result, validate_rag_result
from ..tools.tool_executor import ToolExecutor


# ============================================================
# RAG STUB - Giả lập RAG pipeline cho đến khi tích hợp thật
# Khi sẵn sàng: thay thế hàm này bằng lời gọi VectorDBManager + retriever thật
# ============================================================
def _call_rag_pipeline(query: str, sub_intent: str) -> dict:
    """
    Stub giả lập RAG pipeline.
    TODO: Thay bằng:
        from RAG_pipeline import VectorDBManager, retrieve, rerank, build_context
        db = VectorDBManager(BASE_DIR)
        docs = retrieve(query, db, top_k=5)
        reranked = rerank(query, docs)
        context = build_context(reranked)
        return {"status": "success", "context": context, "sources": [...]}
    """
    # Mock data hữu ích cho các sub_intent khác nhau
    _mock_responses = {
        "policy": {
            "status": "success",
            "context": (
                "Chính sách bảo hành: Điện thoại và laptop được bảo hành từ 12 đến 24 tháng. "
                "Chính sách đổi trả: Đổi trả trong vòng 7 ngày nếu sản phẩm lỗi kỹ thuật. "
                "Hỗ trợ bảo hành chính hãng tại trung tâm hoặc cửa hàng."
            ),
            "sources": ["policy.txt"],
        },
        "product_info": {
            "status": "success",
            "context": (
                "Thông tin sản phẩm được lấy từ cơ sở dữ liệu nội bộ. "
                "Vui lòng cung cấp tên sản phẩm cụ thể để được tư vấn chi tiết hơn."
            ),
            "sources": ["products.json"],
        },
        "recommendation": {
            "status": "success",
            "context": (
                "Để gợi ý sản phẩm phù hợp, tôi cần biết thêm về nhu cầu của bạn: "
                "ngân sách, mục đích sử dụng (gaming, học tập, chụp ảnh,...), "
                "và thương hiệu ưa thích."
            ),
            "sources": ["faq.txt"],
        },
        "faq": {
            "status": "success",
            "context": (
                "Câu hỏi thường gặp: "
                "1. Thời gian giao hàng nội thành 1-2 ngày, tỉnh thành 2-5 ngày. "
                "2. Hỗ trợ COD và trả góp qua thẻ tín dụng. "
                "3. Cài đặt phần mềm miễn phí sau khi mua."
            ),
            "sources": ["faq.txt"],
        },
    }
    return _mock_responses.get(sub_intent, {
        "status": "success",
        "context": "Tôi đã tìm kiếm nhưng không tìm thấy thông tin cụ thể cho câu hỏi này.",
        "sources": [],
    })


class Orchestrator:
    """
    Lớp điều phối trung tâm của hệ thống chatbot.
    Inject ToolExecutor và RAG caller qua constructor để dễ unit-test.
    """

    # Từ khóa nhận diện lời chào - xử lý riêng thay vì reject
    _GREETING_KEYWORDS = {
        "chào", "hello", "hi", "hey", "xin chào", "good morning",
        "good evening", "alo", "ello", "ơi shop", "shop ơi",
        "cho hỏi", "tư vấn", "giúp đỡ", "hỗ trợ",
    }

    def __init__(self, tool_executor: ToolExecutor | None = None):
        self._tool_executor = tool_executor or ToolExecutor()

    def handle_query(self, query: str) -> dict:
        """
        Entry point duy nhất – nhận query thô, trả về output có cấu trúc.

        Returns:
            {
                "status":  "success" | "need_clarification" | "error" | "rejected",
                "intent":  str,
                "sub_intent": str,
                "route":   str,
                "data":    dict,
                "message": str
            }
        """
        try:
            # ────────────────────────────────────────────────
            # BƯỚC 0: Greeting Detection (trước mọi thứ khác)
            # ────────────────────────────────────────────────
            q_lower = query.lower().strip()
            if self._is_greeting(q_lower):
                return self._build_output(
                    status="greeting",
                    intent="greeting",
                    sub_intent="greeting",
                    route="direct",
                    data={},
                    message=query,
                )

            # ────────────────────────────────────────────────
            # BƯỚC 1: Safety Check
            # ────────────────────────────────────────────────
            is_safe, reject_reason = is_safe_query(query)
            if not is_safe:
                return self._build_output(
                    status="rejected",
                    intent="unknown",
                    sub_intent="unknown",
                    route="reject",
                    data={},
                    message=reject_reason,
                )

            # ────────────────────────────────────────────────
            # BƯỚC 2: Classify Query
            # ────────────────────────────────────────────────
            classification = classify_query(query)
            intent      = classification["intent"]
            sub_intent  = classification["sub_intent"]
            all_subs    = set(classification.get("all_sub_intents", [sub_intent]))

            # ────────────────────────────────────────────────
            # BƯỚC 3: Decide Route
            # ────────────────────────────────────────────────
            route = decide_route(classification)

            if route == "reject":
                return self._build_output(
                    status="rejected",
                    intent=intent,
                    sub_intent=sub_intent,
                    route=route,
                    data={},
                    message=(
                        "Câu hỏi của bạn chưa đủ rõ ràng hoặc không thuộc phạm vi "
                        "hỗ trợ (giá, tồn kho, chính sách, tư vấn sản phẩm điện tử). "
                        "Bạn muốn hỏi về điều gì?"
                    ),
                )

            # ────────────────────────────────────────────────
            # BƯỚC 4: Execute theo Route
            # ────────────────────────────────────────────────
            combined_data: dict = {}
            final_message = ""

            if route == "tool":
                tool_result = self._execute_tool(query)
                is_valid, reason = validate_result(tool_result)

                if not is_valid:
                    return self._build_output(
                        status="error",
                        intent=intent, sub_intent=sub_intent, route=route,
                        data={}, message=reason,
                    )

                # Đặc biệt: need_clarification → trả thẳng
                if tool_result.get("status") == "need_clarification":
                    return self._build_output(
                        status="need_clarification",
                        intent=intent, sub_intent=sub_intent, route=route,
                        data=tool_result.get("data", {}),
                        message=tool_result.get("message", ""),
                    )

                # not_found: không xác định được sản phẩm → need_clarification thay vì error
                # (error chỉ dùng khi lỗi kỹ thuật thực sự)
                if tool_result.get("status") == "not_found":
                    return self._build_output(
                        status="need_clarification",
                        intent=intent, sub_intent=sub_intent, route=route,
                        data={"suggestion": "Vui lòng cung cấp tên sản phẩm cụ thể hơn."},
                        message=tool_result.get("message", "Không tìm thấy sản phẩm."),
                    )

                combined_data = tool_result.get("data", {})
                final_message = tool_result.get("message", "")

            elif route == "rag":
                rag_result = _call_rag_pipeline(query, sub_intent)
                is_valid, reason = validate_rag_result(rag_result.get("context", ""))

                if not is_valid:
                    return self._build_output(
                        status="error",
                        intent=intent, sub_intent=sub_intent, route=route,
                        data={}, message=reason,
                    )

                combined_data = {
                    "context":  rag_result.get("context", ""),
                    "sources":  rag_result.get("sources", []),
                }
                final_message = rag_result.get("context", "")

            elif route == "hybrid":
                # Tách riêng rag_sub và tool_sub từ all_sub_intents
                _TOOL_SUBS = {"check_price", "check_stock"}
                _RAG_SUBS  = {"policy", "product_info", "recommendation", "faq"}
                rag_sub  = next((s for s in all_subs if s in _RAG_SUBS), sub_intent)
                tool_sub = next((s for s in all_subs if s in _TOOL_SUBS), None)

                # RAG luôn chạy trước và luôn có kết quả (policy/faq luôn có trong DB)
                rag_result  = _call_rag_pipeline(query, rag_sub)
                rag_context = rag_result.get("context", "")

                if tool_sub:
                    tool_result  = self._execute_tool(query)
                    tool_status  = tool_result.get("status")
                    tool_data    = tool_result.get("data", {})
                    tool_msg     = tool_result.get("message", "")

                    if tool_status == "need_clarification":
                        # Tool cần clarify nhưng RAG đã có nội dung → trả cả 2
                        combined_data = {
                            "rag_context":  rag_context,
                            "sources":      rag_result.get("sources", []),
                            "tool_pending": tool_sub,
                            "candidates":   tool_data.get("candidates", []),
                        }
                        final_message = (
                            f"{rag_context}\n\n"
                            f"[Cần thêm thông tin] Để tra cứu {tool_sub}, "
                            f"vui lòng chỉ rõ sản phẩm: {tool_msg}"
                        )
                        return self._build_output(
                            status="need_clarification",
                            intent=intent, sub_intent=sub_intent, route=route,
                            data=combined_data, message=final_message,
                        )
                    else:
                        # Tool thành công → merge cả 2 kết quả
                        combined_data = {
                            **tool_data,
                            "rag_context": rag_context,
                            "sources":     rag_result.get("sources", []),
                        }
                        tool_msg_part = tool_msg.strip() + "\n\n" if tool_msg.strip() else ""
                        final_message = f"{tool_msg_part}Thông tin chính sách: {rag_context}"
                else:
                    # Chỉ có RAG, không có tool sub_intent
                    combined_data = {
                        "rag_context": rag_context,
                        "sources":     rag_result.get("sources", []),
                    }
                    final_message = rag_context

            # ────────────────────────────────────────────────
            # BƯỚC 5: Validate Output cuối
            # ────────────────────────────────────────────────
            final_result = {
                "status": "success",
                "data":   combined_data,
                "message": final_message,
            }
            is_valid, reason = validate_result(final_result)
            if not is_valid:
                return self._build_output(
                    status="error",
                    intent=intent, sub_intent=sub_intent, route=route,
                    data={}, message=reason,
                )

            return self._build_output(
                status="success",
                intent=intent, sub_intent=sub_intent, route=route,
                data=combined_data, message=final_message,
            )

        except Exception as e:
            return self._build_output(
                status="error",
                intent="unknown", sub_intent="unknown", route="unknown",
                data={},
                message=f"Lỗi hệ thống không mong đợi: {str(e)}",
            )

    def _is_greeting(self, q_lower: str) -> bool:
        """Kiểm tra câu có phải lời chào/mở đầu cuộc hội thoại không."""
        return any(kw in q_lower for kw in self._GREETING_KEYWORDS)

    def _execute_tool(self, query: str) -> dict:
        """Wrapper gọi ToolExecutor và chuẩn hóa output."""
        return self._tool_executor.execute(query)

    @staticmethod
    def _build_output(
        status: str,
        intent: str,
        sub_intent: str,
        route: str,
        data: dict,
        message: str,
    ) -> dict:
        """Chuẩn hóa output theo schema thống nhất."""
        return {
            "status":     status,
            "intent":     intent,
            "sub_intent": sub_intent,
            "route":      route,
            "data":       data,
            "message":    message,
        }
