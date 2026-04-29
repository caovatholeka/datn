"""
test_cases.py — Bộ 50 câu kiểm thử nâng cao cho chatbot bán hàng điện tử.
Thiết kế để bao phủ các edge-case khó:
  - Viết tắt, tiếng lóng, typo
  - Câu mơ hồ / đa nghĩa
  - Câu hỏi giá ngoài domain (bitcoin, xăng)
  - Hybrid 3 chiều
  - RAG policy ẩn trong câu hỏi sản phẩm
  - Unknown giả dạng tool
"""

TEST_CASES = [

    # ══════════════════════════════════════════════════════════
    # GREETING — 4 câu (casual → formal → English → implicit)
    # ══════════════════════════════════════════════════════════
    {
        "id": 1,
        "query":      "xin chào shop ạ",
        "intent":     "greeting",
        "sub_intent": "greeting",
        "note":       "Chào cơ bản",
    },
    {
        "id": 2,
        "query":      "shop ơi cho mình hỏi tý nhé",
        "intent":     "greeting",
        "sub_intent": "greeting",
        "note":       "Mở đầu chưa hỏi gì",
    },
    {
        "id": 3,
        "query":      "hi shop, bạn có thể tư vấn giúp mình không?",
        "intent":     "greeting",
        "sub_intent": "greeting",
        "note":       "English 'hi' + xin tư vấn chưa rõ sản phẩm",
    },
    {
        "id": 4,
        "query":      "alo shop",
        "intent":     "greeting",
        "sub_intent": "greeting",
        "note":       "Câu siêu ngắn — dùng 'alo' như gọi điện",
    },

    # ══════════════════════════════════════════════════════════
    # TOOL / check_price — 12 câu (tăng dần độ khó)
    # ══════════════════════════════════════════════════════════
    {
        "id": 5,
        "query":      "iphone 16 giá bao nhiêu tiền vậy?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Hỏi giá thẳng — baseline",
    },
    {
        "id": 6,
        "query":      "samsung galaxy s25 ultra bán bao nhiêu?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Dùng 'bán' thay vì 'giá'",
    },
    {
        "id": 7,
        "query":      "ip 16 pro max bao nhiêu",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Viết tắt 'ip' thay vì iPhone — rất phổ biến",
    },
    {
        "id": 8,
        "query":      "s25 ultra phé không shop?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Tiếng lóng 'phé' = đắt không",
    },
    {
        "id": 9,
        "query":      "macbook air m3 mấy đồng vậy bạn",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Lóng 'mấy đồng' — Nam Bộ",
    },
    {
        "id": 10,
        "query":      "oppo reno 12 pro có đang sale không?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "'sale' = giảm giá — gián tiếp",
    },
    {
        "id": 11,
        "query":      "giá galaxy tab s9 ultra 512gb màu đen bao nhiêu?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Máy tính bảng + dung lượng + màu sắc",
    },
    {
        "id": 12,
        "query":      "rog phone 8 pro giá có cạnh tranh không?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Hỏi giá + so sánh mơ hồ — gaming phone",
    },
    {
        "id": 13,
        "query":      "iphone 15 128gb còn bảo hành giá bao nhiêu?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Từ 'bảo hành' xuất hiện nhưng intent vẫn là giá",
    },
    {
        "id": 14,
        "query":      "airpods pro 2 giảm rồi à, còn bao nhiêu?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Giả định đã giảm, hỏi giá hiện tại",
    },
    {
        "id": 15,
        "query":      "giá iphone 16 pro màu titan tự nhiên",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Bao gồm màu sắc trong câu hỏi giá",
    },
    {
        "id": 16,
        "query":      "mình muốn mua samsung s24 fe, giá thế nào?",
        "intent":     "tool",
        "sub_intent": "check_price",
        "note":       "Purchase intent + price — câu dài tự nhiên",
    },

    # ══════════════════════════════════════════════════════════
    # TOOL / check_stock — 7 câu
    # ══════════════════════════════════════════════════════════
    {
        "id": 17,
        "query":      "shop còn iphone 15 pro max không?",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "Hỏi tồn kho thẳng",
    },
    {
        "id": 18,
        "query":      "xiaomi 14t pro còn hàng không bạn?",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "'còn hàng' — phổ biến",
    },
    {
        "id": 19,
        "query":      "samsung a55 có không shop, cần mua gấp",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "Câu ngắn + urgency 'cần gấp'",
    },
    {
        "id": 20,
        "query":      "vẫn còn hàng iphone 16 không ạ?",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "Đảo 'vẫn còn hàng' lên đầu câu",
    },
    {
        "id": 21,
        "query":      "macbook pro m4 ship được luôn không hay hết hàng rồi?",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "Ship ngay = có sẵn hàng — hỏi gián tiếp",
    },
    {
        "id": 22,
        "query":      "mình cần mua 2 cái iphone 16 plus, còn không?",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "Số lượng 2 cái — mua sỉ nhỏ",
    },
    {
        "id": 23,
        "query":      "pixel 9 pro fold shop có nhập không?",
        "intent":     "tool",
        "sub_intent": "check_stock",
        "note":       "'có nhập không' = check_stock gián tiếp",
    },

    # ══════════════════════════════════════════════════════════
    # HYBRID — 8 câu (tăng độ phức tạp)
    # ══════════════════════════════════════════════════════════
    {
        "id": 24,
        "query":      "iphone 16 pro còn hàng không và giá bao nhiêu?",
        "intent":     "hybrid",
        "sub_intent": "check_stock",
        "note":       "Hybrid rõ ràng",
    },
    {
        "id": 25,
        "query":      "samsung galaxy s25 giá và tồn kho thế nào?",
        "intent":     "hybrid",
        "sub_intent": "check_price",
        "note":       "Đảo thứ tự giá trước",
    },
    {
        "id": 26,
        "query":      "xiaomi 14 ultra còn không, mà giá ra sao?",
        "intent":     "hybrid",
        "sub_intent": "check_stock",
        "note":       "Ngôn ngữ tự nhiên có dấu phẩy",
    },
    {
        "id": 27,
        "query":      "sony wh-1000xm5 giá bao nhiêu, có sẵn hàng không?",
        "intent":     "hybrid",
        "sub_intent": "check_price",
        "note":       "Tai nghe cao cấp",
    },
    {
        "id": 28,
        "query":      "mình muốn mua iphone 15, còn không và giá là bao?",
        "intent":     "hybrid",
        "sub_intent": "check_stock",
        "note":       "Purchase intent ẩn + hybrid",
    },
    {
        "id": 29,
        "query":      "tab s9 ultra 512gb hàng còn nhiều không, giá có tốt không?",
        "intent":     "hybrid",
        "sub_intent": "check_stock",
        "note":       "'giá có tốt không' = hỏi giá gián tiếp",
    },
    {
        "id": 30,
        "query":      "asus zenbook 14 oled còn hàng không giá bao nhiêu ship hà nội",
        "intent":     "hybrid",
        "sub_intent": "check_stock",
        "note":       "Không dấu câu — câu liên tục tự nhiên + địa điểm",
    },
    {
        "id": 31,
        "query":      "airpods max còn không và đang giảm giá bao nhiêu phần trăm?",
        "intent":     "hybrid",
        "sub_intent": "check_stock",
        "note":       "Hỏi % giảm cụ thể — phức tạp hơn",
    },

    # ══════════════════════════════════════════════════════════
    # RAG / product_info — 8 câu
    # ══════════════════════════════════════════════════════════
    {
        "id": 32,
        "query":      "so sánh iphone 16 và samsung s25 đi",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "So sánh 2 flagship",
    },
    {
        "id": 33,
        "query":      "xiaomi 14t pro có mấy camera và zoom được bao nhiêu lần?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "Thông số camera cụ thể",
    },
    {
        "id": 34,
        "query":      "pin iphone 16 pro max xài được bao lâu, sạc nhanh mấy watt?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "2 thông số kỹ thuật trong 1 câu",
    },
    {
        "id": 35,
        "query":      "samsung s25 ultra có bút s-pen không và viết có mượt không?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "Feature + trải nghiệm chủ quan",
    },
    {
        "id": 36,
        "query":      "macbook pro m4 ram bao nhiêu, có hỗ trợ 2 màn hình ngoài không?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "Thông số RAM + tính năng display",
    },
    {
        "id": 37,
        "query":      "pixel 9 pro camera có tốt hơn iphone 16 không?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "So sánh camera trực tiếp 2 sản phẩm",
    },
    {
        "id": 38,
        "query":      "iphone 16 có cổng usb-c không hay vẫn lightning?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "Hỏi về cổng kết nối — thông tin kỹ thuật quan trọng",
    },
    {
        "id": 39,
        "query":      "gaming laptop asus rog strix g16 màn hình refresh rate bao nhiêu?",
        "intent":     "rag",
        "sub_intent": "product_info",
        "note":       "Thông số màn hình gaming — khách chuyên nghiệp",
    },

    # ══════════════════════════════════════════════════════════
    # RAG / recommendation — 8 câu
    # ══════════════════════════════════════════════════════════
    {
        "id": 40,
        "query":      "điện thoại chụp ảnh đẹp tầm 15 triệu nên mua gì?",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "Budget + use case",
    },
    {
        "id": 41,
        "query":      "laptop gaming pin trâu dưới 25 triệu thì mua cái nào?",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "Gaming + pin + budget",
    },
    {
        "id": 42,
        "query":      "tai nghe chống ồn tốt tầm 2 triệu có gì không shop?",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "Phụ kiện + budget",
    },
    {
        "id": 43,
        "query":      "điện thoại nào dưới 10 triệu pin 5000mah trở lên?",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "Budget chặt + thông số kỹ thuật cụ thể",
    },
    {
        "id": 44,
        "query":      "mình là sinh viên muốn mua laptop tầm 18-20 triệu dùng đồ họa nhẹ",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "User persona + budget range + use case",
    },
    {
        "id": 45,
        "query":      "có gì rẻ hơn iphone 15 mà chụp ảnh cũng ổn không?",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "So sánh giá tham chiếu + feature ảnh",
    },
    {
        "id": 46,
        "query":      "mua tặng ba điện thoại tầm 12 triệu dùng dễ chụp ảnh đẹp",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "Mua tặng = không phải dùng cho mình — context khác",
    },
    {
        "id": 47,
        "query":      "nên mua iphone 16 hay samsung s25, dùng chụp ảnh và quay video",
        "intent":     "rag",
        "sub_intent": "recommendation",
        "note":       "So sánh để chọn — recommendation dạng so sánh 2 SP",
    },

    # ══════════════════════════════════════════════════════════
    # RAG / policy — 6 câu
    # ══════════════════════════════════════════════════════════
    {
        "id": 48,
        "query":      "bảo hành máy bao lâu và làm sao đổi trả?",
        "intent":     "rag",
        "sub_intent": "policy",
        "note":       "Chính sách bảo hành + đổi trả",
    },
    {
        "id": 49,
        "query":      "mua online về bị lỗi có được đổi không?",
        "intent":     "rag",
        "sub_intent": "policy",
        "note":       "Hàng lỗi — tình huống thực tế",
    },
    {
        "id": 50,
        "query":      "shop có ship toàn quốc không, mất mấy ngày và phí ship bao nhiêu?",
        "intent":     "rag",
        "sub_intent": "policy",
        "note":       "Chính sách vận chuyển — 3 câu hỏi con",
    },
    {
        "id": 51,
        "query":      "thanh toán trả góp lãi suất 0% có không?",
        "intent":     "rag",
        "sub_intent": "policy",
        "note":       "Chính sách thanh toán — trả góp",
    },
    {
        "id": 52,
        "query":      "mình mua iphone rồi nhưng muốn đổi sang màu khác được không?",
        "intent":     "rag",
        "sub_intent": "policy",
        "note":       "KHÓ: có tên SP nhưng intent là policy/đổi trả",
    },
    {
        "id": 53,
        "query":      "khi mua iphone 16 ở đây thì bảo hành mấy năm?",
        "intent":     "rag",
        "sub_intent": "policy",
        "note":       "KHÓ: có tên SP + hỏi bảo hành — dễ nhầm tool",
    },

    # ══════════════════════════════════════════════════════════
    # UNKNOWN — 7 câu (tăng dần tính đánh lừa)
    # ══════════════════════════════════════════════════════════
    {
        "id": 54,
        "query":      "thời tiết hà nội hôm nay thế nào?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "Hoàn toàn ngoài scope",
    },
    {
        "id": 55,
        "query":      "kết quả bóng đá tối qua như nào vậy?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "Thể thao — ngoài scope",
    },
    {
        "id": 56,
        "query":      "giá bitcoin hôm nay bao nhiêu đô?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "KHÓ: có từ 'giá' nhưng bitcoin ≠ sản phẩm điện tử",
    },
    {
        "id": 57,
        "query":      "giá xăng hôm nay tăng không?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "KHÓ: có từ 'giá' nhưng xăng ≠ sản phẩm",
    },
    {
        "id": 58,
        "query":      "bạn có thể viết bài luận về biến đổi khí hậu giúp tôi không?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "Yêu cầu tạo nội dung — ngoài scope",
    },
    {
        "id": 59,
        "query":      "nhà hàng nào ở quận 1 ngon và rẻ vậy?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "Nhà hàng — ngoài scope",
    },
    {
        "id": 60,
        "query":      "giá cổ phiếu apple hôm nay là bao nhiêu?",
        "intent":     "unknown",
        "sub_intent": "unknown",
        "note":       "KHÓ NHẤT: Apple + giá nhưng là cổ phiếu, không phải sản phẩm",
    },
]
