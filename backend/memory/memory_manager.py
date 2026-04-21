"""
memory_manager.py
Quản lý bộ nhớ hội thoại theo chiến lược "Summary Buffer Window".

Chiến lược:
  - Giữ nguyên 6 messages gần nhất (= 3 lượt trao đổi) trong bộ nhớ ngắn hạn.
  - Sau mỗi 10 messages (= 5 lượt), tóm tắt phần cũ hơn thành 1-2 câu bằng LLM.
  - Kết hợp [summary + recent window] làm ngữ cảnh truyền cho LLM Classifier.

Tại sao tách thành module riêng?
  - Không phụ thuộc Streamlit → dễ dàng tái sử dụng bởi FastAPI, Flask, CLI, hay bất kỳ
    frontend/API nào sau này.
  - Frontend chỉ cần lưu 2 biến: messages (list) và summary (str), rồi
    truyền vào MemoryManager để nhận context chuẩn hóa.
"""
import os
import openai
from dotenv import load_dotenv

load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    ".env"
))

# ============================================================
# CONSTANTS
# ============================================================
WINDOW_SIZE      = 8   # 4 lượt Q&A đầy đủ — đủ để không bị hổng trước khi summary kịp tạo
SUMMARIZE_EVERY  = 10  # Cứ mỗi 10 messages (5 lượt) thì cập nhật summary


class MemoryManager:
    """
    Quản lý bộ nhớ hội thoại theo dạng "Summary + Rolling Window".

    Cách dùng (ở bất kỳ frontend nào):
        manager = MemoryManager()

        # Sau mỗi lượt:
        if manager.should_summarize(messages):
            summary = manager.summarize(messages, old_summary)

        # Khi cần gọi Orchestrator:
        context = manager.build_context(messages, summary)
        orchestrator.handle_query(query, conversation_history=context)
    """

    def build_context(self, messages: list, summary: str = "") -> list:
        """
        Xây dựng danh sách ngữ cảnh để truyền cho LLM Classifier.

        Cấu trúc output:
          [summary_message (nếu có)] + [6 messages gần nhất]

        Args:
            messages: Toàn bộ lịch sử hội thoại [{role, content}, ...]
            summary:  Chuỗi tóm tắt của các lượt cũ hơn

        Returns:
            Danh sách messages chuẩn hóa để truyền vào conversation_history.
        """
        # Lấy window gần nhất (tối đa WINDOW_SIZE messages)
        recent = messages[-WINDOW_SIZE:] if len(messages) > WINDOW_SIZE else messages[:]

        context: list = []

        # Chèn summary vào đầu nếu có (dùng role="assistant" để tương thích OpenAI API)
        if summary and summary.strip():
            context.append({
                "role":    "assistant",
                "content": f"[Tóm tắt cuộc trò chuyện trước]: {summary}",
            })

        context.extend(recent)
        return context

    def should_summarize(self, messages: list) -> bool:
        """
        Kiểm tra xem đã đến lúc tạo/cập nhật summary chưa.
        Trigger sau mỗi SUMMARIZE_EVERY messages (cả user lẫn assistant).

        Args:
            messages: Toàn bộ lịch sử sau khi đã thêm câu trả lời bot mới nhất.
        """
        n = len(messages)
        return n > 0 and n % SUMMARIZE_EVERY == 0

    def summarize(self, messages: list, existing_summary: str = "") -> str:
        """
        Gọi LLM để tóm tắt phần lịch sử cũ thành 1-2 câu ngắn gọn.

        Chỉ tóm tắt phần NGOÀI window gần nhất (phần cũ hơn WINDOW_SIZE messages).
        Nếu đã có summary từ trước, LLM sẽ cập nhật/merge vào.

        Args:
            messages:         Toàn bộ lịch sử hội thoại.
            existing_summary: Summary cũ (nếu đã có từ lần trước).

        Returns:
            Chuỗi tóm tắt 1-2 câu bằng tiếng Việt.
            Trả về existing_summary nếu có lỗi (không bao giờ mất summary cũ).
        """
        # Chỉ tóm tắt phần cũ hơn window gần nhất
        old_messages = messages[:-WINDOW_SIZE] if len(messages) > WINDOW_SIZE else []

        # Nếu không có gì để tóm tắt → giữ nguyên summary cũ
        if not old_messages and not existing_summary:
            return ""
        if not old_messages:
            return existing_summary

        # Format chuỗi hội thoại để LLM đọc
        history_text = "\n".join(
            f"{'Khách' if m['role'] == 'user' else 'Bot'}: {m['content']}"
            for m in old_messages
        )

        existing_ctx = f"\nTóm tắt trước đó: {existing_summary}" if existing_summary else ""

        prompt = (
            f"Tóm tắt cuộc trò chuyện mua sắm sau thành 1-2 câu ngắn bằng tiếng Việt.\n"
            f"Tập trung vào: sản phẩm đã nhắc đến, thông tin quan trọng (giá, tồn kho, "
            f"chính sách), và mục tiêu của khách hàng.{existing_ctx}\n\n"
            f"Cuộc trò chuyện:\n{history_text}\n\nTóm tắt:"
        )

        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return existing_summary

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=120,   # 1-2 câu ngắn là đủ
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()

        except Exception:
            # Lỗi API → giữ nguyên summary cũ, không crash
            return existing_summary
