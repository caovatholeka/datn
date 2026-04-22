import streamlit as st
import sys
import os

# Đảm bảo frontend có thể import được các module từ thư mục root (datn)
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
# SIDEBAR – Cài đặt
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

    # ──────────────────────────────────────────────────────────
    # NHẬP BẶNG GIỌNG NÓI (Speech-to-Text)
    # ──────────────────────────────────────────────────────────
    st.subheader("🎤 Nhập bằng giọng nói")
    st.caption("Nhấn nút, nói câu hỏi, nhấn lại để dừng. AI sẽ tự động hiểu tiếng Việt.")

    audio = mic_recorder(
        start_prompt="🎤 Nhấn để nói",
        stop_prompt="⏹️ Dừng",
        key="mic_recorder",
        format="webm",          # Chrome/Edge xuất webm, Whisper hỗ trợ sẵn
        use_container_width=True,
    )

    # Xử lý audio mới (dùng ID để tránh xử lý lặp khi Streamlit rerun)
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

    st.divider()

    # ──────────────────────────────────────────────────────────
    # NHẬN DẠNG SẢN PHẨM QUA ẢNH (Vision OCR)
    # ──────────────────────────────────────────────────────────
    st.subheader("📸 Nhận dạng sản phẩm qua ảnh")
    st.caption("Upload ảnh sản phẩm → AI tự động nhận diện và gợi ý hồi.")

    uploaded_img = st.file_uploader(
        label="Chọn ảnh sản phẩm",
        type=["jpg", "jpeg", "png", "webp"],
        key="product_image",
        label_visibility="collapsed",
    )

    if uploaded_img:
        # Hash để tránh gọi API lại với cùng 1 ảnh khi Streamlit rerun
        file_hash = f"{uploaded_img.name}_{uploaded_img.size}"
        image_bytes = uploaded_img.read()   # Đọc bytes 1 lần, dùng cho cả preview lấn OCR

        # Hiển thị preview ảnh luôn luôn
        st.image(image_bytes, use_container_width=True)

        # Chỉ gọi API khi ảnh mới (chưa xử lý lần nào)
        if file_hash != st.session_state.get("last_ocr_hash"):
            st.session_state.last_ocr_hash = file_hash
            st.session_state.ocr_result    = None  # Reset kết quả cũ
            mime = uploaded_img.type       # vd: "image/jpeg"
            with st.spinner("🔍 Đang nhận dạng sản phẩm..."):
                st.session_state.ocr_result = analyze_product_image(image_bytes, mime)

        # Hiển thị kết quả và nút hành động
        ocr = st.session_state.get("ocr_result")
        if ocr:
            if ocr.get("success"):
                product_name = ocr["full_name"]
                conf_icon = "🟢" if ocr["confidence"] == "high" else "🟡"
                st.markdown(f"{conf_icon} **{product_name}**")
                st.markdown("**Hỏi về sản phẩm này:**")
                c1, c2, c3 = st.columns(3)
                if c1.button("💰 Giá", key="ocr_price", use_container_width=True):
                    st.session_state.pending_query = f"{product_name} giá bao nhiêu?"
                    st.rerun()
                if c2.button("📦 Tồn kho", key="ocr_stock", use_container_width=True):
                    st.session_state.pending_query = f"{product_name} còn hàng không?"
                    st.rerun()
                if c3.button("ℹ️ Thông tin", key="ocr_info", use_container_width=True):
                    st.session_state.pending_query = f"Thông tin chi tiết về {product_name}"
                    st.rerun()
            else:
                st.error(f"❌ {ocr.get('error', 'Không nhận dạng được')}")
    else:
        # Người dùng xóa ảnh → reset cache
        st.session_state.last_ocr_hash = None
        st.session_state.ocr_result    = None

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

# Cache kết quả OCR để không gọi API lại khi Streamlit rerun
if "last_ocr_hash" not in st.session_state:
    st.session_state.last_ocr_hash = None

if "ocr_result" not in st.session_state:
    st.session_state.ocr_result = None

# Gợi ý câu hỏi tiếp theo (hiển thị sau mỗi lượt trả lời)
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []

# Query được kích hoạt bởi click vào nút gợi ý
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ──────────────────────────────────────────────────────────
# HIỂN THỊ LỊCH SỬ TIN NHẮN
# ──────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ──────────────────────────────────────────────────────────
# GỢI Ý CÂU HỎI TIẾP THEO (hiển thị phía dưới lịch sử)
# ──────────────────────────────────────────────────────────
if st.session_state.suggestions:
    st.markdown("💡 **Bạn có thể hỏi tiếp:**")
    cols = st.columns(len(st.session_state.suggestions))
    for i, (col, sug) in enumerate(zip(cols, st.session_state.suggestions)):
        if col.button(f"💬 {sug}", key=f"sug_{i}", use_container_width=True):
            st.session_state.pending_query = sug
            st.session_state.suggestions = []   # Xóa gợi ý cũ sau khi click
            st.rerun()

# ──────────────────────────────────────────────────────────
# XỬ LÝ INPUT (từ nút gợi ý hoặc chat_input)
# ──────────────────────────────────────────────────────────
# Ưu tiên pending_query (từ nút click) nếu có
if st.session_state.pending_query:
    user_query = st.session_state.pending_query
    st.session_state.pending_query = None
else:
    user_query = st.chat_input("Hỏi tôi về thông tin sản phẩm, chính sách, v.v...")

if user_query:
    # Xóa gợi ý cũ khi người dùng tự nhập câu mới
    st.session_state.suggestions = []

    # ── Hiển thị câu hỏi người dùng ──
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # ── Xử lý và hiển thị câu trả lời ──
    with st.chat_message("assistant"):

        # PHASE 1: Orchestrator (chạy ngầm, chỉ hiển thị spinner)
        with st.spinner("⚙️ Đang phân tích..."):
            context = st.session_state.memory.build_context(
                st.session_state.messages[:-1],
                st.session_state.conversation_summary,
            )
            orch_result = st.session_state.orchestrator.handle_query(
                user_query,
                conversation_history=context,
            )

        # PHASE 2: Stream câu trả lời LLM từng chữ
        stream    = generate_response_stream(orch_result, query=user_query)
        final_text = st.write_stream(stream)   # hiện chữ từng ký tự, trả về full text

        # Debug: xem luồng tư duy ẩn
        with st.expander("🛠️ Xem luồng tư duy ẩn (JSON)"):
            st.json(orch_result)

    # ── Lưu câu trả lời vào lịch sử ──
    st.session_state.messages.append({"role": "assistant", "content": final_text})

    # PHASE 3: Sinh gợi ý câu hỏi tiếp theo (chỉ khi toggle bật)
    if enable_suggestions:
        with st.spinner("💡 Đang tạo gợi ý..."):
            st.session_state.suggestions = generate_suggestions(
                orch_result, user_query, final_text
            )
    else:
        st.session_state.suggestions = []  # Xóa gợi ý cũ nếu toggle đang tắt

    # PHASE 4: Cập nhật bộ nhớ tóm tắt (nếu đến ngưỡng)
    if st.session_state.memory.should_summarize(st.session_state.messages):
        with st.spinner("💾 Đang cập nhật bộ nhớ hội thoại..."):
            st.session_state.conversation_summary = st.session_state.memory.summarize(
                st.session_state.messages,
                st.session_state.conversation_summary,
            )

    # Rerun để hiển thị gợi ý ở đúng vị trí (phía trên chat_input)
    st.rerun()
