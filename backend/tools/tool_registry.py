"""
8. tool_registry.py
Sổ đăng ký tập trung tất cả các tools trong hệ thống.
Điểm duy nhất cần chỉnh sửa khi thêm tool mới.
"""
from .product_resolver import ProductResolver
from .inventory_tool import InventoryTool
from .pricing_tool import PricingTool
from .base_tool import BaseTool

# ============================================================
# REGISTRY - Chỉnh sửa nơi này khi thêm tool mới
# ============================================================
TOOLS: dict[str, BaseTool] = {
    "resolve_product":      ProductResolver(),
    "get_stock":            InventoryTool(),
    "get_price_and_promo":  PricingTool(),
}


def get_tool(tool_name: str) -> BaseTool | None:
    """Lấy tool instance theo tên. Trả về None nếu không tồn tại."""
    return TOOLS.get(tool_name)


def list_tools() -> list[dict]:
    """Liệt kê tất cả tools đã đăng ký cùng mô tả."""
    return [
        {"name": t.name, "description": t.description}
        for t in TOOLS.values()
    ]
