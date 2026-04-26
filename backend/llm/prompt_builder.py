"""
prompt_builder.py
Xây dựng prompt chặt chẽ từ output của Orchestrator.

Nguyên tắc thiết kế:
- Template-driven: mỗi status có template riêng → ổn định, dễ chỉnh
- Hard constraints luôn nằm trong system prompt → LLM không thể bỏ qua
- Dữ liệu được serialize trước khi chèn → LLM nhận text thuần, không JSON thô
- Deterministic: cùng input → cùng prompt structure
"""
import json
import os
from typing import Optional
from .schemas import OrchestratorOutput, PromptComponents

# Đường dẫn tới thư mục templates
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


# ============================================================
# Map status → template file name
# ============================================================
_STATUS_TO_TEMPLATE: dict[str, str] = {
    "success":            "success",
    "need_clarification": "clarification",
    "rejected":           "rejected",
    "error":              "error",
    "not_found":          "error",
    "greeting":           "greeting",   # Chào hỏi → template riêng
}


def _load_template(name: str) -> str:
    """Đọc nội dung file template. Cache-friendly (đọc một lần)."""
    path = os.path.join(_TEMPLATE_DIR, f"{name}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template không tồn tại: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_base() -> str:
    return _load_template("base")


def _serialize_data(data: dict, status: str) -> str:
    """
    Chuyển đổi dict data thành text dễ đọc cho LLM.
    Tránh để LLM nhìn thấy raw JSON keys (dễ gây confuse).
    """
    if not data:
        return "(Không có dữ liệu bổ sung)"

    lines: list[str] = []

    # ── Thông tin sản phẩm cơ bản ──────────────────────────
    if "product_name" in data:
        lines.append(f"Sản phẩm: {data['product_name']}")

    # ── Tồn kho ─────────────────────────────────────────────
    stock_info = data.get("stock_info", {})
    if stock_info and stock_info.get("status") == "success":
        stock_val = stock_info.get("stock")
        wh = stock_info.get("warehouse", "tất cả kho")
        if isinstance(stock_val, list):
            lines.append("Tồn kho theo kho:")
            for item in stock_val:
                lines.append(f"  - {item.get('warehouse', '?')}: {item.get('stock', 0)} sản phẩm")
            lines.append(f"  Tổng: {stock_info.get('total_stock', '?')} sản phẩm")
        elif isinstance(stock_val, int):
            status_txt = "còn hàng" if stock_val > 0 else "HẾT HÀNG"
            lines.append(f"Tồn kho ({wh}): {stock_val} sản phẩm — {status_txt}")

    # ── Giá cả ──────────────────────────────────────────────
    price_info = data.get("price_info", {})
    if price_info and price_info.get("status") == "success":
        price       = price_info.get("price", 0)
        discount    = price_info.get("discount", 0)
        final_price = price_info.get("final_price", price)
        currency    = price_info.get("currency", "VND")
        if discount and discount > 0:
            lines.append(f"Giá niêm yết: {price:,.0f} {currency}")
            lines.append(f"Giảm giá: {discount}%")
            lines.append(f"Giá sau giảm: {final_price:,.0f} {currency}")
        else:
            lines.append(f"Giá: {final_price:,.0f} {currency}")

    # ── RAG Context (policy, FAQ, recommendation) ───────────
    rag_context = data.get("rag_context") or data.get("context", "")
    if rag_context:
        lines.append(f"\nThông tin chính sách / tư vấn:\n{rag_context}")

    # ── Nguồn tài liệu ──────────────────────────────────────
    sources = data.get("sources", [])
    if sources:
        lines.append(f"Nguồn: {', '.join(sources)}")

    # ── Candidates (cho clarification) ───────────────────────
    candidates = data.get("candidates", [])
    if candidates:
        lines.append("Các sản phẩm tìm thấy:")
        for i, c in enumerate(candidates, 1):
            conf = c.get("confidence", 0)
            lines.append(f"  {i}. {c.get('name', '?')} (độ phù hợp: {conf:.0%})")

    # ── Tool pending (hybrid clarification) ─────────────────
    if data.get("tool_pending"):
        lines.append(f"\n[Cần bổ sung] Vui lòng cho biết rõ sản phẩm để tra cứu {data['tool_pending']}.")

    # ── Recommendation result ────────────────────────────────
    rec = data.get("recommendation", {})
    if rec and rec.get("products"):
        budget = rec.get("max_price")
        products = rec["products"]
        if budget:
            lines.append(f"\nGợi ý sản phẩm trong tầm giá dưới {budget:,.0f} VND:")
        else:
            lines.append("\nGợi ý sản phẩm phù hợp:")
        for i, p in enumerate(products, 1):
            discount = p.get("discount", 0)
            price_txt = f"{p['final_price']:,.0f} VND"
            if discount > 0:
                price_txt += f" (giảm {discount}%)"
            lines.append(f"  {i}. {p['name']} — {price_txt}")

    return "\n".join(lines) if lines else "(Không có dữ liệu cụ thể)"


def build_prompt(
    orchestrator_output: OrchestratorOutput,
    query: str = "",
) -> PromptComponents:
    """
    Xây dựng prompt hoàn chỉnh từ Orchestrator output.

    Args:
        orchestrator_output: dict từ Orchestrator.handle_query()
        query: câu hỏi gốc của người dùng (optional, nếu không có thì lấy từ message)

    Returns:
        PromptComponents chứa system_prompt, user_prompt, và template_name
    """
    status      = orchestrator_output.get("status", "error")
    data        = orchestrator_output.get("data", {})
    message     = orchestrator_output.get("message", "")

    # Chọn template dựa trên status
    template_name = _STATUS_TO_TEMPLATE.get(status, "error")
    template_body = _load_template(template_name)
    base_rules    = _load_base()

    # Serialize data thành text
    data_text = _serialize_data(data, status)

    # Điền biến vào template
    user_prompt = (
        template_body
        .replace("{{query}}",   query or message or "(không có câu hỏi)")
        .replace("{{data}}",    data_text)
        .replace("{{message}}", message)
    )

    return {
        "system_prompt":  base_rules,
        "user_prompt":    user_prompt,
        "template_name":  template_name,
    }
