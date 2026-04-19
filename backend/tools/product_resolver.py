"""
5. product_resolver.py
Bộ phân giải sản phẩm: chuyển ngôn ngữ tự nhiên → product_id nội bộ.
Đây là bước quan trọng nhất trong tool calling pipeline.
"""
from typing import Optional
from .base_tool import BaseTool
from ..data_source.product_repository import ProductRepository


class ProductResolver(BaseTool):
    """
    Phân giải query người dùng thành product_id cụ thể.
    Sử dụng partial/fuzzy matching không phân biệt hoa thường.
    Không bao giờ crash - mọi lỗi đều được trả về dưới dạng dict chuẩn.
    """

    def __init__(self, repo: Optional[ProductRepository] = None):
        self._repo = repo or ProductRepository()

    @property
    def name(self) -> str:
        return "resolve_product"

    @property
    def description(self) -> str:
        return (
            "Chuyển đổi tên sản phẩm từ ngôn ngữ tự nhiên thành product_id nội bộ. "
            "Gọi tool này TRƯỚC TIÊN trước khi gọi bất kỳ tool nghiệp vụ nào khác."
        )

    def run(self, **kwargs) -> dict:
        """
        Args:
            query (str): Tên sản phẩm người dùng nhắc đến.
        Returns:
            {
                "status": "success" | "not_found" | "multiple",
                "product_id": str | None,
                "name": str | None,
                "confidence": float | None,
                "candidates": list | None
            }
        """
        try:
            query: str = kwargs.get("query", "").strip()
            if not query:
                return {
                    "status": "not_found",
                    "product_id": None,
                    "name": None,
                    "confidence": None,
                    "candidates": None,
                    "message": "Query rỗng, không thể phân giải sản phẩm."
                }

            matches = self._repo.search_products(query)

            if not matches:
                return {
                    "status": "not_found",
                    "product_id": None,
                    "name": None,
                    "confidence": 0.0,
                    "candidates": None,
                    "message": f"Không tìm thấy sản phẩm nào khớp với '{query}'."
                }

            # Tính điểm confidence dựa trên mức độ khớp
            scored = self._score_matches(query.lower(), matches)

            # FIX 1: scored có thể rỗng khi tất cả matches bị lọc qua ngưỡng min_required.
            # Thay vì báo error, thực hiện relaxed-scoring (không có ngưỡng) và trả multiple.
            if not scored:
                relaxed = self._score_matches_relaxed(query.lower(), matches)
                candidates = [
                    {"product_id": p["id"], "name": p["name"], "confidence": p["_score"]}
                    for p in relaxed[:5]
                ]
                return {
                    "status": "multiple",
                    "product_id": None,
                    "name": None,
                    "confidence": None,
                    "candidates": candidates,
                    "message": (
                        f"Tìm thấy {len(matches)} sản phẩm có thể liên quan. "
                        f"Bạn đang hỏi về sản phẩm nào?"
                    )
                }

            best = scored[0]

            if len(scored) == 1:
                # Chính xác: chỉ có 1 kết quả
                return {
                    "status": "success",
                    "product_id": best["id"],
                    "name": best["name"],
                    "confidence": best["_score"],
                    "candidates": None,
                    "message": f"Đã xác định sản phẩm: {best['name']}"
                }

            # AUTO-SELECT: nếu best score rất cao (>= 0.85) → chọn ngay
            if best["_score"] >= 0.85:
                return {
                    "status": "success",
                    "product_id": best["id"],
                    "name": best["name"],
                    "confidence": best["_score"],
                    "candidates": None,
                    "message": f"Đã xác định sản phẩm với độ tin cậy cao: {best['name']}"
                }

            # AUTO-SELECT khoảng cách: top1 - top2 > threshold → tự chọn, không hỏi lại
            _AUTO_GAP = 0.15
            if len(scored) >= 2 and (best["_score"] - scored[1]["_score"]) >= _AUTO_GAP:
                return {
                    "status": "success",
                    "product_id": best["id"],
                    "name": best["name"],
                    "confidence": best["_score"],
                    "candidates": None,
                    "message": f"Tự động chọn sản phẩm phù hợp nhất: {best['name']} "
                               f"(điểm {best['_score']:.3f} vs {scored[1]['_score']:.3f})"
                }

            # Nhiều kết quả đồng điều, cần làm rõ
            candidates = [
                {"product_id": p["id"], "name": p["name"], "confidence": p["_score"]}
                for p in scored[:5]
            ]
            return {
                "status": "multiple",
                "product_id": None,
                "name": None,
                "confidence": None,
                "candidates": candidates,
                "message": f"Tìm thấy {len(candidates)} sản phẩm phù hợp. Vui lòng chỉ định rõ hơn."
            }

        except Exception as e:
            return {
                "status": "not_found",
                "product_id": None,
                "name": None,
                "confidence": None,
                "candidates": None,
                "message": f"Lỗi khi phân giải sản phẩm: {str(e)}"
            }

    def _score_matches(self, query: str, matches: list[dict]) -> list[dict]:
        """
        Tính điểm bằng F1 score giữa tập token query và tập token tên sản phẩm.
        Áp dụng ngưỡng thiểu số token để loại false positive (nhiễu dữ liệu).
        """
        STOP_WORDS = {
            "còn", "hàng", "không", "giá", "bao", "nhiêu", "tiền",
            "hỏi", "muốn", "có", "và", "hay", "là", "bạn", "tôi",
            "the", "is", "are", "how", "what", "much", "stock", "price",
            "check", "của", "nào", "này", "sản", "phẩm", "mua", "tìm",
        }

        # Lọc tokens có nghĩa từ query
        query_tokens = [
            t for t in query.lower().replace("-", " ").split()
            if len(t) > 1 and t not in STOP_WORDS
        ] or query.lower().split()

        n_q = len(query_tokens)
        # Ngưỡng tối thiểu: query dài thì yêu cầu khớp nhiều token hơn
        # - 1 token  → cần 1 match
        # - 2 tokens → cần 1 match  
        # - 3+ tokens → cần ít nhất ceil(n * 0.6) match
        if n_q <= 2:
            min_required = 1
        else:
            import math
            min_required = math.ceil(n_q * 0.6)

        scored = []
        for p in matches:
            name_lower = p.get("name", "").lower()
            brand_lower = p.get("brand", "").lower()
            combined = f"{name_lower} {brand_lower}"
            name_tokens = [t for t in name_lower.split() if len(t) > 0]
            n_name = len(name_tokens)

            matched = [t for t in query_tokens if t in combined]
            n_matched = len(matched)

            # Bỏ qua các sản phẩm không đạt ngưỡng tối thiểu → giảm false positive
            if n_matched < min_required:
                continue

            # Exact match → điểm tuyệt đối
            if query.lower().strip() == name_lower:
                score = 1.0
            else:
                # Precision: tỷ lệ token query có trong product
                precision = n_matched / n_q
                # Recall: tỷ lệ token product được query cover
                recall = n_matched / n_name if n_name > 0 else 0
                # F1 score tổng hợp cả 2 chiều
                if precision + recall > 0:
                    score = 2 * precision * recall / (precision + recall)
                else:
                    score = 0.0

            p = dict(p)
            p["_score"] = round(min(score, 1.0), 3)
            scored.append(p)

        return sorted(scored, key=lambda x: x["_score"], reverse=True)

    def _score_matches_relaxed(self, query: str, matches: list[dict]) -> list[dict]:
        """
        Scoring không có ngưỡng tối thiểu - dùng như fallback khi _score_matches trả rỗng.
        Cho phép match 1 token bất kỳ để tạo danh sách candidates gợi ý.
        """
        STOP_WORDS = {
            "còn", "hàng", "không", "giá", "bao", "nhiêu", "tiền",
            "hỏi", "muốn", "có", "và", "hay", "là", "bạn", "tôi",
            "the", "is", "are", "how", "what", "much", "stock", "price",
            "check", "của", "nào", "này", "sản", "phẩm", "mua", "tìm",
            "điện", "thoại", "máy", "cái", "chiếc", "con",
        }
        query_tokens = [
            t for t in query.lower().replace("-", " ").split()
            if len(t) > 1 and t not in STOP_WORDS
        ] or query.lower().split()

        scored = []
        for p in matches:
            name_lower = p.get("name", "").lower()
            combined = f"{name_lower} {p.get('brand', '').lower()}"
            name_tokens = name_lower.split()
            n_name = len(name_tokens)

            matched = [t for t in query_tokens if t in combined]
            n_matched = len(matched)
            if n_matched == 0:
                continue

            precision = n_matched / len(query_tokens)
            recall = n_matched / n_name if n_name > 0 else 0
            score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            p = dict(p)
            p["_score"] = round(min(score, 1.0), 3)
            scored.append(p)

        return sorted(scored, key=lambda x: x["_score"], reverse=True)
