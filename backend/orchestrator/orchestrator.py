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
from ..RAG_pipeline import VectorDBManager, retrieve, rerank, build_context

# Đường dẫn gốc dự án (datn/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# RAG PIPELINE - Gọi ChromaDB thật qua VectorDBManager
# ============================================================
def _call_rag_pipeline(query: str, sub_intent: str) -> dict:
    """
    Gọi RAG pipeline thật: retrieve → rerank → build_context.
    """
    try:
        # Quan trọng: Tạo DB Instance mới mỗi lần gọi để tránh lỗi Threading của Streamlit với SQLite
        db = VectorDBManager(_BASE_DIR)

        # Retrieve top-k chunks từ ChromaDB (có metadata filtering bên trong)
        docs = retrieve(query, db, top_k=5)

        if not docs:
            return {
                "status": "success",
                "context": "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu.",
                "sources": [],
            }

        # Rerank bằng FlashRank AI để lấy chunk liên quan nhất
        reranked = rerank(query, docs)

        # Ghép context từ các chunk đã rerank
        context = build_context(reranked)

        # Thu thập danh sách nguồn tài liệu (dedup)
        sources = list({
            d["metadata"].get("source", "unknown")
            for d in reranked
            if d.get("metadata")
        })

        return {
            "status": "success",
            "context": context,
            "sources": sources,
        }

    except Exception as e:
        return {
            "status": "error",
            "context": "",
            "sources": [],
            "message": f"Lỗi RAG pipeline: {str(e)}",
        }


class Orchestrator:
    """
    Lớp điều phối trung tâm của hệ thống chatbot.
    Inject ToolExecutor và RAG caller qua constructor để dễ unit-test.
    """

    def __init__(self, tool_executor: ToolExecutor | None = None):
        self._tool_executor = tool_executor or ToolExecutor()

    def handle_query(self, query: str, conversation_history: list | None = None) -> dict:
        """
        Entry point duy nhất – nhận query thô, trả về output có cấu trúc.

        Args:
            query:                Câu hỏi hiện tại.
            conversation_history: Lịch sử hội thoại [{role, content}] từ Streamlit.
                                  Dùng để LLM hiểu ngữ cảnh câu trước.

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
            # BƯỚC 2: Classify Query (LLM-based)
            # ────────────────────────────────────────────────
            classification = classify_query(query, conversation_history)
            intent        = classification["intent"]
            sub_intent    = classification["sub_intent"]
            all_subs      = set(classification.get("all_sub_intents", [sub_intent]))
            # product_hint: tên sản phẩm LLM trích xuất được từ ngữ cảnh hội thoại
            # Dùng làm fallback khi query thô không chứa tên sản phẩm (vd: "còn hàng không?")
            product_hint  = classification.get("product_hint")

            # Greeting được LLM detect → trả về ngay
            if intent == "greeting":
                return self._build_output(
                    status="greeting",
                    intent="greeting",
                    sub_intent="greeting",
                    route="direct",
                    data={},
                    message=query,
                )

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
                tool_result = self._execute_tool(query, list(all_subs), product_hint)
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
                # ── Đặc biệt: recommendation → ưu tiên gọi tool trước ──────────
                if "recommendation" in all_subs:
                    from ..tools.recommendation_tool import get_recommendations
                    # Lấy giá sản phẩm tham chiếu nếu có product_hint
                    ref_price = None
                    if product_hint:
                        try:
                            from ..tools.tool_registry import TOOLS
                            resolver = TOOLS["resolve_product"]
                            r = resolver.run(query=product_hint)
                            if r.get("status") == "found":
                                from ..tools.tool_registry import TOOLS as T2
                                pr = T2["get_price_and_promo"].run(product_id=r["product_id"])
                                if pr.get("status") == "success":
                                    ref_price = pr.get("final_price")
                        except Exception:
                            pass

                    rec_result = get_recommendations(query, reference_price=ref_price)

                    if rec_result.get("status") == "success" and rec_result.get("products"):
                        return self._build_output(
                            status="success",
                            intent=intent, sub_intent="recommendation", route=route,
                            data={"recommendation": rec_result},
                            message="recommendation_result",
                        )

                # ── RAG thông thường ─────────────────────────────────────────────
                rag_result = _call_rag_pipeline(query, sub_intent)

                # Nếu RAG đã báo lỗi thực sự bên dưới (như OpenAI auth error), ném thẳng ra
                if rag_result.get("status") == "error":
                    return self._build_output(
                        status="error",
                        intent=intent, sub_intent=sub_intent, route=route,
                        data={}, message=rag_result.get("message", "Lỗi ẩn trong RAG"),
                    )

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
                    tool_result  = self._execute_tool(query, list(all_subs), product_hint)
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

    def _execute_tool(
        self,
        query: str,
        sub_intents: list | None = None,
        product_hint: str | None = None,
    ) -> dict:
        """Wrapper gọi ToolExecutor và chuẩn hóa output."""
        return self._tool_executor.execute(query, sub_intents=sub_intents, product_hint=product_hint)

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
