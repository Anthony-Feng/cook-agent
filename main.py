from agent.food_agent import FoodAgent
import streamlit as st
import base64

def encode_image_to_base64(uploaded_file):
    if uploaded_file is not None:
        # 使用 getvalue() 获取字节流，比直接 read() 更安全
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
            5.Output natural language.
            """
        }
    ]
    st.session_state["input_text"] = ""


# ================== Streamlit 界面 ==================
if __name__ == "__main__":
    st.title("🍳 AI Recipe & Nutrition Assistant")
    # 初始化 agent 和对话历史
    if "agent" not in st.session_state:
        st.session_state.agent = FoodAgent()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.subheader("📝 session log")
    chat_container = st.container(height=350)  # 👌 固定高度 600px！
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.write(f"**You:** {chat['content']}")
                # 假设你在循环中，当前变量名是 chat
                # 遍历渲染聊天记录
                if chat.get("images"):
                    img_data = chat["images"]

                    # 1. 确保 Base64 格式头正确
                    if isinstance(img_data, str) and not img_data.startswith("data:image"):
                        img_display = f"data:image/jpeg;base64,{img_data}"
                    else:
                        img_display = img_data

                    try:
                        # 2. 设置固定宽度并关闭容器自适应
                        st.image(
                            img_display,
                            caption="Uploaded Image",
                            width=200  # 直接给数字，Streamlit 默认就不再是 'stretch' 了
                        )
                    except Exception as e:
                        st.error(f"Display Error: {e}")
                st.divider()
            else:
                st.write(f"**AI:** {chat['content']}")
                st.divider()

    # 1. 初始化一个用于控制组件“版本”的计数器
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    if "persistent_image" not in st.session_state:
        st.session_state.persistent_image = None

    col0_inner1, col0_inner2 = st.columns([5, 2])

    with col0_inner1:
        # 2. 将 key 绑定到计数器上
        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=["jpg", "jpeg", "png"],
            key=f"file_uploader_{st.session_state.uploader_key}"
        )

        # 同步状态
        if uploaded_file:
            st.session_state.persistent_image = uploaded_file
    # ----------------------
    # 输入框&Send&Clear
    # ----------------------
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        user_input = st.text_input(
            "text_input",
            label_visibility="collapsed",
            placeholder="Enter information about the food, and I will assist.",
            key="input_text",
            #on_change=handle_submit
        )
    with col2:
        send_button = st.button("Send", use_container_width=True, key="send_button",
                                #on_click=handle_submit
        )
    with col3:
        clear_button = st.button("Clear", use_container_width=True, on_click=clear_chat)


    # ----------------------
    # 发送按钮逻辑
    # ----------------------
    if send_button and (user_input or uploaded_file):
        #=======================================
        image_base64 = None
        if uploaded_file:
            image_base64 = encode_image_to_base64(uploaded_file)
        # =======================================
        with st.spinner("AI Thinking..."):
            agent = st.session_state.agent
            response, tool_results = agent.chat(user_input, image_base64=image_base64)
            # # 保存用户消息
            st.session_state.chat_history.append({"role": "user", "content": user_input,"images": image_base64})

            # 组装AI回复
            ai_content = ""
            if tool_results:
                ai_content += f"✅ Used {len(tool_results)} tool(s)\n\n"
                for typ, result in tool_results:
                    if typ == "recipe":
                        ai_content += "📋 Recipe\n\n"
                    elif typ == "calories":
                        ai_content += "🔥 Calories Analysis\n\n"
                    elif typ == "web":
                        ai_content += "🔍 Web Search\n\n"
                    elif typ == "vision":
                        ai_content += "🥗 Vision\n\n"
                    ai_content += result + "\n\n"
            else:
                raw_content = response.message.content

                # --- 核心改进：拦截并清洗 JSON 幻觉 ---
                # 检查内容是否包含类似 {"name": ...} 的结构
                if '{"name":' in raw_content or '{"parameters":' in raw_content:
                    # 如果检测到 JSON，说明模型“误吐”了工具调用指令
                    # 我们可以提示它重新说话，或者显示一个友好的占位符
                    ai_content += "💬 (I'm processing your request... Please try to ask more specifically if I missed it.)"
                elif not raw_content.strip():
                    # 如果内容完全为空（有时 Tool Call 失败会导致 content 为空）
                    ai_content += "💬 I'm here to help! Could you tell me more about what you're looking for?"
                else:
                    # 正常的对话回复
                    ai_content += raw_content


                # 保存AI消息
            st.session_state.chat_history.append({"role": "assistant", "content": ai_content})
            st.rerun()