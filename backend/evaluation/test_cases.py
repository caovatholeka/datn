"""
test_cases.py
Bộ dữ liệu kiểm thử 28 câu hỏi thực tế dành cho chatbot bán hàng điện tử.

Các câu được thiết kế để phản ánh cách người dùng THỰC SỰ hỏi,
không phải câu mẫu lý tưởng.  Bao gồm:
  - Từ ngữ tự nhiên / rút gọn ("bao nhiêu tiền", "còn không", "hỏi cái này")
  - Câu mơ hồ, thiếu tên sản phẩm cụ thể
  - Câu lai (hybrid): hỏi nhiều thứ cùng lúc
  - Câu ngoài phạm vi (unknown)
  - Chào hỏi xã giao (greeting)

Nhãn ground-truth dùng cùng schema với LLM Classifier:
  intent:     "tool" | "rag" | "hybrid" | "greeting" | "unknown"
  sub_intent: sub-intent chính kỳ vọng
"""

TEST_CASES = [
    # ── GREETING (2 câu) ──────────────────────────────────────
    {
        "id": 1,
        "query":       "xin chào shop ạ",
        "intent":      "greeting",
        "sub_intent":  "greeting",
        "note":        "Chào hỏi cơ bản",
    },
    {
        "id": 2,
        "query":       "shop ơi cho mình hỏi tý nhé",
        "intent":      "greeting",
        "sub_intent":  "greeting",
        "note":        "Mở đầu cuộc trò chuyện, chưa hỏi gì cụ thể",
    },

    # ── CHECK_PRICE / TOOL (5 câu) ───────────────────────────
    {
        "id": 3,
        "query":       "iphone 16 giá bao nhiêu tiền vậy?",
        "intent":      "tool",
        "sub_intent":  "check_price",
        "note":        "Hỏi giá thẳng — phổ biến nhất",
    },
    {
        "id": 4,
        "query":       "samsung galaxy s25 ultra bán bao nhiêu?",
        "intent":      "tool",
        "sub_intent":  "check_price",
        "note":        "Dùng 'bán' thay vì 'giá'",
    },
    {
        "id": 5,
        "query":       "macbook air m3 mấy tiền vậy bạn",
        "intent":      "tool",
        "sub_intent":  "check_price",
        "note":        "Từ thân mật 'bạn', viết tắt 'mấy tiền'",
    },
    {
        "id": 6,
        "query":       "oppo reno 12 pro có đang sale không?",
        "intent":      "tool",
        "sub_intent":  "check_price",
        "note":        "Hỏi giảm giá/sale — dạng gián tiếp của check_price",
    },
    {
        "id": 7,
        "query":       "samsung s24 fe giá thế nào shop ơi",
        "intent":      "tool",
        "sub_intent":  "check_price",
        "note":        "Kêu 'shop ơi' — cách nói dân dã",
    },

    # ── CHECK_STOCK / TOOL (4 câu) ───────────────────────────
    {
        "id": 8,
        "query":       "shop còn iphone 15 pro max không?",
        "intent":      "tool",
        "sub_intent":  "check_stock",
        "note":        "Hỏi tồn kho thẳng",
    },
    {
        "id": 9,
        "query":       "xiaomi 14t pro còn hàng không bạn?",
        "intent":      "tool",
        "sub_intent":  "check_stock",
        "note":        "Phổ biến — 'còn hàng không?'",
    },
    {
        "id": 10,
        "query":       "cửa hàng có bán điện thoại samsung không?",
        "intent":      "tool",
        "sub_intent":  "check_stock",
        "note":        "Hỏi brand chứ không hỏi model cụ thể",
    },
    {
        "id": 11,
        "query":       "airpods pro gen 2 hiện còn bán không?",
        "intent":      "tool",
        "sub_intent":  "check_stock",
        "note":        "Phụ kiện, hỏi 'hiện còn bán không'",
    },

    # ── HYBRID: price + stock (4 câu) ────────────────────────
    {
        "id": 12,
        "query":       "iphone 16 pro còn hàng không và giá bao nhiêu?",
        "intent":      "hybrid",
        "sub_intent":  "check_stock",   # sub chính (stock trước)
        "note":        "Hỏi cả 2 trong 1 câu — rõ ràng",
    },
    {
        "id": 13,
        "query":       "samsung galaxy s25 giá và tồn kho thế nào?",
        "intent":      "hybrid",
        "sub_intent":  "check_price",
        "note":        "Đảo thứ tự: giá trước, tồn kho sau",
    },
    {
        "id": 14,
        "query":       "xiaomi 14 ultra còn không, mà giá ra sao?",
        "intent":      "hybrid",
        "sub_intent":  "check_stock",
        "note":        "Ngôn ngữ rất tự nhiên, có dấu phẩy ngắt",
    },
    {
        "id": 15,
        "query":       "sony wh-1000xm5 giá bao nhiêu, có sẵn hàng không?",
        "intent":      "hybrid",
        "sub_intent":  "check_price",
        "note":        "Tai nghe, dùng 'có sẵn hàng' thay vì 'còn hàng'",
    },

    # ── PRODUCT_INFO / RAG (5 câu) ───────────────────────────
    {
        "id": 16,
        "query":       "so sánh iphone 16 và samsung s25 đi",
        "intent":      "rag",
        "sub_intent":  "product_info",
        "note":        "So sánh 2 flagship — cần RAG",
    },
    {
        "id": 17,
        "query":       "xiaomi 14t pro có mấy camera?",
        "intent":      "rag",
        "sub_intent":  "product_info",
        "note":        "Hỏi thông số kỹ thuật cụ thể",
    },
    {
        "id": 18,
        "query":       "pin iphone 16 pro max xài được bao lâu?",
        "intent":      "rag",
        "sub_intent":  "product_info",
        "note":        "Hỏi tuổi thọ pin — thông số kỹ thuật",
    },
    {
        "id": 19,
        "query":       "airpods pro 2 có chống ồn tốt không?",
        "intent":      "rag",
        "sub_intent":  "product_info",
        "note":        "Review/đánh giá tính năng",
    },
    {
        "id": 20,
        "query":       "vivo v40 màn hình bao nhiêu inch?",
        "intent":      "rag",
        "sub_intent":  "product_info",
        "note":        "Thông số cụ thể, ngắn gọn",
    },

    # ── RECOMMENDATION / RAG (3 câu) ─────────────────────────
    {
        "id": 21,
        "query":       "điện thoại chụp ảnh đẹp tầm 15 triệu nên mua gì?",
        "intent":      "rag",
        "sub_intent":  "recommendation",
        "note":        "Tư vấn theo nhu cầu + ngân sách",
    },
    {
        "id": 22,
        "query":       "laptop gaming pin trâu dưới 25 triệu thì mua cái nào?",
        "intent":      "rag",
        "sub_intent":  "recommendation",
        "note":        "Điều kiện cụ thể: gaming + pin + giá",
    },
    {
        "id": 23,
        "query":       "tai nghe chống ồn tốt tầm 2 triệu có gì không shop?",
        "intent":      "rag",
        "sub_intent":  "recommendation",
        "note":        "Tư vấn phụ kiện theo ngân sách",
    },

    # ── POLICY / RAG (2 câu) ─────────────────────────────────
    {
        "id": 24,
        "query":       "bảo hành máy bao lâu và làm sao đổi trả?",
        "intent":      "rag",
        "sub_intent":  "policy",
        "note":        "Hỏi chính sách bảo hành + đổi trả",
    },
    {
        "id": 25,
        "query":       "mua online về bị lỗi có được đổi không?",
        "intent":      "rag",
        "sub_intent":  "policy",
        "note":        "Tình huống thực tế: hàng lỗi sau khi mua online",
    },

    # ── UNKNOWN — ngoài phạm vi hỗ trợ (3 câu) ──────────────────
    {
        "id": 26,
        "query":       "thời tiết hà nội hôm nay thế nào?",
        "intent":      "unknown",
        "sub_intent":  "unknown",
        "note":        "Hoàn toàn ngoài phạm vi — dự báo thời tiết",
    },
    {
        "id": 27,
        "query":       "kết quả bóng đá tối qua như nào vậy?",
        "intent":      "unknown",
        "sub_intent":  "unknown",
        "note":        "Chủ đề thể thao — không liên quan đến điện tử",
    },
    {
        "id": 28,
        "query":       "bạn có thể viết bài luận cho tôi không?",
        "intent":      "unknown",
        "sub_intent":  "unknown",
        "note":        "Yêu cầu tạo nội dung — ngoài scope bán hàng",
    },
]
