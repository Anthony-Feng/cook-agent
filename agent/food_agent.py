import ollama
from tools import recommend_recipe, calculate_calories, search_web, analyze_image_contents

class FoodAgent:
    def __init__(self):
        # ================== 模型配置 ==================
        #self.model_select = "llama3.2:1b-instruct-q4_0"
        self.model_select = "llama3.1:8b-instruct-q5_K_M"
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
                    "description": "STRICT LIMITATION: Query the local PRODUCTION or FARMING status of only ONE specific food item at a time. Trigger this tool when the user asks about the origin, local farming, harvest, or availability of locally grown produce in a specific location (e.g., 'Is this grown in HK?', 'Local farms for...'). Even if multiple items are mentioned, extract only the most relevant one.",
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
    def chat(self, user_input, image_base64=None):  # 把参数名改为
        if image_base64 :
            self.current_image_base64 = image_base64
            # 给用户的输入加上一个显式的【系统标记】
            # 这就像是对 AI 眨了下眼，提示它去调用工具
            contextual_input = user_input + "\n(System: The user has uploaded an image. )"
        else:
            contextual_input = user_input + "\n(no image. )"
        #print(contextual_input)
        self.messages.append({"role": "user", "content": contextual_input})

        # 3. 让 Llama 决定调用工具
        response = ollama.chat(
            model=self.model_select,
            messages=self.messages,
            tools=self.tools,
        )

        tool_results = []
        # 4. 执行工具
        if response.message.tool_calls:
            if len(response.message.tool_calls) > 0:
                for tool_call in response.message.tool_calls:
                    print('tool_call',tool_call)
                    func_name = tool_call.function.name
                    args = tool_call.function.arguments

                    if func_name == "recommend_recipe":
                        res = recommend_recipe(**args)
                        tool_results.append(("recipe", res))

                    elif func_name == "calculate_calories":
                        res = calculate_calories(**args)
                        tool_results.append(("calories", res))

                    elif func_name == "search_web":
                        res = search_web(**args)
                        tool_results.append(("web", res))
                        # --- 核心改进：解决你说的“随便答”问题 ---
                        # 如果 LLM 想调工具，但它给的工具名（如 create_limerick）不在上面那三个里面
                        # 那么 tool_results 此时就是空的。
                    elif func_name == "analyze_image_contents":
                        # 这里的 self.analyze_image_contents 会调用视觉模型并返回 "I have..."
                        res = analyze_image_contents(self)
                        tool_results.append(("vision", res))
                if not tool_results:
                    # 默默删掉刚才那个错误的工具意图，不让它污染记忆
                    # 重新请求，这次完全不传 tools 参数，强迫它“随便答”
                    fallback_response = ollama.chat(
                        model=self.model_select,
                        messages=self.messages
                    )
                    self.messages.append(fallback_response.message)
                    return fallback_response, []
            # 4. 如果 LLM 本来就没想调工具 (len == 0)
        else:
            # 直接保存并返回普通对话
            self.messages.append(response.message)
            return response, []

        return response, tool_results
