"""
4. price_repository.py
Data Access Layer cho Price.
"""
import json
import os
from typing import Optional


class PriceRepository:
    """
    Repository cho giá sản phẩm.
    Current implementation: đọc từ price.json.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base, "data", "raw")
        self._data_dir = data_dir
        self._cache: Optional[dict] = None  # Index bằng product_id để O(1) lookup

    def _load(self) -> dict:
        """Load và index price data bằng product_id."""
        if self._cache is None:
            path = os.path.join(self._data_dir, "price.json")
            with open(path, "r", encoding="utf-8") as f:
                raw: list = json.load(f)
            # Chuyển list thành dict {product_id: record} để lookup nhanh hơn
            self._cache = {r["product_id"]: r for r in raw}
        return self._cache

    def get_price(self, product_id: str) -> Optional[dict]:
        """Trả về thông tin giá của một sản phẩm, hoặc None nếu không tìm thấy."""
        return self._load().get(product_id)
