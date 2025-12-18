import streamlit as st
from openai import OpenAI
import json
import docx

# ================= 配置区域 =================
# 替换为你的 DeepSeek API Key
API_KEY = "sk-3d8512f1fa07420cb8a4142dbcf2250c"
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"


# ================= 工具函数 =================

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])


def analyze_article(text):
    """调用 DeepSeek 进行结构化提取"""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    system_prompt = """
    你是一个资深的公文与文章分析专家。你的任务是将用户输入的文章进行深度结构化拆解。
    请务必返回标准的 JSON 格式数据，不要包含 Markdown 标记。
    JSON 结构必须包含以下字段：
    {
        "core_summary": "文章的核心要义（100字以内）",
        "what": "是什么：文章讨论的核心概念、背景或定义",
        "why": "为什么：做这件事的原因、背景痛点或必要性",
        "todo": "做什么：具体的目标、任务方向或重点工程",
        "how": "怎么做：具体的实施路径、手段、措施或抓手（分点概括）",
        "result": "做成怎么样：预期的成效、量化指标或未来愿景"
    }
    如果文章中缺失某一部分，该字段请填“文中未提及”。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下文章：\n{text[:10000]}"}  # 截取前1万字防止溢出
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"分析出错: {e}")
        return None


# ================= 页面布局 (UI) =================

st.set_page_config(page_title="文章结构化提取工具", layout="wide")

st.title("📑 云南农信深度阅读助手 (YNRCC-DeepReader)")
st.markdown("上传文章或粘贴文本，AI 帮你提取 **“核心要义”以及“是什么、为什么、做什么、怎么做、做成什么样”**。")

# --- 左侧栏：设置与输入 ---
with st.sidebar:
    st.header("1. 输入内容")
    input_method = st.radio("选择输入方式", ["粘贴文本", "上传 Word 文档"])

    user_text = ""

    if input_method == "粘贴文本":
        user_text = st.text_area("在此粘贴文章内容", height=300)
    else:
        uploaded_file = st.file_uploader("上传 .docx 文件", type=["docx"])
        if uploaded_file:
            user_text = read_docx(uploaded_file)
            st.success(f"已读取: {uploaded_file.name}")

    start_btn = st.button("🚀 开始深度分析", type="primary")

# --- 主界面：展示结果 ---
if start_btn:
    if not user_text:
        st.warning("请先输入文章内容！")
    else:
        with st.spinner("DeepSeek 正在思考中..."):
            result = analyze_article(user_text)

        if result:
            # 1. 核心要义区域
            st.subheader("💡 核心要义")
            st.info(result.get("core_summary"))

            st.divider()

            # 2. 结构化拆解区域 (两列布局)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🟦 是什么 (What)")
                st.write(result.get("what"))

                st.markdown("### 🟨 为什么 (Why)")
                st.write(result.get("why"))

                st.markdown("### 🟧 做什么 (Task)")
                st.write(result.get("todo"))

            with col2:
                st.markdown("### 🟩 怎么做 (How)")
                # 对“怎么做”进行稍微复杂的渲染，如果内容长的话
                st.success(result.get("how"))

                st.markdown("### 🟪 做成怎么样 (Outcome)")
                st.write(result.get("result"))

            # 3. 导出功能 (可选)
            st.divider()
            json_str = json.dumps(result, ensure_ascii=False, indent=4)
            st.download_button(
                label="📥 下载分析报告 (JSON)",
                data=json_str,
                file_name="analysis_report.json",
                mime="application/json"

            )

