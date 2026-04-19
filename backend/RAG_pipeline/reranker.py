from flashrank import Ranker, RerankRequest

# Biến lưu trữ global để giữ Model trong Memory (tránh load lại lâu)
_global_ranker = None

def get_ranker():
    global _global_ranker
    if _global_ranker is None:
        print("   -> Bật FlashRank AI Model (Mất một chút thời gian để load model ở lần chạy đầu tiên)...")
        # Sử dụng model siêu nhẹ mặc định của FlashRank dựa trên Onnx
        _global_ranker = Ranker()
    return _global_ranker

def rerank(query: str, retrieved_docs: list) -> list:
    """
    6. Reranking áp dụng sức mạnh của nguyên lý Nơ-ron bằng FlashRank AI.
    Không dùng Khoảng cách, ta dùng AI phân tích câu đối thoại trực tiếp để đánh điểm Score.
    """
    if not retrieved_docs:
        return []
        
    # Chuẩn bị format array chuẩn để nạp vào API của bảng xếp hạng FlashRank
    passages = []
    for i, doc in enumerate(retrieved_docs):
        passages.append({
            "id": i,
            "text": doc["text"],
            "meta": doc["metadata"]
        })
        
    # Cấu hình Rerank Request
    rerank_request = RerankRequest(query=query, passages=passages)
    
    # Thực thi chấm điểm chéo bằng model Mchine Learning cực mạnh
    ranker = get_ranker()
    flashrank_results = ranker.rerank(rerank_request)
    
    # Lấy dữ liệu và map ngược trở về cấu trúc doc nguyên bản của Pipeline chúng ta
    final_docs = []
    for res in flashrank_results:
        final_docs.append({
            "text": res["text"],
            "metadata": res["meta"],
            "score": res["score"] # Điểm từ Model ML, càng chạy từ 0 đến khoảng 1.0 (càng cao càng tốt)
        })
        
    return final_docs
