from duckduckgo_search import DDGS
import trafilatura
import ollama

# ================== 工具1：菜谱生成 ==================
def recommend_recipe(self, ingredients):
    # print('ingredients',ingredients)
    # print(f"🍲 正在搜索组合菜谱: {ingredients}...\n")
    try:
        with DDGS() as ddgs:
            # 一次性获取前 5 条综合结果
            results = ddgs.text(ingredients, max_results=5)

            for i, r in enumerate(results, 1):
                # print(f"[{i}] {r['title']}")
                # print(f"ingredients: {r['body']}")
                # print(f"Link: {r['href']}\n")
                pass
        url = r['href']
        # 下载网页内容
        downloaded = trafilatura.fetch_url(url)
        # 提取正文（过滤广告、导航）
        text = trafilatura.extract(downloaded)
        # print('url main text',text)
    except Exception as e:
        print(f"search wrong: {e}")
    messages = [
        {
            "role": "user",
            "content": f"""
        Please refer to the MAIN RECIPE CONTENT from the webpage text below:
        -------------------
        {text}
        -------------------

        Based on the recipe above AND using these ingredients: {ingredients}
        Create a healthy recipe in ENGLISH.

        You MUST use the following Markdown format exactly, including the headings:

        ## 1. Dish Name
        [Your dish name here]

        ## 2. Brief Description
        [1-2 sentences describing the dish]

        ## 3. Ingredients
        ### Main Ingredients
        - [Ingredient]: [Quantity with unit, e.g., "Potatoes: 250g"]

        ### Supplementary Ingredients
        - [Ingredient]: [Quantity with unit, e.g., "Salt: 2g"]

        ## 4. Step-by-Step Cooking Instructions
        1. [Step 1]
        2. [Step 2]

        ## 5. Estimated Prep & Cook Time
        - Prep Time: [minutes]
        - Cook Time: [minutes]

        ## 6. Tips and Variations
        - [Tip 1]
        - [Tip 2]

        ## 7. Ingredients Usage & Tips
        - ✅ Used in this recipe:
          - List the ingredients from {ingredients} that are used
        - ❌ Not used in this recipe (for variations):
          - List the ingredients from {ingredients} that are NOT used

        Do NOT add any extra text outside this structure.
        Do NOT add explanations outside the format.
        """
        }
        # {"role": "user", "content": ingredients}
    ]
    res = ollama.chat(model=self.model_select, messages=messages)
    return res.message.content