"""
ocr_helper.py
Nhận dạng sản phẩm điện tử từ ảnh qua GPT-4o-mini Vision API.

Chi phí:
  - Low detail: ~85 tokens/ảnh ≈ $0.000013/ảnh với gpt-4o-mini
  - Cực rẻ, cùng model đang dùng cho classifier và response

Pipeline:
  image_bytes → base64 → GPT-4o-mini Vision → JSON {brand, model, full_name}
                                                    ↓
  → Trả về dict chuẩn cho frontend xử lý
"""
import os
import io
import base64
import json
import openai
from dotenv import load_dotenv

load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".env"
))

_VISION_PROMPT = """\
Đây là ảnh sản phẩm điện tử (điện thoại, laptop, tablet, tai nghe, v.v.).
Hãy xác định tên đầy đủ của sản phẩm trong ảnh.

Trả về JSON với các trường sau (không thêm gì khác ngoài JSON):
{
  "brand":      "Tên thương hiệu (Samsung, Apple, Xiaomi...)",
  "model":      "Tên model cụ thể (Galaxy S25 Ultra, iPhone 16 Pro Max...)",
  "full_name":  "Tên đầy đủ đúng chuẩn thương mại",
  "confidence": "high hoặc medium hoặc low"
}

Nếu không xác định được sản phẩm điện tử rõ ràng:
{"recognizable": false}
"""


def analyze_product_image(image_bytes: bytes, mime_type: str = "jpeg") -> dict:
    """
    Phân tích ảnh để nhận dạng sản phẩm điện tử.

    Args:
        image_bytes: Raw bytes của ảnh (JPEG/PNG/WebP/GIF).
        mime_type:   Định dạng ảnh: "jpeg", "png", "webp", "gif".
                     Dùng để xây dựng đúng data URL cho API.

    Returns:
        Thành công:
          {
            "success":    True,
            "brand":      str,    # "Samsung"
            "model":      str,    # "Galaxy S25 Ultra"
            "full_name":  str,    # "Samsung Galaxy S25 Ultra"
            "confidence": str,    # "high" | "medium" | "low"
          }
        Thất bại:
          {
            "success": False,
            "error":   str     # Lý do thất bại
          }
    """
    if not image_bytes:
        return {"success": False, "error": "Không có dữ liệu ảnh."}

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY chưa được cấu hình."}

    # Chuẩn hóa mime_type (Streamlit trả về "image/jpeg" → chỉ lấy phần sau "/")
    if "/" in mime_type:
        mime_type = mime_type.split("/")[-1]
    if mime_type == "jpg":
        mime_type = "jpeg"

    # Encode ảnh thành base64 data URL
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/{mime_type};base64,{b64}"

    try:
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=150,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":    data_url,
                                "detail": "low",   # Low = rẻ hơn, đủ để nhận dạng tên sp
                            },
                        },
                        {
                            "type": "text",
                            "text": _VISION_PROMPT,
                        },
                    ],
                }
            ],
        )

        raw    = response.choices[0].message.content.strip()
        result = json.loads(raw)

        # LLM báo không nhận dạng được
        if result.get("recognizable") is False or not result.get("full_name"):
            return {
                "success": False,
                "error":   "Không nhận dạng được sản phẩm điện tử trong ảnh.",
            }

        return {
            "success":    True,
            "brand":      result.get("brand",      ""),
            "model":      result.get("model",      ""),
            "full_name":  result.get("full_name",  ""),
            "confidence": result.get("confidence", "medium"),
        }

    except json.JSONDecodeError:
        return {"success": False, "error": "Lỗi phân tích phản hồi từ LLM."}

    except Exception as e:
        return {"success": False, "error": f"Lỗi API: {str(e)}"}
