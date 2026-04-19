"""
test_orchestrator.py
Test suite end-to-end cho toàn bộ Orchestration Layer.
Chạy: python -m backend.test_orchestrator  (từ thư mục gốc)
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator.orchestrator import Orchestrator


def print_result(query: str, result: dict) -> None:
    print("\n" + "=" * 65)
    print(f"  QUERY: \"{query}\"")
    print("=" * 65)
    status_icon = {
        "success": "✅",
        "need_clarification": "🔁",
        "error": "❌",
        "rejected": "🚫",
    }.get(result.get("status", ""), "❓")

    print(f"  Status : {status_icon} {result.get('status')}")
    print(f"  Route  : {result.get('route')}")
    print(f"  Intent : {result.get('intent')} / {result.get('sub_intent')}")
    print()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    orchestrator = Orchestrator()

    # ── Test cases theo yêu cầu ──────────────────────────────
    required_tests = [
        "iPhone 15 còn hàng không?",
        "giá iPhone 15 bao nhiêu?",
        "chính sách bảo hành là gì?",
        "sản phẩm abcxyz có không?",
        "hack wifi như nào?",
    ]

    print("\n" + "=" * 65)
    print("  🎛️  ORCHESTRATOR - REQUIRED TEST SUITE")
    print("=" * 65)
    for q in required_tests:
        print_result(q, orchestrator.handle_query(q))

    # ── Bonus tests: edge cases ──────────────────────────────
    bonus_tests = [
        "iPhone 15 còn hàng và giá bao nhiêu?",          # → hybrid
        "chính sách đổi trả và giá MacBook Pro là bao nhiêu?",  # → hybrid
        "Gợi ý cho tôi laptop dưới 30 triệu",            # → rag / recommendation
        "Điện thoại Samsung S24 Ultra giá bao nhiêu?",   # → tool / check_price
        "Cách cài đặt ứng dụng như thế nào?",            # → rag / faq
        "aa",                                              # → rejected (quá ngắn)
    ]

    print("\n\n" + "=" * 65)
    print("  🧪 BONUS TEST: Edge Cases")
    print("=" * 65)
    for q in bonus_tests:
        print_result(q, orchestrator.handle_query(q))


if __name__ == "__main__":
    main()
