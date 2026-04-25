import ollama

# ================== 工具4：图片识别 ==================
def analyze_image_contents(self, **kwargs):
    """
    视觉识别工具：当用户上传了图片且需要识别其中的食材时调用。
    """
    if not hasattr(self, 'current_image_base64') or not self.current_image_base64:
        return "wrong：no img upload，cant analyze"

    try:
        # 调用视觉模型进行分析
        res = ollama.chat(
            model='llama3.2-vision',
            messages=[{
                'role': 'user',
                'content': 'Identify all food items, vegetables, or fruits in this image. Format: "I have item1, item2, item3".',
                'images': [self.current_image_base64]
            }]
        )
        self.messages.append({
            "role": "user",  # 角色是 tool
            "content": res.message.content
        })
        # 【进阶技巧】为了防止它下一轮再看一遍，识别完后立刻清空临时图片
        self.current_image_base64 = None
        return res.message.content.strip()
    except Exception as e:
        return f"vision error: {str(e)}"