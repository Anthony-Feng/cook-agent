from ddgs import DDGS
import ollama
from config import MODEL_SELECT

# ================== 工具3：搜索工具函数 ==================
def search_web(query):
    """
    使用 DuckDuckGo 搜索网络信息 + LLM 整理：只提取食物名称与对应价格
    """
    # print(f"🔍 search online: {query} ...")
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=10)]
            raw_result = "\n".join(results)
            # print(raw_result)
        # 精准 Prompt：提取食物在本地的生产/农业状况
        # 精准 Prompt：严格锁定单一查询目标，杜绝无关作物
        prompt = f"""
        You are a strict agricultural data auditor. Do NOT act as a chatbot.

        TASK:
        Extract data ONLY for the specific food item requested in the query: "{query}".

        STRICT RULES (NO EXCEPTIONS):
        1. **STRICT FILTERING**: You are FORBIDDEN from listing any food items that are not "{query}". If the search results mention other crops (e.g., wheat, barley, corn), IGNORE them entirely unless they match the query.
        2. **UNIQUE ENTRY**: Output a maximum of ONE row for "{query}". If multiple data points exist, merge them into that single row.
        3. **NO DATA, NO TABLE**: If the search results contain no specific production information for "{query}", respond with: "No local production data found for {query}." Do not generate a table for unrelated items.
        4. **NO NOTES**: Do not include any introductory text, notes, or explanations after the table.
        5. Columns: | Food Name | Production Status | Main Farming Areas | Seasonality |

        REQUIRED OUTPUT FORMAT:
        | Food Name | Production Status | Main Farming Areas | Seasonality |
        | :--- | :--- | :--- | :--- |
        | {query} | [Data] | [Data] | [Data] |

        Search result content:
        {raw_result}
        """

        res = ollama.chat(
            model=MODEL_SELECT,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.message.content.strip()

    except Exception as e:
        return f"Search error: {str(e)}"