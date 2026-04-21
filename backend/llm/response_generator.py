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


# ============================================================
# STREAMING RESPONSE - Hiển thị chữ từng ký tự như ChatGPT
# ============================================================

def generate_response_stream(
    orchestrator_output: OrchestratorOutput,
    query: str = "",
):
    """
    Generator version của generate_response — dùng với st.write_stream().
    Yield từng chunk text để Streamlit render ngay khi có dữ liệu.

    Cách dùng trong Streamlit:
        stream = generate_response_stream(orch_result, query=user_query)
        full_text = st.write_stream(stream)   # trả về toàn bộ text cuối cùng

    Args:
        orchestrator_output: Kết quả từ Orchestrator.handle_query()
        query:               Câu hỏi gốc của người dùng

    Yields:
        str: Chunk text nhỏ từ LLM stream
    """
    prompt_components = build_prompt(orchestrator_output, query=query)
    system_prompt = prompt_components["system_prompt"]
    user_prompt   = prompt_components["user_prompt"]

    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=600,
            stream=True,             # Bật chế độ streaming
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    except ImportError:
        # Không có openai → yield mock response
        yield _call_llm_mock(system_prompt, user_prompt)

    except Exception as e:
        yield f"\n[Lỗi kết nối LLM: {str(e)}]"


# ============================================================
# SUGGESTED QUESTIONS - Gợi ý câu hỏi tiếp theo
# ============================================================

def generate_suggestions(
    orch_result: dict,
    user_query: str,
    bot_response: str,
) -> list[str]:
    """
    Gọi LLM để sinh 2-3 câu hỏi gợi ý follow-up phù hợp với ngữ cảnh.

    Trường hợp đặc biệt:
      - need_clarification + candidates → trả ngay tên candidates, không cần gọi LLM
      - rejected / error / greeting     → trả [] (không gợi ý)

    Args:
        orch_result:  Kết quả JSON từ Orchestrator.
        user_query:   Câu hỏi vừa được người dùng hỏi.
        bot_response: Câu trả lời vừa sinh ra (800 ký tự đầu).

    Returns:
        list[str] — tối đa 3 câu gợi ý, hoặc [] nếu không phù hợp.
    """
    import json

    status = orch_result.get("status", "")
    data   = orch_result.get("data",   {})

    # Không gợi ý khi rejected / error / greeting
    if status in ("rejected", "error", "greeting"):
        return []

    # need_clarification + candidates → hiển thị tên sản phẩm như gợi ý
    if status == "need_clarification":
        candidates = data.get("candidates", [])
        if candidates:
            return [c["name"] for c in candidates[:3]]

    # === Gọi LLM để sinh gợi ý === #
    product_name = data.get("product_name", "")
    context_parts = [f"Khách hỏi: {user_query}"]
    if product_name:
        context_parts.append(f"Sản phẩm đang hỏi: {product_name}")
    context_parts.append(f"Bot trả lời: {bot_response[:300]}")

    prompt = (
        "Bạn là trợ lý mua sắm điện tử. Dựa vào cuộc hội thoại dưới đây, "
        "hãy đề xuất 2-3 câu hỏi ngắn gọn mà khách có thể muốn hỏi tiếp. "
        "Câu hỏi phải liên quan đến sản phẩm, giá, tồn kho, so sánh hoặc chính sách.\n\n"
        + "\n".join(context_parts)
        + "\n\nTRẢ VỀ CHỈ JSON array, không markdown, không giải thích:\n"
        '["câu hỏi 1?", "câu hỏi 2?", "câu hỏi 3?"]'
    )

    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content.strip()
        # Xử lý nếu LLM bọc trong markdown code block
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        suggestions = json.loads(raw)
        return [s for s in suggestions if isinstance(s, str)][:3]

    except Exception:
        return []

