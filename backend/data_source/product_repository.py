"""
2. product_repository.py
Data Access Layer cho Product - trừu tượng hóa hoàn toàn nguồn dữ liệu.
Muốn đổi sang PostgreSQL: chỉ cần viết lại class này, các tools không cần thay đổi.
"""
import json
import os
from typing import Optional


class ProductRepository:
    """
    Repository pattern: tách biệt logic truy cập dữ liệu khỏi business logic.
    Current implementation: đọc từ JSON file.
    Future: thay bằng SQLAlchemy/psycopg2 kết nối PostgreSQL.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Tự động tính đường dẫn tuyệt đối đến thư mục data/raw
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base, "data", "raw")
        self._data_dir = data_dir
        self._cache: Optional[list] = None  # In-memory cache tránh đọc file nhiều lần

    def _load(self) -> list:
        """Load và cache dữ liệu JSON vào bộ nhớ."""
        if self._cache is None:
            path = os.path.join(self._data_dir, "products.json")
            with open(path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        return self._cache

    def get_all_products(self) -> list[dict]:
        """Trả về toàn bộ danh sách sản phẩm."""
        return self._load()

    def get_by_id(self, product_id: str) -> Optional[dict]:
        """Lấy một sản phẩm theo ID chính xác."""
        for p in self._load():
            if p.get("id") == product_id:
                return p
        return None

    def search_products(self, query: str) -> list[dict]:
        """
        Tìm kiếm sản phẩm theo token. Tách query thành từng từ riêng để có thể khớp với
        tên sản phẩm dù query chứa các từ thừa (ví dụ: 'còn hàng không', 'giá bao nhiêu').
        """
        # Danh sách stop words tiếng Việt + tiếng Anh thường gặp, lọc trước khi so khớp
        STOP_WORDS = {
            "còn", "hàng", "không", "giá", "bao", "nhiêu", "tiền",
            "hỏi", "muốn", "có", "và", "hay", "là", "bạn", "tôi",
            "the", "is", "are", "how", "what", "much", "stock", "price",
            "check", "của", "nào", "này", "sản", "phẩm",
        }
        q_lower = query.lower().strip()
        # Tách thành tokens, bỏ stop words và từ quá ngắn
        tokens = [
            t for t in q_lower.replace("-", " ").split()
            if len(t) > 1 and t not in STOP_WORDS
        ]

        if not tokens:
            return []

        results = []
        for p in self._load():
            name    = p.get("name", "").lower()
            brand   = p.get("brand", "").lower()
            category = p.get("category", "").lower()
            combined = f"{name} {brand} {category}"

            # Sản phẩm được chấp nhận nếu ít nhất 1 token khkhp trong tên/thương hiệu
            if any(token in combined for token in tokens):
                results.append(p)
        return results
