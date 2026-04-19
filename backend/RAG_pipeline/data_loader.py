import os
import json

def load_data(base_dir: str):
    """
    1. Đọc toàn bộ dữ liệu từ các file json và txt.
    Output: documents_raw = chứa items thô (raw dict/string).
    """
    data_dir = os.path.join(base_dir, "data", "raw")
    
    # Đọc products.json
    products_path = os.path.join(data_dir, "products.json")
    products = []
    if os.path.exists(products_path):
        with open(products_path, "r", encoding="utf-8") as f:
            products = json.load(f)
            
    # Đọc policy.txt
    policy_path = os.path.join(data_dir, "policy.txt")
    policy_text = ""
    if os.path.exists(policy_path):
        with open(policy_path, "r", encoding="utf-8") as f:
            policy_text = f.read()
            
    # Đọc faq.txt
    faq_path = os.path.join(data_dir, "faq.txt")
    faq_text = ""
    if os.path.exists(faq_path):
        with open(faq_path, "r", encoding="utf-8") as f:
            faq_text = f.read()
            
    return {
        "products": products,
        "policy": policy_text,
        "faq": faq_text
    }
