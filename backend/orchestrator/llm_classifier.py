"""
llm_classifier.py
LLM-based Intent Classifier thay thế hoàn toàn cho keyword matching.

Nhiệm vụ: Nhận câu hỏi thô của người dùng → gọi LLM → trả về structured intent JSON.
LLM chỉ quyết định NHÃN intent, không đụng đến data hay routing logic.

Output schema:
{
    "intent":       "tool" | "rag" | "hybrid" | "greeting" | "unknown",
    "sub_intents":  ["check_price", "check_stock", "product_info", ...],
    "product_hint": "tên sản phẩm trích xuất được nếu có, hoặc null",
    "confidence":   "high" | "medium" | "low"
}
"""
import os
import json
import openai
from dotenv import load_dotenv

# Load .env từ thư mục gốc dự án
load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    ".env"
))

# ============================================================
# SYSTEM PROMPT cho LLM Classifier
# Prompt được thiết kế chặt chẽ: output PHẢI là JSON hợp lệ
# ============================================================
_CLASSIFIER_SYSTEM_PROMPT = """\
Bạn là bộ phân loại ý định (intent classifier) cho hệ thống chatbot bán hàng điện tử.
Nhiệm vụ: Phân tích câu hỏi của khách và trả về JSON phân loại ý định.

=== NGỮ CẢNH HỘI THOẠI ===
Bạn có thể nhận được lịch sử hội thoại (các tin nhắn trước) để hiểu ngữ cảnh.
- Nếu câu hỏi hiện tại mơ hồ (ví dụ: "còn tồn kho không?", "thế còn máy kia?"), hãy dùng
  ngữ cảnh từ lịch sử để xác định sản phẩm/chủ đề đang được nói đến.
- Điền product_hint bằng sản phẩm suy luận được từ ngữ cảnh nếu người dùng không nêu rõ.
- Câu ngắn như "còn không?", "giá sao?", "thế còn iphone thì?" đều phải được phân loại
  dựa trên ngữ cảnh, KHÔNG trả về unknown.

=== CÁC INTENT CÓ THỂ PHÂN LOẠI ===

NHÓM TOOL (cần tra cứu dữ liệu real-time từ hệ thống):
  - check_price   : hỏi giá, khuyến mãi, giảm giá, tiền, bao nhiêu
  - check_stock   : hỏi tồn kho, còn hàng không, có máy không, còn bao nhiêu

NHÓM RAG (cần tra cứu tài liệu/kiến thức):
  - product_info  : hỏi thông số kỹ thuật, cấu hình, tính năng, đánh giá, so sánh
  - policy        : hỏi chính sách bảo hành, đổi trả, quy định mua hàng
  - recommendation: xin tư vấn, gợi ý sản phẩm phù hợp
  - faq           : câu hỏi thường gặp khác liên quan đến mua sắm

NHÓM ĐẶC BIỆT:
  - greeting      : chào hỏi, cảm ơn, tạm biệt, mở đầu/kết thúc cuộc trò chuyện
  - unknown       : hoàn toàn không liên quan đến cửa hàng điện tử (thời tiết, chính trị...)

=== QUY TẮC PHÂN LOẠI ===
- intent = "tool"    nếu chỉ có check_price HOẶC check_stock
- intent = "rag"     nếu chỉ có product_info, policy, recommendation, hoặc faq
- intent = "hybrid"  nếu có cả TOOL intent lẫn RAG intent
- intent = "greeting" nếu câu là lời chào/cảm ơn/tạm biệt
- intent = "unknown" CHỈ khi câu hoàn toàn không liên quan đến mua sắm điện tử

=== FORMAT OUTPUT BẮT BUỘC === (chỉ JSON thuần, không markdown, không giải thích)
{
  "intent": "<tool|rag|hybrid|greeting|unknown>",
  "sub_intents": ["<danh sách các sub-intent detect được>"],
  "product_hint": "<tên sản phẩm/thương hiệu nếu có hoặc suy luận được từ ngữ cảnh, null nếu không>",
  "confidence": "<high|medium|low>"
}

=== VÍ DỤ (KHÔNG có ngữ cảnh) ===
Input: "xiaomi 14 pro giá bao nhiêu?"
Output: {"intent":"tool","sub_intents":["check_price"],"product_hint":"Xiaomi 14 Pro","confidence":"high"}

Input: "có điện thoại xiaomi không?"
Output: {"intent":"tool","sub_intents":["check_stock"],"product_hint":"Xiaomi","confidence":"high"}

Input: "xiaomi 14 pro"
Output: {"intent":"rag","sub_intents":["product_info"],"product_hint":"Xiaomi 14 Pro","confidence":"medium"}

Input: "chính sách bảo hành của shop như thế nào?"
Output: {"intent":"rag","sub_intents":["policy"],"product_hint":null,"confidence":"high"}

Input: "xin chào shop"
Output: {"intent":"greeting","sub_intents":[],"product_hint":null,"confidence":"high"}

Input: "thời tiết hôm nay thế nào?"
Output: {"intent":"unknown","sub_intents":[],"product_hint":null,"confidence":"high"}

Input: "iphone 15 pro max còn hàng không và giá bao nhiêu?"
Output: {"intent":"hybrid","sub_intents":["check_stock","check_price"],"product_hint":"iPhone 15 Pro Max","confidence":"high"}

=== VÍ DỤ (CÓ ngữ cảnh hội thoại - follow-up questions) ===
[Lịch sử: user hỏi "xiaomi 14 pro giá bao nhiêu?" → bot trả lời giá]
Input follow-up: "còn tồn kho không?"
Output: {"intent":"tool","sub_intents":["check_stock"],"product_hint":"Xiaomi 14 Pro","confidence":"high"}

[Lịch sử: đang nói về Samsung Galaxy S25]
Input follow-up: "thế còn iphone 16 thì sao?"
Output: {"intent":"tool","sub_intents":["check_price"],"product_hint":"iPhone 16","confidence":"high"}

[Lịch sử: đang so sánh 2 máy A và B]
Input follow-up: "so sánh hai máy đó đi"
Output: {"intent":"rag","sub_intents":["product_info"],"product_hint":"<tên 2 máy từ ngữ cảnh>","confidence":"medium"}
"""


# ============================================================
# FALLBACK: Khi LLM không khả dụng, trả về unknown (không crash)
# ============================================================
_FALLBACK_RESULT = {
    "intent": "unknown",
    "sub_intents": [],
    "product_hint": None,
    "confidence": "low",
}


def classify_with_llm(query: str, conversation_history: list | None = None) -> dict:
    """
    Gọi LLM để phân loại ý định câu hỏi, có tính đến lịch sử hội thoại.

    Args:
        query:                Câu hỏi thô hiện tại của người dùng.
        conversation_history: Danh sách các turn trước [{"role": ..., "content": ...}]
                              Lấy từ Streamlit session_state.messages.
                              Nếu None hoặc rỗng, phân loại độc lập.

    Returns:
        {
            "intent":       str,        # tool | rag | hybrid | greeting | unknown
            "sub_intents":  list[str],  # danh sách sub-intent detect được
            "product_hint": str | None, # tên sản phẩm trích xuất nếu có
            "confidence":   str,        # high | medium | low
        }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _FALLBACK_RESULT.copy()

    try:
        client = openai.OpenAI(api_key=api_key)

        # Xây dựng danh sách messages gửi lên OpenAI
        messages = [{"role": "system", "content": _CLASSIFIER_SYSTEM_PROMPT}]

        # Chèn lịch sử hội thoại (tối đa 6 messages = 3 lượt trao đổi gần nhất)
        # Đủ để LLM hiểu ngữ cảnh nhưng không tốn quá nhiều token
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({
                    "role":    msg["role"],
                    "content": msg["content"],
                })

        # Thêm câu hỏi hiện tại
        messages.append({"role": "user", "content": query})

        # Gọi OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=150,
            response_format={"type": "json_object"},
            messages=messages,
        )

        raw = response.choices[0].message.content.strip()

        result = json.loads(raw)

        # Validate và normalize fields
        return {
            "intent":       result.get("intent", "unknown"),
            "sub_intents":  result.get("sub_intents", []),
            "product_hint": result.get("product_hint", None),
            "confidence":   result.get("confidence", "medium"),
        }

    except (json.JSONDecodeError, KeyError):
        # LLM trả về JSON không hợp lệ → fallback
        return _FALLBACK_RESULT.copy()

    except Exception:
        # Lỗi mạng, API key hết hạn, v.v. → fallback thay vì crash
        return _FALLBACK_RESULT.copy()
