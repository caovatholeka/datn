import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.orchestrator.llm_classifier import classify_with_llm

# Mô phỏng cuộc trò chuyện: sau khi hỏi giá Xiaomi 14 Pro, hỏi tiếp "còn tồn kho không?"
history = [
    {"role": "user",      "content": "xiaomi 14 pro giá bao nhiêu?"},
    {"role": "assistant", "content": "Xiaomi 14 Pro có giá 18,990,000 VND."},
]

followup_queries = [
    "còn tồn kho không?",
    "thế còn iphone 16 thì sao?",
    "so sánh hai máy đó đi",
    "cảm ơn bạn nhé",
]

print("=== Context-aware Classification Test ===\n")
print(f"[History] {history[0]['content']} → {history[1]['content']}\n")

for q in followup_queries:
    r = classify_with_llm(q, conversation_history=history)
    print(f"Follow-up: {q}")
    print(f"  intent={r['intent']} | subs={r['sub_intents']} | hint={r['product_hint']}")
    print()
    # Giả sử bot trả lời và thêm vào history
    history.append({"role": "user", "content": q})
    history.append({"role": "assistant", "content": "(bot reply)"})
