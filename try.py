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

# ===== 功能1：初始化问答历史 =====
if "history" not in st.session_state:
    st.session_state["history"] = []

if "main_question_box" not in st.session_state:
    st.session_state["main_question_box"] = ""

def fill_question(q):
    st.session_state["main_question_box"] = q

st.title("小航 · 郑州航院校园信息助手")
role = st.selectbox("你是?", ["新生", "在校生", "教师"])
question = st.text_input("有啥想问的?", key="main_question_box")

# ===== 功能5：问题分类标签页 =====
st.markdown("**试试这些问题：**")
tab1, tab2, tab3 = st.tabs(["新生指南", "办事流程", "应急防骗"])

with tab1:
    new_qs = ["新生报到需要带哪些材料？", "宿舍是几人间？能选吗？", "一卡通怎么办理和充值？"]
    cols = st.columns(3)
    for i, q in enumerate(new_qs):
        with cols[i]:
            st.button(q, key=f"new_{i}", on_click=fill_question, args=(q,))

with tab2:
    flow_qs = ["怎么办理走读申请？", "补办学生证去哪里？", "奖学金评定流程是什么？"]
    cols = st.columns(3)
    for i, q in enumerate(flow_qs):
        with cols[i]:
            st.button(q, key=f"flow_{i}", on_click=fill_question, args=(q,))

with tab3:
    emer_qs = ["保卫处电话是多少？", "心理咨询中心怎么联系？", "遇到诈骗怎么办？"]
    cols = st.columns(3)
    for i, q in enumerate(emer_qs):
        with cols[i]:
            st.button(q, key=f"emer_{i}", on_click=fill_question, args=(q,))

# ===== 异常场景5：空输入 + 小任务1 序号3：长度边界 =====
if question and question.strip():
    # ===== 小任务1：长问题边界处理 =====
    if len(question) > 500:
        st.warning("⚠️ 问题有点长（超过500字），AI 可能处理不了，建议拆短一些再问")
    else:
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
                        # ===== 功能1：保存到历史 =====
                        st.session_state["history"].append({
                            "time": time.strftime("%H:%M:%S"),
                            "role": role,
                            "question": question,
                            "answer": answer,
                        })
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

# ===== 功能1+功能2：问答历史 + 清空按钮 =====
st.divider()
col1, col2 = st.columns([4, 1])
with col1:
    st.header("📝 问答历史")
with col2:
    if st.button("🗑️ 清空历史"):
        st.session_state["history"] = []
        st.rerun()

if st.session_state["history"]:
    for item in reversed(st.session_state["history"]):
        st.write(f"[{item['time']}] {item['role']} 提问：{item['question']}")
        st.write(f"回答：{item['answer']}")
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
