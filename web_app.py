# ========== laji管理AI系统 - 主页 ==========

import streamlit as st

# 页面配置
st.set_page_config(page_title="laji管理AI系统", page_icon="", layout="wide")

# 主页标题
st.title(" laji管理AI系统")
st.caption("AI 驱动的管理平台 | 智能问答 · 股票分析")

st.divider()

# 功能介绍
st.subheader("系统功能")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ###  AI 文档问答
    - 上传技术文档（txt/md/pdf）
    - 自然语言提问
    - 基于文档内容智能回答
    - 支持多轮对话
    """)

with col2:
    st.markdown("""
    ###  股票智能问答
    - 实时A股行情查询
    - 历史K线数据分析
    - 大盘指数监控
    - 自然语言智能问答
    """)

st.divider()
st.info("👈 请从左侧导航栏选择功能模块")
