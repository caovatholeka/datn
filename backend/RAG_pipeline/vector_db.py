import os
import shutil
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

class VectorDBManager:
    """4. Embedding + Indexing module."""
    
    def __init__(self, base_dir: str):
        # Tự động nạp file .env vào biến môi trường của Python
        dotenv_path = os.path.join(base_dir, ".env")
        load_dotenv(dotenv_path)
        
        self.persist_directory = os.path.join(base_dir, "chroma_db")
        # Khởi tạo mô hình embed. Lúc này Langchain sẽ tự tìm thấy OPENAI_API_KEY
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

    def embed_and_index(self, chunks: list):
        """Index (add) list các chunks vào database."""
        # --- CHIẾN LƯỢC: CHỈ CHO PHÉP 1 DB TRỌN VẸN Duy nhất ---
        # Ngăn chặn tình trạng Append trùng rác bằng cách xóa cũ trước khi build mới
        print("   -> [HỆ THỐNG] Đang dọn dẹp kho dữ liệu Chroma DB cũ (Xóa an toàn tránh WinError 32)...")
        try:
            # Drop data trực tiếp từ Chroma thay vì dùng lệnh xóa Folder của Hệ điều hành
            self.vectorstore.delete_collection()
            # Khởi tạo lại store instance để Langchain gen ra collection mới tinh thay thế
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        except Exception as e:
            pass # Bỏ qua nếu DB chưa từng tồn tại
            
        docs = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["text"],
                metadata=chunk["metadata"]
            )
            docs.append(doc)
            
        # Thêm vector, text, metadata vào DB
        if docs:
            self.vectorstore.add_documents(docs)
            print(f"Đã lưu {len(docs)} documents/chunks vào Chroma DB.")
        return True
