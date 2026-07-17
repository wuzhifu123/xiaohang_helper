import time
import sys
import os
import streamlit as st
from pathlib import Path

if getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.join(sys._MEIPASS, 'src'))
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import load_school_info, get_system_prompt
from config import API_KEY
from api import call_api

if "history" not in st.session_state:
    st.session_state["history"] = []

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "main_question_box" not in st.session_state:
    st.session_state["main_question_box"] = ""

if "new_dialog_time" not in st.session_state:
    st.session_state["new_dialog_time"] = 0

if "show_new_dialog_toast" not in st.session_state:
    st.session_state["show_new_dialog_toast"] = False

def fill_question(q):
    st.session_state["main_question_box"] = q

def reset_dialog():
    st.session_state["messages"] = []
    st.session_state["new_dialog_time"] = time.time()

st.markdown("""
<style>
.archive-expander { color: #999; }
.archive-expander summary { opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

st.title("小航 · 郑州航院校园信息助手")

role = st.selectbox("你是?", ["新生", "在校生", "教师"], on_change=reset_dialog)

RECOMMEND_QUESTIONS = {
    "新生": [
        "报到注册流程是怎样的？",
        "宿舍是怎么分配的？",
        "校园一卡通在哪里办理？",
        "新生军训安排是什么？"
    ],
    "在校生": [
        "如何办理请假手续？",
        "图书馆借书流程是怎样的？",
        "成绩查询在哪里可以查到？",
        "如何申请助学金？"
    ],
    "教师": [
        "如何申请科研经费？",
        "教职工宿舍申请流程？",
        "如何在教务系统录入成绩？",
        "会议室怎么预约？"
    ]
}

st.markdown(f"**{role}可能想问：**")
rec_qs = RECOMMEND_QUESTIONS[role]
cols = st.columns(2)
for i, q in enumerate(rec_qs):
    with cols[i % 2]:
        st.button(q, key=f"rec_{i}", on_click=fill_question, args=(q,))

if st.session_state["show_new_dialog_toast"]:
    st.toast("✅ 新对话已开始！AI 将重新开始回答", icon="🎉")
    st.session_state["show_new_dialog_toast"] = False

if st.session_state["new_dialog_time"] > 0:
    st.info("🔄 当前：新对话 · AI 已忘记之前对话")

if st.button("🔄 新对话", help="清空多轮对话上下文，AI 将忘记之前的对话"):
    st.session_state["messages"] = []
    st.session_state["new_dialog_time"] = time.time()
    st.session_state["main_question_box"] = ""
    st.session_state["show_new_dialog_toast"] = True
    st.rerun()

with st.form("ask_form", clear_on_submit=False):
    question = st.text_input("有啥想问的?", key="main_question_box")
    submitted = st.form_submit_button("发送提问", type="primary")

    if submitted:
        if not question or not question.strip():
            st.info("请输入有效的问题")
        elif len(question) > 500:
            st.warning("⚠️ 问题有点长（超过500字），AI 可能处理不了，建议拆短一些再问")
        elif not API_KEY:
            st.error("🔑 API Key 未配置，请在 .env 文件中设置 API_KEY")
        else:
            md_files = list(Path("data").glob("*.md"))
            if not md_files:
                st.warning("⚠️ 数据文件缺失，请联系老师补齐 data/ 目录下的 md 文件")
            else:
                system_prompt = get_system_prompt(role, load_school_info())
                current_messages = st.session_state["messages"].copy()
                current_messages.append({"role": "user", "content": question})

                start = time.time()
                with st.spinner("小航正在思考..."):
                    answer, error = call_api(system_prompt, current_messages)

                if error:
                    st.error(f"⚠️ {error}")
                else:
                    end = time.time()
                    st.markdown(answer)
                    st.caption(f"回答字数：{len(answer)} 字 · 耗时：{end - start:.1f} 秒")

                    current_time = time.time()
                    st.session_state["history"].append({
                        "time": time.strftime("%H:%M:%S"),
                        "timestamp": current_time,
                        "role": role,
                        "question": question,
                        "answer": answer,
                    })

                    st.session_state["messages"].append({"role": "user", "content": question})
                    st.session_state["messages"].append({"role": "assistant", "content": answer})

st.divider()
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.header("📝 问答历史")
with col2:
    if st.session_state["history"]:
        text = ""
        for item in st.session_state["history"]:
            text += f"[{item['time']}] {item['role']} 提问：{item['question']}\n"
            text += f"回答：{item['answer']}\n"
            text += "---\n"
        st.download_button(
            label="📥 导出",
            data=text,
            file_name=f"小航对话记录_{time.strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )
with col3:
    if st.button("🗑️ 清空"):
        st.session_state["history"] = []
        st.rerun()

if st.session_state["history"]:
    old_history = []
    new_history = []
    for item in reversed(st.session_state["history"]):
        if st.session_state["new_dialog_time"] > 0 and item.get("timestamp", 0) < st.session_state["new_dialog_time"]:
            old_history.append(item)
        else:
            new_history.append(item)

    if old_history:
        st.markdown("📋 **之前的对话（已归档）**", help="这些对话的上下文已被 AI 遗忘")
        for item in old_history:
            st.markdown(f"**<span style='color:#999'>[{item['time']}] {item['role']} · {item['question']}</span>**", unsafe_allow_html=True)
            with st.expander("查看回答"):
                st.markdown(item["answer"])
            st.caption("---")
        st.divider()

    for item in new_history:
        with st.expander(f"[{item['time']}] {item['role']} · {item['question']}"):
            st.markdown(item["answer"])
            st.caption("---")
else:
    st.caption("暂无历史记录，问一个问题试试吧～")

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