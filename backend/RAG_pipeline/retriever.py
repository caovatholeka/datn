from .vector_db import VectorDBManager

def retrieve(query: str, vector_db_manager: VectorDBManager, top_k: int = 5) -> list:
    """
    5. Retrieval - Tìm kiếm Vector
    Input: query string, k chunks cần lấy ra.
    Output: Danh sách các chunks kèm điểm similarity score.
    """
    # Xây dựng Metadata Filtering cơ bản
    query_lower = query.lower()
    search_kwargs = {"k": top_k}
    
    # Kích hoạt Intent Detection: Nếu khách hỏi luật lệ mua hàng, chặn lấy info của máy móc để tránh nhiễu
    if any(keyword in query_lower for keyword in ["chính sách", "bảo hành", "quy định", "đổi trả"]):
        print("   -> 🔎 Đã phát hiện ý định hỏi 'Chính Sách'. Áp dụng Khóa Cứng Metadata Filtering (type=policy)...")
        search_kwargs["filter"] = {"type": "policy"}
        
    # Hàm này tự động gọi model embed truy vấn và chạy lệnh search trên vector db với search_kwargs nâng cao
    results = vector_db_manager.vectorstore.similarity_search_with_score(
        query, 
        **search_kwargs
    )
    
    retrieved_docs = []
    for doc, score in results:
        retrieved_docs.append({
            "text": doc.page_content,
            "metadata": doc.metadata,
            "score": score
        })
        
    return retrieved_docs
