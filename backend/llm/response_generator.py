"""
response_generator.py
LLM Adapter + Response Generator.

Tách biệt hoàn toàn:
  - call_llm()          → LLM Adapter (dễ swap: OpenAI / local / mock)
  - generate_response() → Pipeline orchestration
  - _format_final()     → Post-processing (trim, clean)

LLM KHÔNG được:
  - Quyết định route
  - Tự suy đoán product_id
  - Thêm thông tin ngoài data được cấp

LLM CHỈ được:
  - Render text tự nhiên từ dữ liệu đã được cung cấp
"""
import os
from dotenv import load_dotenv
from .prompt_builder import build_prompt
from .schemas import OrchestratorOutput, LLMResponse

# Tải env key
load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    ".env"
))


# ============================================================
# LLM ADAPTER - Thay thế hàm này để đổi provider
# ============================================================

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    LLM Adapter - gọi API thật.
    Hiện tại dùng OpenAI GPT. Thay thế để dùng provider khác.

    Returns:
        Câu trả lời text thuần từ LLM.
    """
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        completion = client.chat.completions.create(
            model="gpt-4o-mini",          # Nhanh + rẻ, đủ chất lượng cho chatbot bán hàng
            temperature=0.3,              # Thấp → ít sáng tác, bám sát dữ liệu hơn
            max_tokens=600,               # Giới hạn độ dài phản hồi
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )
        return completion.choices[0].message.content.strip()

    except ImportError:
        return _call_llm_mock(system_prompt, user_prompt)

    except Exception as e:
        # Nếu API lỗi → dùng fallback text thay vì crash
        return f"[LLM Error] Không thể kết nối LLM: {str(e)}"


def _call_llm_mock(system_prompt: str, user_prompt: str) -> str:
    """
    Mock LLM - dùng khi không có OpenAI key hoặc khi test offline.
    Trả về prompt thô để debug, đủ thông tin để verify logic.
    """
    return (
        "[MOCK LLM - Chưa kết nối API thật]\n\n"
        "---- SYSTEM PROMPT ----\n"
        f"{system_prompt}\n\n"
        "---- USER PROMPT ----\n"
        f"{user_prompt}"
    )


# ============================================================
# RESPONSE GENERATOR - Pipeline chính
# ============================================================

def generate_response(
    orchestrator_output: OrchestratorOutput,
    query: str = "",
    debug: bool = False,
) -> LLMResponse:
    """
    Pipeline hoàn chỉnh: Orchestrator JSON → LLM Text.

    Args:
        orchestrator_output: Kết quả từ Orchestrator.handle_query()
        query:               Câu hỏi gốc của người dùng
        debug:               Nếu True → include prompt trong output

    Returns:
        LLMResponse {text, status, prompt}
    """
    status = orchestrator_output.get("status", "error")

    # 1. Build prompt từ structured data
    prompt_components = build_prompt(orchestrator_output, query=query)
    system_prompt     = prompt_components["system_prompt"]
    user_prompt       = prompt_components["user_prompt"]
    template_name     = prompt_components["template_name"]

    # 2. Gọi LLM để render text tự nhiên
    raw_text = call_llm(system_prompt, user_prompt)

    # 3. Post-processing nhẹ: trim whitespace, xóa artifact
    final_text = _clean_response(raw_text)

    full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}" if debug else ""

    return {
        "text":   final_text,
        "status": status,
        "prompt": full_prompt,
    }


def _clean_response(text: str) -> str:
    """
    Dọn dẹp output của LLM:
    - Xóa các cụm từ hệ thống bị lộ
    - Trim whitespace thừa
    """
    # Xóa các marker hệ thống nếu LLM vô tình nhắc đến
    forbidden_phrases = [
        "json", "schema", "orchestrator", "pipeline",
        "tool calling", "rag pipeline", "product_id",
        "status:", "intent:", "sub_intent:",
    ]
    text_lower = text.lower()
    for phrase in forbidden_phrases:
        if phrase in text_lower:
            # Không xóa (quá aggressive), chỉ log warning
            pass  # TODO: log warning nếu cần

    return text.strip()
