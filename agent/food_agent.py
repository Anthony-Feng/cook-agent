import ollama
from tools import recommend_recipe, calculate_calories, search_web, analyze_image_contents
from config import MODEL_SELECT
class FoodAgent:
    def __init__(self):
        # ================== 模型配置 ==================
        self.model_select = MODEL_SELECT
        # ================== 【短期记忆核心】对话历史 ==================
        self.messages = [
            {
                "role": "system",
                "content": """
                You are a professional food assistant.
                1. Use provided tools ONLY when the user asks for a recipe, nutrition analysis, or local farming info.
                2. For general greetings, jokes, poems, or non-food topics, respond DIRECTLY and naturally in plain text.
                3. Do NOT explain why you are or are not using a tool. Just provide the answer.
                """
            }
        ]
        # ================== Tool Schema -> belongs MCP Protocol ==================
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "recommend_recipe",
                    "description": "Recommend a healthy recipe based on ingredients.If user add/drop or have/not have something",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ingredients": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of ingredients with 'Recipe',for example 'Carrots,eggs,ham,corn Recipe'."
                            }
                        },
                        "required": ["ingredients"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_calories",
                    "description": "Calculate Nutritional(e.g. calories) for a list of foods with weight and unit. Extract input into format: 'weight food and weight food and weight food'. Example: '1lb brisket and 1kg fries and 500g apple'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipe_text": {
                                "type": "string",
                                "description": "Food list strictly in this format: 'weight+food+and+weight+food+and+weight+food...'. Example: '1lb brisket and 1kg fries and 500g apple',If no weight, use default 1lb"
                            }
                        },
                        "required": ["recipe_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "STRICT LIMITATION: Query the PRODUCTION or FARMING status of only ONE specific food item at a time. Trigger this tool when the user asks about the origin, local farming, harvest, or availability of locally grown produce in a specific location (e.g., 'Is this grown in HK?', 'Local farms for...'). Even if multiple items are mentioned, extract only the most relevant one.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Format: [Single Item Name] + 'local production OR agriculture' + [Location, e.g., Hong Kong]. Example: 'strawberry local production farming Hong Kong'. Do not include multiple items or price-related keywords."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'analyze_image_contents',
                    'description': 'CRITICAL: Call this tool ONLY IF there is a system notification stating an image has been uploaded. This tool performs visual analysis on the uploaded photo to identify ingredients.',
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                    },
                },
            }
        ]

    # ==================agent_core 核心：带记忆的对话 ==================
    def chat(self, user_input, image_base64=None):
        if image_base64:
            self.current_image_base64 = image_base64
            contextual_input = user_input + "\n(System: The user has uploaded an image. )"
        else:
            contextual_input = user_input + "\n(no image. )"

        self.messages.append({"role": "user", "content": contextual_input})

        # 1. 第一次请求：让 Llama 决定是否调用工具
        response = ollama.chat(
            model=self.model_select,
            messages=self.messages,
            tools=self.tools,
        )

        # 情况 A：模型不想调工具，直接回复
        if not response.message.tool_calls:
            self.messages.append(response.message)
            return response, []

        # 情况 B：模型想调工具
        # --- 关键修改 1：必须把 AI 的调用意图存入历史 ---
        self.messages.append(response.message)

        tool_results = []
        for tool_call in response.message.tool_calls:
            func_name = tool_call.function.name
            args = tool_call.function.arguments
            print(func_name,args)
            # 执行工具逻辑
            res = None
            if func_name == "recommend_recipe":
                res = recommend_recipe(**args)  # 注意：这里建议去掉 self，除非你内部真的需要
                tool_results.append(("recipe", res))
            elif func_name == "calculate_calories":
                res = calculate_calories(**args)
                tool_results.append(("calories", res))
            elif func_name == "search_web":
                res = search_web(**args)
                tool_results.append(("web", res))
            elif func_name == "analyze_image_contents":
                res = analyze_image_contents(self)  # 视觉通常需要 self 里的 base64
                tool_results.append(("vision", res))

            # --- 关键修改 2：必须把工具结果【反馈回消息历史】 ---
            if res:
                self.messages.append({
                    "role": "tool",
                    "content": str(res),
                    "name": func_name
                })

        # --- 关键修改 3：再次调用模型，让它根据工具结果生成最终回复 ---
        final_response = ollama.chat(
            model=self.model_select,
            messages=self.messages,
        )

        # 将最终的人类语言回复存入记忆
        self.messages.append(final_response.message)
        return final_response, tool_results
