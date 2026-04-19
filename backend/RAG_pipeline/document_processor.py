def convert_product_to_text(product: dict) -> str:
    """Biến đổi dictionary của một product thành chuỗi văn bản tự nhiên."""
    parts = []
    if product.get('name'):
        parts.append(f"Tên sản phẩm: {product['name']}")
    if product.get('category'):
        parts.append(f"Danh mục: {product['category']}")
    if product.get('brand'):
        parts.append(f"Thương hiệu: {product['brand']}")
    if product.get('price'):
        parts.append(f"Giá bán: {product['price']} VNĐ")
    if product.get('stock') is not None:
        parts.append(f"Tồn kho: {product['stock']}")
    if product.get('specs'):
        parts.append(f"Cấu hình nổi bật: {product['specs']}")
    if product.get('warranty'):
        parts.append(f"Bảo hành: {product['warranty']}")
        
    return "\n".join(parts)

def process_documents(raw_data: dict) -> list:
    """
    2. Biến đổi dữ liệu thô thành list document chuẩn cho RAG:
    [{"text": "...", "metadata": {...}}]
    """
    documents = []
    
    # A. Convert product -> text
    for prod in raw_data.get("products", []):
        text = convert_product_to_text(prod)
        metadata = {
            "source": "products",
            "type": "product",
            "id": prod.get("id", ""),
            "name": prod.get("name", "")
        }
        documents.append({
            "text": text,
            "metadata": metadata
        })
        
    # B. Convert policy / faq -> document thô nguyên khối
    policy_text = raw_data.get("policy", "")
    if policy_text.strip():
        documents.append({
            "text": policy_text,
            "metadata": {"source": "policy", "type": "policy"}
        })
        
    faq_text = raw_data.get("faq", "")
    if faq_text.strip():
        documents.append({
            "text": faq_text,
            "metadata": {"source": "faq", "type": "faq"}
        })
        
    return documents
