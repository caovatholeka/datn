"""
7. pricing_tool.py
Tool tra cứu giá và khuyến mãi của sản phẩm.
"""
from typing import Optional
from .base_tool import BaseTool
from ..data_source.price_repository import PriceRepository


class PricingTool(BaseTool):
    """Tool tra cứu giá gốc, % giảm giá và giá cuối cùng của sản phẩm."""

    def __init__(self, repo: Optional[PriceRepository] = None):
        self._repo = repo or PriceRepository()

    @property
    def name(self) -> str:
        return "get_price_and_promo"

    @property
    def description(self) -> str:
        return (
            "Tra cứu giá bán, phần trăm khuyến mãi và giá cuối cùng của sản phẩm. "
            "Trả về đầy đủ thông tin giá theo định dạng chuẩn với đơn vị VND."
        )

    def run(self, **kwargs) -> dict:
        """
        Args:
            product_id (str): ID sản phẩm (bắt buộc).
        Returns:
            {
                "product_id": str,
                "price": float,
                "discount": float,
                "final_price": float,
                "currency": "VND"
            }
        """
        try:
            product_id: str = kwargs.get("product_id", "").strip()
            if not product_id:
                return {
                    "status": "error",
                    "message": "product_id là bắt buộc nhưng không được cung cấp."
                }

            price_record = self._repo.get_price(product_id)

            if not price_record:
                return {
                    "status": "error",
                    "product_id": product_id,
                    "message": f"Không tìm thấy thông tin giá cho sản phẩm {product_id}."
                }

            price: float = float(price_record.get("price", 0))
            discount_pct: float = float(price_record.get("discount", 0))
            final_price: float = price * (1 - discount_pct / 100)

            return {
                "status": "success",
                "product_id": product_id,
                "price": price,
                "discount": discount_pct,
                "final_price": round(final_price, 0),
                "currency": "VND"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi khi tra cứu giá: {str(e)}"
            }
