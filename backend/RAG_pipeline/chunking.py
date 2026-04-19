def chunk_text(documents: list) -> list:
    """
    3. Chia text thành các chunk nhỏ hơn tùy theo logic của từng loại tài liệu.
    Output là mảng chunks chuẩn: [{"text": "...", "metadata": {...}}]
    """
    chunks = []
    
    for doc in documents:
        doc_type = doc["metadata"].get("type", "")
        text = doc["text"]
        base_metadata = doc["metadata"]
        
        if doc_type == "product":
            # Product -> 1 chunk không cắt đôi để tránh mất ngữ cảnh thông số
            chunks.append({
                "text": text,
                "metadata": base_metadata.copy()
            })
            
        elif doc_type in ["policy", "faq"]:
            # Policy & FAQ -> chia theo đoạn hoặc rule (dấu \n\n)
            blocks = text.split("\n\n")
            for i, block in enumerate(blocks):
                block = block.strip()
                if not block:
                    continue
                
                meta_chunk = base_metadata.copy()
                meta_chunk["chunk_id"] = i
                
                chunks.append({
                    "text": block,
                    "metadata": meta_chunk
                })
        else:
            chunks.append(doc)
            
    return chunks
