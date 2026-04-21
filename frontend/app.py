import streamlit as st
import sys
import os

# Đảm bảo frontend có thể import được các module từ thư mục root (datn)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator.orchestrator import Orchestrator
from backend.llm.response_generator import generate_response

# Khởi tạo trang Web bằng Streamlit
st.set_page_config(page_title="AI Chatbot Thương Mại", page_icon="🤖", layout="centered")
st.title("🤖 Trợ Lý Ảo Chatbot Bán Hàng Điện Tử")
st.caption("DATN - Đồ án tốt nghiệp: RAG + Tool Calling")

# Khởi tạo Orchestrator dạng Singleton (Lưu trong Session state để không phải tạo lại khi load)
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

# Khởi tạo mảng lưu trữ Lịch sử trò chuyện
if "messages" not in st.session_state:
    st.session_state.messages = []

# Vẽ lại toàn bộ tin nhắn cũ lên màn hình mỗi khi tương tác
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Khung nhập text ở dưới cùng
user_query = st.chat_input("Hỏi tôi về thông tin sản phẩm, chính sách, v.v...")

if user_query:
    # 1. In câu hỏi của người dùng ra màn hình và lưu vào mảng
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. In câu trả lời của Bot ra màn hình
    with st.chat_message("assistant"):
        # Hiển thị icon Loading chờ xử lý AI
        with st.spinner("Đang suy nghĩ..."):
            
            # --- ĐOẠN CORE: Gọi vào Backend của bạn ---
            # Bước A: Chạy qua não bộ Orchestrator
            orch_result = st.session_state.orchestrator.handle_query(user_query)
            
            # Bước B: Gọi LLM (OpenAI) để sinh chữ tự nhiên
            llm_result = generate_response(orch_result, query=user_query)
            
            # Lấy text cuối cùng từ LLM
            final_text = llm_result["text"]
            
        # Hiển thị chữ lên màn hình
        st.markdown(final_text)
        
        # Tùy chọn in thêm thông tin Debug (để thầy cô xem cho rõ luồng dữ liệu JSON)
        with st.expander("🛠️ Xem luồng tư duy ẩn (JSON)"):
            st.json(orch_result)

    # Lưu câu của bot vào mảng lịch sử
    st.session_state.messages.append({"role": "assistant", "content": final_text})
