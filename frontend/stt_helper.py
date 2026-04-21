"""
stt_helper.py
Speech-to-Text helper sử dụng OpenAI Whisper API.

Nhận audio bytes từ streamlit-mic-recorder
→ Gọi Whisper API → Trả về text tiếng Việt.

Tại sao Whisper thay vì Google STT miễn phí?
  - Chính xác hơn với accent tiếng Việt đa dạng
  - Không cần thêm dependency phức tạp (pyaudio, sounddevice...)
  - Cùng API key với phần còn lại của dự án
  - Chi phí: ~$0.0005 / 5 giây nói = cực rẻ
"""
import io
import os
import openai
from dotenv import load_dotenv

load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".env"
))


def transcribe_audio(audio_bytes: bytes, format: str = "webm") -> str:
    """
    Transcribe audio bytes thành text tiếng Việt qua OpenAI Whisper API.

    Args:
        audio_bytes: Raw audio bytes từ streamlit-mic-recorder.
        format:      Định dạng file âm thanh ("webm", "wav", "mp3"...).
                     Chrome/Edge thường xuất webm, Safari xuất mp4.

    Returns:
        Chuỗi text đã nhận dạng, hoặc "" nếu có lỗi / không nghe thấy gì.
    """
    if not audio_bytes:
        return ""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    try:
        client = openai.OpenAI(api_key=api_key)

        # Bọc bytes vào file-like object với tên file đúng extension
        # (Whisper API dùng extension để xác định format)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"recording.{format}"

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="vi",              # Tiếng Việt — tăng accuracy
            prompt="Câu hỏi về điện thoại, laptop, tồn kho, giá cả, bảo hành.",
            # Prompt giúp Whisper hiểu ngữ cảnh → nhận dạng tên sản phẩm tốt hơn
        )

        text = transcript.text.strip()

        # Lọc các trường hợp Whisper trả về câu thừa kiểu "Cảm ơn bạn đã xem."
        # khi không nghe thấy gì
        noise_patterns = ["thank you", "cảm ơn", "bye", "tạm biệt"]
        if len(text) < 3 or any(text.lower().startswith(p) for p in noise_patterns):
            return ""

        return text

    except Exception:
        return ""
