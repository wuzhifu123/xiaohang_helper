import time
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

# ===== 功能1：初始化问答历史（页面显示用）=====
if "history" not in st.session_state:
    st.session_state["history"] = []

# ===== 挑战1：初始化多轮对话上下文（发给 API 用）=====
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "main_question_box" not in st.session_state:
    st.session_state["main_question_box"] = ""

# ===== 新对话视觉反馈：记录新对话开始时间戳 =====
if "new_dialog_time" not in st.session_state:
    st.session_state["new_dialog_time"] = 0

# ===== 新对话临时提示标记 =====
if "show_new_dialog_toast" not in st.session_state:
    st.session_state["show_new_dialog_toast"] = False

def fill_question(q):
    st.session_state["main_question_box"] = q

# ===== 挑战1：切换角色时清空多轮上下文，避免身份混乱 =====
def reset_dialog():
    st.session_state["messages"] = []
    st.session_state["new_dialog_time"] = time.time()

# ===== 旧历史灰色样式 =====
st.markdown("""
<style>
.archive-expander { color: #999; }
.archive-expander summary { opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

st.title("小航 · 郑州航院校园信息助手")

# ===== 优化2：角色选择放表单外，切换不会触发搜索；切换时清空多轮上下文 =====
role = st.selectbox("你是?", ["新生", "在校生", "教师"], on_change=reset_dialog)

# ===== 推荐：按角色显示4个专属问题（参考 app.py 的 RECOMMEND_QUESTIONS）=====
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

# ===== 新对话临时提示：在 rerun 后显示 toast =====
if st.session_state["show_new_dialog_toast"]:
    st.toast("✅ 新对话已开始！AI 将重新开始回答", icon="🎉")
    st.session_state["show_new_dialog_toast"] = False

# ===== 状态指示器：显示当前对话状态 =====
if st.session_state["new_dialog_time"] > 0:
    st.info("🔄 当前：新对话 · AI 已忘记之前对话")

# ===== 挑战1：新对话按钮（移到表单前面，避免修改已实例化的 session_state）=====
if st.button("🔄 新对话", help="清空多轮对话上下文，AI 将忘记之前的对话"):
    st.session_state["messages"] = []
    st.session_state["new_dialog_time"] = time.time()
    st.session_state["main_question_box"] = ""
    st.session_state["show_new_dialog_toast"] = True
    st.rerun()

# ===== 优化2：用表单包裹输入框+发送按钮，切换角色不会自动重搜 =====
with st.form("ask_form", clear_on_submit=False):
    question = st.text_input("有啥想问的?", key="main_question_box")
    submitted = st.form_submit_button("发送提问", type="primary")

    if submitted:
        # ===== 异常场景5：空输入校验 =====
        if not question or not question.strip():
            st.info("请输入有效的问题")
        # ===== 小任务1：长问题边界处理 =====
        elif len(question) > 500:
            st.warning("⚠️ 问题有点长（超过500字），AI 可能处理不了，建议拆短一些再问")
        else:
            # ===== 异常场景4：数据文件缺失检查 =====
            md_files = list(Path("data").glob("*.md"))
            if not md_files:
                st.warning("⚠️ 数据文件缺失，请联系老师补齐 data/ 目录下的 md 文件")
            else:
                # ===== 挑战1：构造多轮对话 messages（system + 历史上下文 + 当前问题）=====
                system_prompt = get_system_prompt(role, load_school_info())
                messages = [{"role": "system", "content": system_prompt}] + st.session_state["messages"]
                messages.append({"role": "user", "content": question})

                data = {
                    "model": "meituan-longcat/LongCat-2.0",
                    "messages": messages,
                }
                try:
                    # ===== 功能3：加载状态提示 =====
                    # ===== 功能6：耗时统计起点 =====
                    start = time.time()
                    with st.spinner("小航正在思考..."):
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
                            end = time.time()
                            # ===== 交互优化：Markdown 格式化 =====
                            st.markdown(answer)
                            # ===== 功能6：回答元信息 =====
                            st.caption(f"回答字数：{len(answer)} 字 · 耗时：{end - start:.1f} 秒")
                            # ===== 功能1：保存到页面历史 =====
                            current_time = time.time()
                            st.session_state["history"].append({
                                "time": time.strftime("%H:%M:%S"),
                                "timestamp": current_time,
                                "role": role,
                                "question": question,
                                "answer": answer,
                            })
                            # ===== 挑战1：保存到多轮上下文（下次提问会带上）=====
                            st.session_state["messages"].append({"role": "user", "content": question})
                            st.session_state["messages"].append({"role": "assistant", "content": answer})
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

# ===== 功能1+2 + 挑战2：问答历史区 + 导出按钮 + 清空按钮 =====
st.divider()
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.header("📝 问答历史")
with col2:
    # ===== 挑战2：导出对话记录为 txt 文件 =====
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

# ===== 优化1：历史记录改为可折叠展开（expander），标题显示问题，点击展开看回答 =====
# ===== 新对话视觉反馈：旧历史变暗 =====
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
