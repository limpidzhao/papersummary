import streamlit as st
from openai import OpenAI
import json

# ================= 配置区域 =================
# ⚠️ 请将此处替换为小米开放平台提供的实际 Key 和 Endpoint
# 如果小米使用的是兼容 OpenAI 的接口：
XIAOMI_API_KEY = "sk-spsavmnsrw0ls9z194hvy431gyekpx28wz5g9yedi8yp9cpq"
# 小米大模型的 Base URL (示例地址，请查阅小米文档获取真实地址)
# 例如可能是: https://api.xiaomi.com/v1 或类似地址
XIAOMI_BASE_URL = "https://api.xiaomi.ai/v1" 
# 模型名称 (例如: milm-pro, milm-6b 等，需查阅文档)
MODEL_NAME = "mimo-v2-flash" 

# ================= 核心逻辑 =================

def analyze_article_xiaomi(text):
    """调用小米大模型进行结构化分析"""
    # 初始化客户端 (假设小米支持 OpenAI SDK 标准协议)
    client = OpenAI(
        api_key=XIAOMI_API_KEY,
        base_url=XIAOMI_BASE_URL
    )

    # 提示词 (Prompt) 设计：强制要求 JSON 输出
    system_prompt = """
    你是一个资深的内容分析专家。请阅读用户输入的文章，并输出以下 JSON 格式的深度分析。
    
    JSON 结构要求：
    {
        "core_summary": "文章的核心要义（50字以内，一针见血）",
        "analysis": {
            "what": "是什么：文章讨论的核心定义、现象或背景",
            "why": "为什么：背后的原因、痛点、必要性或动机",
            "todo": "做什么：具体的目标、行动项、重点任务",
            "how": "怎么做：具体的执行路径、方法论、手段（分点简述）",
            "result": "做成怎么样：预期的量化成果、愿景或最终状态"
        }
    }
    注意：不要输出 Markdown 标记（如 ```json），直接输出纯 JSON 字符串。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析这篇文章：\n{text[:8000]}"} # 截断防止超长
            ],
            temperature=0.2, # 低温度保证格式稳定
            # 如果小米 API 支持 response_format="json_object"，请取消下面这行的注释
            # response_format={"type": "json_object"} 
        )
        
        # 解析返回的内容
        content = response.choices[0].message.content
        # 清理可能存在的 markdown 符号
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)

    except Exception as e:
        st.error(f"调用小米 API 失败: {e}")
        return None

# ================= 页面 UI 设计 =================

st.set_page_config(page_title="小米 MiLM 深度阅读器", layout="wide")

st.title("📱 小米 MiLM · 文章深度拆解")
st.markdown("输入文章，AI 自动拆解为 **“是什么、为什么、怎么做”** 五维结构。")

# 左侧输入栏
with st.sidebar:
    st.header("输入文章")
    user_input = st.text_area("在此粘贴文章内容...", height=400)
    run_btn = st.button("开始分析", type="primary")

# 右侧/主展示区
if run_btn and user_input:
    with st.spinner("小米 MiLM 正在思考中..."):
        result = analyze_article_xiaomi(user_input)
    
    if result:
        # 1. 核心要义 (高亮显示)
        st.subheader("💡 核心要义")
        st.success(result.get("core_summary", "解析失败"))
        
        st.divider()
        
        # 2. 五维拆解 (使用 Streamlit 的 columns 布局)
        # 第一行：是什么、为什么
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🟦 **是什么 (What)**\n\n{result['analysis'].get('what')}")
        with col2:
            st.warning(f"🟨 **为什么 (Why)**\n\n{result['analysis'].get('why')}")
            
        # 第二行：做什么、怎么做
        col3, col4 = st.columns(2)
        with col3:
            st.error(f"🟧 **做什么 (To-Do)**\n\n{result['analysis'].get('todo')}")
        with col4:
            st.success(f"🟩 **怎么做 (How)**\n\n{result['analysis'].get('how')}")
            
        # 第三行：结果
        st.markdown(f"### 🟪 **做成怎么样 (Outcome)**")
        st.markdown(f"> {result['analysis'].get('result')}")
        
        # 调试信息（可折叠）
        with st.expander("查看原始 JSON 数据"):
            st.json(result)
