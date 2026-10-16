# ========== 文档问答页面（RAG） ==========
# Streamlit 多页面应用的 RAG 模块

import streamlit as st
import requests

# API 地址（优先从 Streamlit Secrets 读取，否则用本地地址）
import os
try:
    # Streamlit Cloud Secrets（在 Secrets 设置页配置）
    API_URL = st.secrets["API_URL"]
except:
    # 本地运行时用 localhost
    API_URL = "http://localhost:8000"

# 页面标题
st.header("技术文档 AI 问答")
st.caption("基于 RAG 技术，从技术文档中检索并生成回答")

# ===== 侧边栏：知识库状态 + 上传 =====
with st.sidebar:
    st.subheader("知识库状态")
    try:
        health = requests.get(f"{API_URL}/api/rag/health").json()
        st.metric("文档块数量", health["doc_count"])
    except:
        st.error("后端服务未启动")

    st.divider()
    st.subheader("上传文档")
    st.caption("上传 .txt / .md / .pdf 格式的技术文档")
    uploaded_file = st.file_uploader("选择文件", type=["txt", "md", "pdf"])
    if uploaded_file is not None:
        if st.button("上传到知识库", use_container_width=True):
            try:
                response = requests.post(
                    f"{API_URL}/api/rag/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"{data['filename']} 上传成功！")
                    st.info(f"切成 {data['chunk_count']} 块，知识库共 {data['total_chunks']} 块")
                    st.rerun()
                else:
                    st.error(f"上传失败：{response.text}")
            except Exception as e:
                st.error(f"无法连接后端服务：{e}")

# ===== 快捷问题 =====
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Python 类怎么定义？", use_container_width=True):
        st.session_state["rag_auto_q"] = "Python 类怎么定义？"
with col2:
    if st.button("Vue 组件怎么传值？", use_container_width=True):
        st.session_state["rag_auto_q"] = "Vue 组件怎么传值？"
with col3:
    if st.button("Python 生成器是什么？", use_container_width=True):
        st.session_state["rag_auto_q"] = "Python 生成器是什么？"

# ===== 对话历史 =====
if "rag_history" not in st.session_state:
    st.session_state.rag_history = []

for msg in st.session_state.rag_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ===== 高级选项 =====
with st.expander("高级选项"):
    n_results = st.slider("返回文档条数", min_value=1, max_value=10, value=3)
    source_filter = st.selectbox(
        "按来源过滤",
        options=["全部", "python_classes.txt", "vue_components.txt"],
        index=0,
    )
    source_filter = None if source_filter == "全部" else source_filter

# ===== 输入和发送 =====
user_input = st.chat_input("输入你的问题...")

if user_input:
    # 显示用户消息
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.rag_history.append({"role": "user", "content": user_input})

    try:
        request_data = {
            "question": user_input,
            "n_results": n_results,
            "source_filter": source_filter,
            "history": st.session_state.rag_history[:-1],
        }
        response = requests.post(f"{API_URL}/api/rag/ask", json=request_data)

        if response.status_code == 200:
            data = response.json()
            with st.chat_message("assistant"):
                st.write(data["answer"])
                with st.expander("参考文档"):
                    for i, source in enumerate(data["sources"]):
                        st.text(f"[{i+1}] {source}")
            st.session_state.rag_history.append({"role": "assistant", "content": data["answer"]})
        else:
            st.error(f"请求失败：{response.text}")
    except Exception as e:
        st.error(f"无法连接后端服务：{e}")
