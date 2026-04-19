"""
3. inventory_repository.py
Data Access Layer cho Inventory.
"""
import json
import os
from typing import Optional


class InventoryRepository:
    """
    Repository cho tồn kho.
    Current implementation: đọc từ inventory.json.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base, "data", "raw")
        self._data_dir = data_dir
        self._cache: Optional[list] = None

    def _load(self) -> list:
        if self._cache is None:
            path = os.path.join(self._data_dir, "inventory.json")
            with open(path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        return self._cache

    def get_stock(self, product_id: str, warehouse: Optional[str] = None) -> list[dict]:
        """
        Trả về thông tin tồn kho.
        - Nếu warehouse được chỉ định: trả về record của kho đó.
        - Nếu không: trả về tất cả records của sản phẩm.
        """
        records = [r for r in self._load() if r.get("product_id") == product_id]
        if warehouse:
            records = [r for r in records if warehouse.lower() in r.get("warehouse", "").lower()]
        return records
