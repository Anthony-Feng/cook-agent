import requests
import json
import ollama


# ================== 工具2：卡路里计算 ==================
def calculate_calories(self, recipe_text):
    api_key = "bTXJdDVjjDAFpuyGdzFVKvd2cb1nSH2HFanmM6Ou"
    url = f'https://api.api-ninjas.com/v1/nutrition?query={recipe_text}'

    # 1. 获取原始营养数据
    response = requests.get(url, headers={'X-Api-Key': api_key})
    nutritional_list = []
    if response.status_code == 200:
        nutritional_list = response.json()

    # 2. 优化 Prompt，加入换算逻辑
    # 我们把 API 的原始结果 json.dumps 进去，让 LLM 看到每 100g 的数值
    prompt = f"""
            # Role
            You are an expert Nutritionist AI assistant.

            # Context
            - User's Requested Ingredients/Weights: {recipe_text}
            - API Raw Nutrition Data (per 100g or per serving): {json.dumps(nutritional_list)}

            # Task
            Calculate the nutrition for the **ACTUAL WEIGHTS** specified in the User's request. 
            Do NOT just copy the API data if the weights differ.

            # Calculation Rules
            1. **Scaling**: If the API provides data for 100g but the user asks for 500g, multiply all values by 5.
            2. **Unit Matching**: Carefully match the "name" in API data with the "Food Item" in user text.
            3. **Missing Data**: If {nutritional_list} is empty or missing an item, use your internal USDA knowledge to estimate for the specific weight requested.
            4. **Cooking Oil**: Add ~10g oil (90 kcal, 10g fat) for any cooked/stir-fried dish.
            5. **Total**: Provide a clear sum of all items.

            # Output Rules
            1. Output ONLY the Markdown table and assumptions.
            2. NO preamble like "Here is the analysis...".
            3. Use ENGLISH.

            # Output Format
            ### 🥗 Nutritional Analysis
            **Assumptions & Calculations:**
            - [Explain how you scaled the API data to the user's weights, e.g., "Scaled 100g API data to 250g for Steak"]
            - [List other assumptions]

            | Food Item | Est. Weight | Calories (kcal) | Protein (g) | Carbs (g) | Fat (g) |
            | :--- | :--- | :--- | :--- | :--- | :--- |
            | [Item 1] | [Target]g | [Scaled Value] | [Value] | [Value] | [Value] |
            | **Total** | **-** | **[Sum]** | **[Sum]** | **[Sum]** | **[Sum]** |

            **Dietary Note:**
            [1-sentence professional insight]
            """

    res = ollama.chat(model=self.model_select, messages=[{"role": "user", "content": prompt}])
    return res.message.content