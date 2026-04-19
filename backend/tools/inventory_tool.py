"""
6. inventory_tool.py
Tool kiểm tra tồn kho theo product_id và warehouse (tùy chọn).
"""
from typing import Optional
from .base_tool import BaseTool
from ..data_source.inventory_repository import InventoryRepository


class InventoryTool(BaseTool):
    """Tool truy vấn số lượng tồn kho từ hệ thống kho hàng."""

    def __init__(self, repo: Optional[InventoryRepository] = None):
        self._repo = repo or InventoryRepository()

    @property
    def name(self) -> str:
        return "get_stock"

    @property
    def description(self) -> str:
        return (
            "Kiểm tra số lượng tồn kho của sản phẩm theo product_id. "
            "Có thể lọc theo kho hàng cụ thể (warehouse) nếu người dùng yêu cầu."
        )

    def run(self, **kwargs) -> dict:
        """
        Args:
            product_id (str): ID sản phẩm (bắt buộc).
            warehouse (str, optional): Tên kho hàng cụ thể (vd: 'Hà Nội').
        Returns:
            {
                "product_id": str,
                "warehouse": str,
                "stock": int | list[dict]
            }
        """
        try:
            product_id: str = kwargs.get("product_id", "").strip()
            warehouse: Optional[str] = kwargs.get("warehouse", None)

            if not product_id:
                return {
                    "status": "error",
                    "message": "product_id là bắt buộc nhưng không được cung cấp."
                }

            records = self._repo.get_stock(product_id, warehouse)

            if not records:
                scope = f"kho '{warehouse}'" if warehouse else "hệ thống"
                return {
                    "status": "error",
                    "product_id": product_id,
                    "message": f"Không tìm thấy thông tin tồn kho cho sản phẩm {product_id} trong {scope}."
                }

            if warehouse:
                # Trả về số lượng đơn của kho đó
                total_stock = sum(r.get("stock", 0) for r in records)
                return {
                    "status": "success",
                    "product_id": product_id,
                    "warehouse": records[0].get("warehouse", warehouse),
                    "stock": total_stock
                }
            else:
                # Trả về toàn bộ breakdown theo kho
                stock_breakdown = [
                    {"warehouse": r.get("warehouse"), "stock": r.get("stock", 0)}
                    for r in records
                ]
                total = sum(r["stock"] for r in stock_breakdown)
                return {
                    "status": "success",
                    "product_id": product_id,
                    "warehouse": "all",
                    "stock": stock_breakdown,
                    "total_stock": total
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi khi truy vấn tồn kho: {str(e)}"
            }
