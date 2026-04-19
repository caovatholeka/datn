import os
from RAG_pipeline import (
    load_data, 
    process_documents, 
    chunk_text, 
    VectorDBManager,
    retrieve, 
    rerank, 
    build_context
)

def build_index(base_dir: str):
    print("--- 1. Data Loader ---")
    raw_data = load_data(base_dir)
    print(f"Loaded: {len(raw_data['products'])} products, policy length: {len(raw_data['policy'])}, faq length: {len(raw_data['faq'])}")
    
    print("\n--- 2. Document Processor ---")
    documents = process_documents(raw_data)
    print(f"Processed into {len(documents)} core documents.")
    
    print("\n--- 3. Chunking ---")
    chunks = chunk_text(documents)
    print(f"Chunked into {len(chunks)} fragments.")
    
    print("\n--- 4. Embedding & Indexing ---")
    db_manager = VectorDBManager(base_dir)
    db_manager.embed_and_index(chunks)
    print("Indexing complete.")
    
    return db_manager

def test_search(base_dir: str, db_manager: VectorDBManager, query: str):
    print(f"\n--- TESTING QUERY: '{query}' ---")
    
    print("--- 5. Retrieval ---")
    top_docs = retrieve(query, db_manager, top_k=5)
    print(f"Retrieved {len(top_docs)} docs.")
    
    print("--- 6. Reranking ---")
    reranked_docs = rerank(query, top_docs)
    for i, doc in enumerate(reranked_docs):
        print(f"Top {i+1} Score (FlashRank AI): {doc['score']:.4f} | Thuộc loại: {doc['metadata'].get('type')}")
        
    print("--- 7. Context Builder ---")
    context = build_context(reranked_docs)
    
    print("\nFINAL CONTEXT RESULT:\n")
    print(context)

if __name__ == "__main__":
    import sys
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(">>> RAG PIPELINE TESTER <<<")
    
    # BẠN ĐÃ NẠP CƠ SỞ DỮ LIỆU THÀNH CÔNG RỒI NÊN KHÔNG CẦN CHẠY build_index LẠI NỮA!
    if "--rebuild" in sys.argv:
        print("\n[CẢNH BÁO] Đang nạp và nhúng (Embed) lại toàn bộ Data. (Bước này Sẽ Tốn Token OpenAI)...")
        db = build_index(BASE_DIR)
    else:
        print("\n[HỆ THỐNG] Sử dụng VectorDB có sẵn trên ổ cứng cục bộ (Hoàn toàn KHÔNG tốn Token nhúng nữa!)")
        db = VectorDBManager(BASE_DIR)
    
    print("\n--- BỘ TEST TÌM KIẾM TRỰC TIẾP ---")
    print("Mẹo: Thêm --rebuild khi chạy script nếu bạn có cập nhật file JSON/TXT nhé.")
    # Vòng lặp cho phép test hàng ngàn câu mà chỉ tốn đúng 1 xíu token cho việc dịch (embed) câu hỏi đó thôi
    while True:
        try:
            print("\n" + "="*60)
            query = input("Bạn muốn hỏi thông tin gì? (Gõ 'exit' để thoát): ")
            if query.lower().strip() in ["exit", "q", "quit"]:
                print("Tạm biệt!")
                break
            if not query.strip():
                continue
                
            test_search(BASE_DIR, db, query)
            
        except KeyboardInterrupt:
            print("\nTạm biệt!")
            break
