import sys; sys.path.insert(0,'.')
from backend.orchestrator.safety_guard import is_safe_query
from backend.orchestrator.llm_classifier import classify_with_llm

# Mô phỏng đúng cuộc trò chuyện trong ảnh
history = [
    {'role': 'user',      'content': 'co iphone 12 khong'},
    {'role': 'assistant', 'content': 'Ban dang quan tam den san pham nao? Vi du: iPhone 15 128GB, iPhone 13 128GB hay OnePlus 12?'},
    {'role': 'user',      'content': 'the iphone 15 bao nhieu tien'},
    {'role': 'assistant', 'content': 'Ban dang quan tam den iPhone 15 ban nao? Vi du: iPhone 15 128GB, iPhone 15 Plus hay iPhone 15 Pro Max 256GB?'},
]

queries = ['128gb', '128GB', 'thoi', 'ura']
for q in queries:
    safe, reason = is_safe_query(q)
    if not safe:
        print(f"BLOCKED [{q}]: {reason}")
        continue
    result = classify_with_llm(q, conversation_history=history)
    print(f"[{q}] intent={result['intent']} sub={result['sub_intents']} hint={result['product_hint']}")
