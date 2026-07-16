import requests
import streamlit as st
from pathlib import Path
from prompts import load_school_info, get_system_prompt

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-pdggycmtyfivgqopxqypzvygttuiyeiofxqcxmzhrusuxkyd"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

if "main_question_box" not in st.session_state:
    st.session_state["main_question_box"] = ""

def fill_question(q):
    st.session_state["main_question_box"] = q

st.title("小航 · 郑州航院校园信息助手")
role = st.selectbox("你是?", ["新生", "在校生", "教师"])
question = st.text_input(
    "有啥想问的?",
    key="main_question_box"
)

PRESET_QUESTIONS = {
    "新生": [
        "新生报到需要带哪些材料？",
        "宿舍是几人间？能选吗？",
        "一卡通怎么办理和充值？",
    ],
    "在校生": [
        "怎么办理走读申请？",
        "补办学生证去哪里？",
        "奖学金评定流程是什么？",
    ],
    "教师": [
        "教师入职办事流程？",
        "科研经费报销窗口在哪？",
        "教职工体检怎么预约？",
    ],
    "通用": [
        "保卫处电话是多少？",
        "心理咨询中心怎么联系？",
        "校园网怎么连？",
    ],
}

st.markdown("**试试这些问题：**")
cols = st.columns(3)
flat = []
for group in PRESET_QUESTIONS.values():
    flat.extend(group)
for i, q in enumerate(flat):
    with cols[i % 3]:
        st.button(q, key=f"q_{i}", on_click=fill_question, args=(q,))  # 用on_click

# ===== 异常场景5：用户输入空问题（只输入空格不算有效问题）=====
if question and question.strip():
    # ===== 异常场景4：数据文件缺失检查 =====
    md_files = list(Path("data").glob("*.md"))
    if not md_files:
        st.warning("⚠️ 数据文件缺失，请联系老师补齐 data/ 目录下的 md 文件")
    else:
        data = {
            # 模型名用课件要求的 Qwen
            "model": "meituan-longcat/LongCat-2.0",
            "messages": [
                {"role": "system", "content": get_system_prompt(role, load_school_info())},
                {"role": "user", "content": question},
            ],
        }
        try:
            response = requests.post(API_URL, headers=HEADERS, json=data, timeout=30)

            # ===== 异常场景3：API Key 失效或错误 =====
            if response.status_code == 401:
                st.error("🔑 API Key 失效，请重新配置")
            elif response.status_code != 200:
                st.error(f"⚠️ API 异常，状态码：{response.status_code}")
            else:
                result = response.json()
                # ===== 异常场景6：API 返回格式异常 =====
                try:
                    answer = result["choices"][0]["message"]["content"]
                    st.write(answer)
                except (KeyError, IndexError):
                    st.error("⚠️ AI 返回格式异常，请重试")

        # ===== 异常场景1：API 调用超时 =====
        except requests.exceptions.Timeout:
            st.error("⏰ AI 响应超时，请稍后再试")
        # ===== 异常场景2：网络连接失败 =====
        except requests.exceptions.ConnectionError:
            st.error("📡 网络连接失败，请检查网络")
        except Exception as e:
            st.error(f"发生错误：{e}")
elif question is not None and question != "":
    # 用户输入了纯空格
    st.info("请输入有效的问题")

st.divider()
st.header("📞 电话黄页（静态兜底）")
st.caption("AI 答不上来时，可以直接查这里。本页不依赖网络，永远可用。")
try:
    yellow_page_content = Path("data/03_电话黄页.md").read_text(encoding="utf-8")
    st.markdown(yellow_page_content)
except FileNotFoundError:
    st.error("电话黄页文件缺失：data/03_电话黄页.md")
except UnicodeDecodeError:
    yellow_page_content = Path("data/03_电话黄页.md").read_text(encoding="gbk")
    st.markdown(yellow_page_content)