# ========== 股票智能问答页面 ==========
# Streamlit 多页面应用的股票问答模块

import streamlit as st
import requests

# API 地址（自动检测环境）
import os
if os.getenv("STREAMLIT_RUNTIME"):
    API_URL = "https://products-app-scvx.onrender.com"
else:
    API_URL = "http://localhost:8000"

# 页面标题
st.header("股票智能问答")
st.caption("基于 AKShare 免费数据源，用自然语言查询A股行情、历史走势、大盘指数")

# ===== 侧边栏：服务状态 =====
with st.sidebar:
    st.subheader("服务状态")
    try:
        # 调用健康检查接口，确认后端服务正常
        health = requests.get(f"{API_URL}/api/stock/health").json()
        st.success(health["message"])
    except:
        st.error("后端服务未启动")

    st.divider()
    st.subheader("功能说明")
    st.markdown("""
    - 查实时行情：平安银行现在多少钱？
    - 查历史K线：茅台最近30天走势
    - 查基本信息：宁德时代市值多少？
    - 查大盘指数：今天大盘怎么样？
    - 模糊搜索：帮我找平安的股票代码
    - 板块行情：今天哪个板块涨得好？
    - 资金流向：茅台主力资金流向
    - 涨跌排行：今天涨停的股票有哪些
    - **技术指标**：茅台MACD金叉了吗？KDJ超买了吗？
    """)

# ===== 快捷问题按钮 =====
st.subheader("快捷提问")

# 第一行：基础功能
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("今天大盘怎么样？", use_container_width=True):
        st.session_state["stock_auto_q"] = "今天大盘怎么样？"

with col2:
    if st.button("贵州茅台现在多少钱？", use_container_width=True):
        st.session_state["stock_auto_q"] = "贵州茅台现在多少钱？"

with col3:
    if st.button("宁德时代市值多少？", use_container_width=True):
        st.session_state["stock_auto_q"] = "宁德时代市值多少？"

with col4:
    if st.button("帮我找平安银行的代码", use_container_width=True):
        st.session_state["stock_auto_q"] = "帮我找平安银行的股票代码"

st.markdown("")  # 间距

# 第二行：新增功能
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("今天哪个板块涨得好？", use_container_width=True):
        st.session_state["stock_auto_q"] = "今天哪个行业板块涨得最好？"

with col2:
    if st.button("热门概念板块有哪些？", use_container_width=True):
        st.session_state["stock_auto_q"] = "今天热门概念板块有哪些？"

with col3:
    if st.button("茅台主力资金流向", use_container_width=True):
        st.session_state["stock_auto_q"] = "贵州茅台的主力资金流向如何？"

with col4:
    if st.button("今天涨停的股票", use_container_width=True):
        st.session_state["stock_auto_q"] = "今天涨幅最大的股票有哪些？"

st.markdown("")  # 间距

# 第三行：技术指标分析
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("茅台技术指标分析", use_container_width=True):
        st.session_state["stock_auto_q"] = "贵州茅台的技术指标怎么样？MA、MACD、KDJ、RSI分析一下"

with col2:
    if st.button("平安银行MACD金叉了吗", use_container_width=True):
        st.session_state["stock_auto_q"] = "平安银行的MACD出现金叉了吗？"

with col3:
    if st.button("宁德时代KDJ超买了吗", use_container_width=True):
        st.session_state["stock_auto_q"] = "宁德时代的KDJ指标是不是超买了？"

with col4:
    if st.button("比亚迪均线多头排列吗", use_container_width=True):
        st.session_state["stock_auto_q"] = "比亚迪的均线系统是多头排列吗？MA5、MA10、MA20、MA60分析一下"

# ===== 对话历史 =====
# 用 session_state 存储对话历史，实现多轮对话
if "stock_history" not in st.session_state:
    st.session_state.stock_history = []

# 显示历史对话
for msg in st.session_state.stock_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ===== 输入框和发送 =====
user_input = st.chat_input("输入你的股票问题...")

# 如果点击了快捷问题按钮，自动填充输入
if "stock_auto_q" in st.session_state and not user_input:
    user_input = st.session_state.pop("stock_auto_q")

if user_input:
    # 显示用户消息
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.stock_history.append({"role": "user", "content": user_input})

    # 显示加载状态
    with st.chat_message("assistant"):
        with st.spinner("Agent 正在查询数据..."):
            try:
                # 构造请求数据
                request_data = {
                    "question": user_input,           # 用户问题
                    "session_id": "web_default",      # 会话ID
                    "history": st.session_state.stock_history[:-1],  # 之前的对话历史
                }

                # 调用后端股票问答接口
                response = requests.post(
                    f"{API_URL}/api/stock/ask",
                    json=request_data,
                    timeout=120,  # Agent调用+AKShare拉数据可能需要较长时间
                )

                if response.status_code == 200:
                    data = response.json()
                    # 显示Agent回答
                    st.write(data["answer"])

                    # 如果有工具调用记录，显示在折叠区域
                    if data.get("sources"):
                        with st.expander("查看工具调用过程"):
                            for source in data["sources"]:
                                st.text(source)

                    # 保存Agent回答到历史
                    st.session_state.stock_history.append({
                        "role": "assistant",
                        "content": data["answer"]
                    })
                else:
                    st.error(f"请求失败：{response.text}")

            except Exception as e:
                st.error(f"无法连接后端服务：{e}")

# ===== 清空对话按钮 =====
if st.session_state.stock_history:
    if st.button("清空对话历史"):
        st.session_state.stock_history = []
        st.rerun()
