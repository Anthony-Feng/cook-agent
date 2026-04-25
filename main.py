import streamlit as st
import base64
from agent.food_agent import FoodAgent


# ================== 工具函数 ==================

def encode_image_to_base64(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    return None


def clear_chat():
    st.session_state.chat_history = []
    st.session_state.agent.messages = [
        {
            "role": "system",
            "content": """
            You are a professional food assistant.
            Rules:
            1. If user input contains ANY food/ingredient/dish → MUST use at least ONE tool.
            2. Only use provided tools.
            3. Use Ollama tool call format.
            4. Do NOT output raw JSON,dict.
            5. Output natural language.
            """
        }
    ]
    # 同时重置输入版本，清空当前的输入框
    st.session_state.input_version += 1


# ================== Streamlit 界面 ==================
st.set_page_config(page_title="AI Recipe Assistant", layout="centered")

# 1. 初始化状态变量
if "agent" not in st.session_state:
    st.session_state.agent = FoodAgent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "input_version" not in st.session_state:
    st.session_state.input_version = 0

st.title("🍳 AI Recipe & Nutrition Assistant")

# 2. 聊天记录显示区
st.subheader("📝 session log")
chat_container = st.container(height=400)
with chat_container:
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.write(f"**You:** {chat['content']}")
            if chat.get("images"):
                img_data = chat["images"]
                if isinstance(img_data, str) and not img_data.startswith("data:image"):
                    img_display = f"data:image/jpeg;base64,{img_data}"
                else:
                    img_display = img_data
                st.image(img_display, caption="Uploaded Image", width=200)
            st.divider()
        else:
            st.write(f"**AI:** {chat['content']}")
            st.divider()

# 3. 输入区域 (使用 input_version 动态生成 key)
current_version = st.session_state.input_version

col0_inner1, col0_inner2 = st.columns([5, 2])
with col0_inner1:
    # 动态 Key 是重置上传组件的关键
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png"],
        key=f"uploader_v_{current_version}"
    )

col1, col2, col3 = st.columns([5, 1, 1])
with col1:
    # 动态 Key 确保文本框也会清空
    user_input = st.text_input(
        "text_input",
        label_visibility="collapsed",
        placeholder="Enter food info...",
        key=f"text_v_{current_version}"
    )

with col2:
    send_button = st.button("Send", use_container_width=True)
with col3:
    st.button("Clear", use_container_width=True, on_click=clear_chat)

# 4. 发送逻辑
if send_button and (user_input or uploaded_file):
    image_base64 = None
    if uploaded_file:
        image_base64 = encode_image_to_base64(uploaded_file)

    with st.spinner("AI Thinking..."):
        # 调用 Agent
        agent = st.session_state.agent
        response, tool_results = agent.chat(user_input, image_base64=image_base64)

        # 保存用户消息
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "images": image_base64
        })

        # 组装回复内容
        ai_content = ""
        if tool_results:
            ai_content += f"✅ Used {len(tool_results)} tool(s)\n\n"
            for typ, result in tool_results:
                headers = {"recipe": "📋 Recipe", "calories": "🔥 Calories", "web": "🔍 Web", "vision": "🥗 Vision"}
                ai_content += f"{headers.get(typ, '🛠 Tool')}\n\n{result}\n\n"
        else:
            raw_content = response.message.content if hasattr(response, 'message') else str(response)
            if '{"' in raw_content:
                ai_content = "💬 Processing your request...Ask again or clear all"
            else:
                ai_content = raw_content if raw_content.strip() else "I'm here to help!"

        # 保存 AI 消息
        st.session_state.chat_history.append({"role": "assistant", "content": ai_content})

        # --- 核心重置逻辑 ---
        # 增加版本号，这会导致下次渲染时 key 变化，从而清空组件
        st.session_state.input_version += 1
        st.rerun()