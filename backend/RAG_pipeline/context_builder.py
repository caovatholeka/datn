def build_context(top_docs: list) -> str:
    """
    7. Context Builder - Điểm rơi nối ráp dữ liệu
    Ghép nội dung các chunks thành một cụm text lớn format chuẩn 
    nhằm gửi làm Prompt trực tiếp cho LLM.
    """
    if not top_docs:
        return "Không có thông tin hữu ích được tìm thấy."
        
    context_parts = []
    
    for i, doc in enumerate(top_docs, start=1):
        source = doc['metadata'].get('source', 'Unknown')
        doc_type = doc['metadata'].get('type', 'Unknown')
        text = doc['text']
        
        context_parts.append(f"--- Thông tin {i} (Nguồn: {source} | Loại: {doc_type}) ---")
        context_parts.append(text)
    
    return "\n".join(context_parts)
