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

if question:
    data = {
        "model": "meituan-longcat/LongCat-2.0",#meituan-longcat/LongCat-2.0|Qwen/Qwen2.5-7B-Instruct
        "messages": [
            {"role": "system", "content": get_system_prompt(role, load_school_info())},
            {"role": "user", "content": question},
        ],
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, timeout=30)
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        st.write(answer)
    except requests.exceptions.Timeout:
        st.error("AI 响应超时，请稍后再试")
    except requests.exceptions.ConnectionError:
        st.error("网络连接失败，请检查网络")
    except Exception as e:
        st.error(f"发生错误：{e}")