import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator.orchestrator import Orchestrator
from backend.llm.response_generator import generate_response_stream, generate_suggestions
from backend.memory.memory_manager import MemoryManager
from frontend.stt_helper import transcribe_audio
from frontend.ocr_helper import analyze_product_image
from streamlit_mic_recorder import mic_recorder

# ──────────────────────────────────────────────────────────
# CẤU HÌNH TRANG
# ──────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot Thương Mại", page_icon="🤖", layout="centered")
st.title("🤖 Trợ Lý Ảo Chatbot Bán Hàng Điện Tử")
st.caption("DATN - Đồ án tốt nghiệp: RAG + Tool Calling + Conversation Memory")

# ──────────────────────────────────────────────────────────
# SIDEBAR – Cài đặt + STT
# ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Cài đặt")
    enable_suggestions = st.toggle(
        "💡 Gợi ý câu hỏi tiếp theo",
        value=False,
        help="Bật để AI tự động gợi ý 2-3 câu hỏi follow-up sau mỗi câu trả lời.\n"
             "Lưu ý: Tốn thêm 1 lần gọi API mỗi lượt chat.",
    )
    st.caption("🔴 Tắt = tiết kiệm token  |  🟢 Bật = trải nghiệm đầy đủ")

    st.divider()

    st.subheader("🎤 Nhập bằng giọng nói")
    st.caption("Nhấn nút, nói câu hỏi, nhấn lại để dừng. AI hiểu tiếng Việt.")

    audio = mic_recorder(
        start_prompt="🎤 Nhấn để nói",
        stop_prompt="⏹️ Dừng",
        key="mic_recorder",
        format="webm",
        use_container_width=True,
    )

    if (
        audio
        and audio.get("bytes")
        and audio.get("id") != st.session_state.get("last_audio_id")
    ):
        st.session_state.last_audio_id = audio["id"]
        with st.spinner("🔄 Đang nhận dạng giọng nói..."):
            transcribed = transcribe_audio(audio["bytes"], format="webm")

        if transcribed:
            st.success(f"✅ **{transcribed}**")
            st.session_state.pending_query = transcribed
            st.rerun()
        else:
            st.warning("⚠️ Không nghe rõ, vui lòng nói lại.")

# ──────────────────────────────────────────────────────────
# KHỞI TẠO SESSION STATE
# ──────────────────────────────────────────────────────────
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

if "memory" not in st.session_state:
    st.session_state.memory = MemoryManager()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_summary" not in st.session_state:
    st.session_state.conversation_summary = ""

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if "suggestions" not in st.session_state:
    st.session_state.suggestions = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ──────────────────────────────────────────────────────────
# HIỂN THỊ LỊCH SỬ TIN NHẮN
# ──────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Render lại ảnh đã đính kèm (nếu có)
        if msg.get("image_bytes"):
            st.image(msg["image_bytes"], width=220)
            if msg.get("ocr_label"):
                st.caption(msg["ocr_label"])
        # Hiển thị text gốc (không phải enriched pipeline query)
        st.markdown(msg.get("content_display", msg["content"]))

# ──────────────────────────────────────────────────────────
# GỢI Ý CÂU HỎI TIẾP THEO
# ──────────────────────────────────────────────────────────
if st.session_state.suggestions:
    st.markdown("💡 **Bạn có thể hỏi tiếp:**")
    cols = st.columns(len(st.session_state.suggestions))
    for i, (col, sug) in enumerate(zip(cols, st.session_state.suggestions)):
        if col.button(f"💬 {sug}", key=f"sug_{i}", use_container_width=True):
            st.session_state.pending_query = sug
            st.session_state.suggestions = []
            st.rerun()

# ──────────────────────────────────────────────────────────
# CHAT INPUT – có nút "+" đính kèm ảnh tích hợp sẵn
# accept_file=True → Streamlit tự thêm nút 📎 cạnh input bar
# Người dùng có thể gửi: chỉ text | text + ảnh | chỉ ảnh
# ──────────────────────────────────────────────────────────
msg = st.chat_input(
    "Hỏi về sản phẩm, giá, tồn kho, chính sách...",
    accept_file=True,      # Nút 📎 hiện ngay cạnh input bar ← đây là cái bạn muốn
)

# ── Xác định nguồn input: pending (suggestion/STT) hay chat_input ──
user_query    = None
uploaded_file = None

if st.session_state.pending_query:
    user_query = st.session_state.pending_query
    st.session_state.pending_query = None

elif msg:
    text  = (msg.text or "").strip()
    files = getattr(msg, "files", None) or []
    uploaded_file = files[0] if files else None

    if text:
        user_query = text
    elif uploaded_file:
        # Chỉ gửi ảnh, không kèm text → tự sinh query mặc định
        user_query = "Cho tôi biết sản phẩm trong ảnh này"

# ──────────────────────────────────────────────────────────
# XỬ LÝ TIN NHẮN
# ──────────────────────────────────────────────────────────
if user_query is not None:
    st.session_state.suggestions = []

    # ── Xử lý ảnh đính kèm (nếu có) ──────────────────────
    image_bytes    = None
    pipeline_query = user_query   # Query gửi vào backend
    ocr_label      = ""           # Caption hiển thị dưới ảnh

    if uploaded_file:
        # Kiểm tra loại file
        if not uploaded_file.type.startswith("image/"):
            st.warning("⚠️ Chỉ hỗ trợ ảnh (JPG, PNG, WEBP). File vừa gửi sẽ bị bỏ qua.")
            uploaded_file = None
        else:
            image_bytes = uploaded_file.read()
            with st.spinner("🔍 Đang nhận dạng sản phẩm trong ảnh..."):
                ocr = analyze_product_image(image_bytes, mime_type=uploaded_file.type)

            if ocr.get("success"):
                product_name   = ocr["full_name"]
                conf_icon      = "🟢" if ocr["confidence"] == "high" else "🟡"
                pipeline_query = f"[Ảnh sản phẩm: {product_name}] {user_query}"
                ocr_label      = f"{conf_icon} Nhận dạng: **{product_name}**"
            else:
                ocr_label = "⚠️ Không nhận dạng được sản phẩm — xử lý câu hỏi bình thường"

    # ── Hiển thị tin nhắn người dùng ──────────────────────
    with st.chat_message("user"):
        if image_bytes:
            st.image(image_bytes, width=220)
            if ocr_label:
                st.caption(ocr_label)
        st.markdown(user_query)

    # Lưu vào lịch sử:
    #   content          → pipeline_query (enriched, để memory hiểu ngữ cảnh)
    #   content_display  → user_query (text gốc, hiển thị sạch trong chat)
    user_msg_record = {
        "role":            "user",
        "content":         pipeline_query,
        "content_display": user_query,
    }
    if image_bytes:
        user_msg_record["image_bytes"] = image_bytes
        user_msg_record["ocr_label"]   = ocr_label
    st.session_state.messages.append(user_msg_record)

    # ── PHASE 1: Orchestrator ──────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("⚙️ Đang phân tích..."):
            context = st.session_state.memory.build_context(
                st.session_state.messages[:-1],
                st.session_state.conversation_summary,
            )
            orch_result = st.session_state.orchestrator.handle_query(
                pipeline_query,
                conversation_history=context,
            )

        # ── PHASE 2: Stream response ──────────────────────
        stream     = generate_response_stream(orch_result, query=pipeline_query)
        final_text = st.write_stream(stream)

        with st.expander("🛠️ Xem luồng tư duy ẩn (JSON)"):
            st.json(orch_result)

    st.session_state.messages.append({"role": "assistant", "content": final_text})

    # ── PHASE 3: Suggestions ──────────────────────────────
    if enable_suggestions:
        with st.spinner("💡 Đang tạo gợi ý..."):
            st.session_state.suggestions = generate_suggestions(
                orch_result, user_query, final_text
            )
    else:
        st.session_state.suggestions = []

    # ── PHASE 4: Cập nhật bộ nhớ tóm tắt ─────────────────
    if st.session_state.memory.should_summarize(st.session_state.messages):
        with st.spinner("💾 Đang cập nhật bộ nhớ hội thoại..."):
            st.session_state.conversation_summary = st.session_state.memory.summarize(
                st.session_state.messages,
                st.session_state.conversation_summary,
            )

    st.rerun()
