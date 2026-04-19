"""
test_llm.py
Test suite end-to-end cho LLM Response Layer.
Chạy: python -m backend.test_llm

Kiểm tra 5 scenario:
  1. RAG success (policy)
  2. Tool success (price + stock)
  3. need_clarification (multiple candidates)
  4. rejected (off-topic / hack)
  5. error (fallback)

Nếu có OPENAI_API_KEY → gọi thật.
Nếu không có → dùng Mock để kiểm tra prompt structure.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.response_generator import generate_response

# ============================================================
# Test fixtures - mock output từ Orchestrator
# ============================================================

FIXTURES = [
    # ── 1. RAG SUCCESS: Chính sách bảo hành ───────────────────
    {
        "query": "Tư vấn cho mình laptop làm đồ họa dưới 40 triệu.",
        "orchestrator_output": {
            "status":     "success",
            "intent":     "rag",
            "sub_intent": "recommendation",
            "route":      "rag",
            "data": {
                "context": (
                    "Laptop đồ họa dưới 40 triệu bán chạy: MacBook Pro 14 M3, Asus ROG Zephyrus G14, Dell XPS 15. "
                    "Đặc điểm chung: Màn hình chuẩn màu 100% sRGB, RAM tối thiểu 16GB, có card đồ họa rời. "
                    "Khuyến mãi tháng này: Tặng kèm chuột không dây và balo chống sốc."
                ),
                "sources": ["buying_guide.txt"],
            },
            "message": "Thông tin tư vấn laptop đồ họa.",
        },
    },

    # ── 7. TOOL SUCCESS: Kiểm tra tồn kho (Hết hàng) ──────────
    {
        "query": "Samsung Galaxy S23 Ultra còn hàng không?",
        "orchestrator_output": {
            "status":     "success",
            "intent":     "tool",
            "sub_intent": "check_stock",
            "route":      "tool",
            "data": {
                "product_name": "Samsung Galaxy S23 Ultra 256GB",
                "product_id":   "PROD-099",
                "stock_info": {
                    "status":      "success",
                    "product_id":  "PROD-099",
                    "warehouse":   "Tất cả kho",
                    "stock":       [],
                    "total_stock": 0,
                },
            },
            "message": "Sản phẩm hiện đã hết hàng trên toàn hệ thống.",
        },
    },

    # ── 8. HYBRID SUCCESS: Giá (Tool) + Trả góp (RAG) ─────────
    {
        "query": "Báo giá MacBook Air M2 và chính sách trả góp?",
        "orchestrator_output": {
            "status":     "success",
            "intent":     "hybrid",
            "sub_intent": "check_price",
            "route":      "hybrid",
            "data": {
                "product_name": "MacBook Air M2 8GB/256GB",
                "product_id":   "PROD-045",
                "price_info": {
                    "status":      "success",
                    "product_id":  "PROD-045",
                    "price":       24990000,
                    "discount":    10,
                    "final_price": 22491000,
                    "currency":    "VND",
                },
                "rag_context": (
                    "Chính sách trả góp: Hỗ trợ trả góp 0% lãi suất qua thẻ tín dụng của 24 ngân hàng. "
                    "Hỗ trợ trả góp qua công ty tài chính (Home Credit, HD Saison) với thủ tục chỉ cần CCCD, duyệt hồ sơ trong 15 phút."
                )
            },
            "message": "Thông tin giá và chính sách trả góp MacBook Air M2.",
        },
    },

    # ── 9. ERROR / NOT FOUND: Không kinh doanh sản phẩm ───────
    {
        "query": "Shop có bán điện thoại Nokia đập đá cục gạch không?",
        "orchestrator_output": {
            "status":     "error",
            "intent":     "tool",
            "sub_intent": "check_stock",
            "route":      "tool",
            "data":       {},
            "message":    "Không tìm thấy sản phẩm Nokia đập đá trong cơ sở dữ liệu. Có thể cửa hàng không kinh doanh.",
        },
    },

    # ── 5. GREETING: Câu chào hỏi ──────────────────────────────
    {
        "query": "Chào shop",
        "orchestrator_output": {
            "status":     "greeting",
            "intent":     "greeting",
            "sub_intent": "greeting",
            "route":      "direct",
            "data":       {},
            "message":    "Chào shop",
        },
    },
]


def run_tests(debug: bool = False):
    sep = "=" * 65

    print(f"\n{sep}")
    print("  🤖 LLM RESPONSE LAYER - TEST SUITE")
    print(sep)

    for i, fixture in enumerate(FIXTURES, 1):
        query  = fixture["query"]
        output = fixture["orchestrator_output"]
        status = output["status"]

        status_icon = {
            "success":           "✅",
            "need_clarification":"🔁",
            "rejected":          "🚫",
            "error":             "❌",
        }.get(status, "❓")

        print(f"\n{sep}")
        print(f"  TEST {i}: [{status_icon} {status.upper()}]")
        print(f"  Query: \"{query}\"")
        print(sep)

        response = generate_response(output, query=query, debug=debug)

        print(f"\n💬 LLM Response:\n")
        print(response["text"])

        if debug and response["prompt"]:
            print(f"\n--- DEBUG PROMPT ---\n{response['prompt'][:500]}...")

        print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="In cả prompt để debug")
    args = parser.parse_args()
    run_tests(debug=args.debug)
