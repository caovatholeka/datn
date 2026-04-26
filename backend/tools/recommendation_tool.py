"""
recommendation_tool.py
Tool tư vấn và gợi ý sản phẩm phù hợp ngân sách.
Đọc từ products.json + price.json để tìm alternatives.
"""
import json
import os
import re
from typing import Optional

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DATA_DIR = os.path.join(_BASE, "data", "raw")


def _load_products() -> list:
    path = os.path.join(_DATA_DIR, "products.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_prices() -> dict:
    path = os.path.join(_DATA_DIR, "price.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {r["product_id"]: r for r in raw}


def _extract_budget_from_query(query: str) -> Optional[float]:
    """Trích xuất ngân sách từ câu hỏi (VD: '10 triệu', '15tr', '500k')."""
    query_lower = query.lower()

    # Pattern: X triệu / X tr
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr\b)", query_lower)
    if m:
        return float(m.group(1).replace(",", ".")) * 1_000_000

    # Pattern: X nghìn / Xk
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:nghìn|k\b)", query_lower)
    if m:
        return float(m.group(1).replace(",", ".")) * 1_000

    return None


def get_recommendations(
    query: str,
    reference_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
    top_k: int = 5,
) -> dict:
    """
    Tìm sản phẩm phù hợp theo ngân sách hoặc rẻ hơn sản phẩm tham chiếu.

    Args:
        query:           Câu hỏi gốc (để trích xuất budget nếu chưa rõ).
        reference_price: Giá sản phẩm tham chiếu (VD: iPhone 15 = 18.5M → tìm rẻ hơn).
        max_price:       Ngân sách tối đa (nếu user nêu trực tiếp).
        category:        Lọc theo danh mục (phone, laptop, tablet...).
        top_k:           Số sản phẩm tối đa trả về.

    Returns:
        {
            "status": "success" | "not_found",
            "max_price": float,
            "products": [{"name", "brand", "price", "final_price", "discount", "category"}]
        }
    """
    try:
        products = _load_products()
        prices   = _load_prices()

        # Xác định ngưỡng giá
        budget = max_price or reference_price or _extract_budget_from_query(query)

        # Nếu không trích xuất được budget → trả về top 5 rẻ nhất
        results = []
        for p in products:
            pid = p.get("id") or p.get("product_id", "")   # products.json dùng "id"
            price_rec = prices.get(pid, {})
            if not price_rec:
                continue

            base_price = float(price_rec.get("price", 0))
            discount   = float(price_rec.get("discount", 0))
            final      = round(base_price * (1 - discount / 100), 0)

            # Lọc theo ngân sách
            if budget and final > budget:
                continue

            # Lọc theo danh mục nếu có
            if category:
                if category.lower() not in p.get("category", "").lower():
                    continue

            results.append({
                "product_id":  pid,
                "name":        p.get("name", ""),
                "brand":       p.get("brand", ""),
                "category":    p.get("category", ""),
                "price":       base_price,
                "discount":    discount,
                "final_price": final,
            })

        if not results:
            return {
                "status":    "not_found",
                "max_price": budget,
                "message":   f"Không tìm thấy sản phẩm phù hợp với ngân sách {budget:,.0f} VND." if budget else "Không tìm thấy sản phẩm.",
                "products":  []
            }

        # Sắp xếp theo giá tăng dần, lấy top_k
        results.sort(key=lambda x: x["final_price"])
        results = results[:top_k]

        return {
            "status":    "success",
            "max_price": budget,
            "count":     len(results),
            "products":  results,
        }

    except Exception as e:
        return {
            "status":  "error",
            "message": f"Lỗi khi tìm gợi ý sản phẩm: {str(e)}",
            "products": []
        }
