import streamlit as st
from openai import OpenAI
import os

# Hàm đọc nội dung từ file văn bản với xử lý lỗi
def rfile(name_file, default_content=""):
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        st.warning(f"Cảnh báo: Không tìm thấy file '{name_file}'. Sử dụng nội dung mặc định.")
        return default_content

# Tải CSS từ file ngoài - nên đặt ở đầu để tải style trước
st.markdown(f"<style>{rfile('style.css')}</style>", unsafe_allow_html=True)

# Hiển thị logo (nếu có)
if os.path.exists("logo.png"):
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logo.png", use_container_width=True)

# Hiển thị tiêu đề
title_content = rfile("00.xinchao.txt", "Trợ lý AI")
st.markdown(
    f"""<h1 style="text-align: center; font-size: 24px;">{title_content}</h1>""",
    unsafe_allow_html=True
)

# Lấy OpenAI API key từ st.secrets và kiểm tra
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Chưa cấu hình OpenAI API key. Vui lòng thêm vào Streamlit secrets.")
    st.stop()

# Khởi tạo OpenAI client
client = OpenAI(api_key=openai_api_key)

# Khởi tạo tin nhắn "system" và "assistant" với giá trị mặc định
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": rfile("01.system_trainning.txt", "Bạn là một trợ lý ảo hữu ích.")}
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": rfile("02.assistant.txt", "Chào Sếp, em có thể giúp gì cho Sếp hôm nay?")}

# Kiểm tra nếu chưa có session lưu trữ thì khởi tạo tin nhắn ban đầu
if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# Hiển thị lịch sử tin nhắn (loại bỏ system để tránh hiển thị)
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.markdown(f'<div class="assistant">{message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "user":
        st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)

# Ô nhập liệu cho người dùng
if prompt := st.chat_input("Sếp nhập nội dung cần trao đổi ở đây nhé?"):
    # Lưu tin nhắn người dùng vào session
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user">{prompt}</div>', unsafe_allow_html=True)

    # Tạo phản hồi từ API OpenAI với xử lý lỗi
    try:
        # Giới hạn lịch sử tin nhắn để tiết kiệm chi phí và token
        messages_to_send = [st.session_state.messages[0]] + st.session_state.messages[-10:]

        response = ""
        stream = client.chat.completions.create(
            model=rfile("module_chatgpt.txt", "gpt-3.5-turbo").strip(),
            messages=[{"role": m["role"], "content": m["content"]} for m in messages_to_send],
            stream=True,
        )

        # Ghi lại phản hồi của trợ lý vào biến
        for chunk in stream:
            if chunk.choices:
                response += chunk.choices[0].delta.content or ""

        # Hiển thị phản hồi của trợ lý
        st.markdown(f'<div class="assistant">{response}</div>', unsafe_allow_html=True)

        # Cập nhật lịch sử tin nhắn trong session
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"Đã có lỗi xảy ra khi kết nối với AI: {e}")
        # Xóa tin nhắn người dùng vừa gửi để họ có thể thử lại mà không bị trùng lặp
        st.session_state.messages.pop()
