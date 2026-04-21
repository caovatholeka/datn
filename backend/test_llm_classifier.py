import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator.llm_classifier import classify_with_llm

tests = [
    "có điện thoại xiaomi không?",
    "xiaomi 14 pro",
    "xiaomi 14 pro giá bao nhiêu",
    "xin chào shop",
    "chính sách bảo hành như thế nào?",
    "thời tiết hôm nay thế nào?",
    "iphone 15 pro max còn hàng không và giá bao nhiêu?",
]

print("--- LLM Classifier Test ---")
for q in tests:
    r = classify_with_llm(q)
    print(f"Query : {q}")
    print(f"Result: intent={r['intent']} | subs={r['sub_intents']} | hint={r['product_hint']} | conf={r['confidence']}")
    print()
