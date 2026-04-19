"""
test_tool_calling.py
Script kiểm thử end-to-end cho hệ thống Tool Calling.
Chạy: python -m backend.test_tool_calling  (từ thư mục gốc)
"""
import json
import sys
import os

# Thêm thư mục gốc vào path để import hoạt động
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.tool_executor import ToolExecutor


def print_result(query: str, result: dict) -> None:
    """In kết quả theo định dạng JSON có cấu trúc, dễ đọc."""
    print("\n" + "=" * 65)
    print(f"  QUERY: \"{query}\"")
    print("=" * 65)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()


def main():
    executor = ToolExecutor()

    # ---- Các test cases theo yêu cầu ----
    test_queries = [
        "Có điện thoại nào dưới 10 triệu không?",
        "Tìm cho tôi iPhone màu Titan tự nhiên",
        "iPhone 15 Pro Max kho Đà Nẵng còn không?",
        "Máy nào đang được giảm giá trên 10%?",
        "Cho tôi xem giá của cái tủ lạnh Samsung.",
    ]

    print("\n" + "=" * 65)
    print("  🔧 TOOL CALLING SYSTEM - TEST SUITE")
    print("=" * 65)

    for query in test_queries:
        result = executor.execute(query)
        print_result(query, result)

    # ---- Bonus: Test case phát hiện nhiều ứng viên ----
    print("\n" + "=" * 65)
    print("  📌 BONUS TEST: Truy vấn mơ hồ (nhiều ứng viên)")
    print("=" * 65)
    bonus_queries = [
        "ip 15 prm giá bao nhiêu?",   # → multiple candidates
        "S24 ultra còn hàng ở Hà Nội không?",            # → multiple candidates
        "Mấy con mac m3 giá thế nào?",      # → exact match
    ]
    for query in bonus_queries:
        result = executor.execute(query)
        print_result(query, result)


if __name__ == "__main__":
    main()
