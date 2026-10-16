# ========== laji管理AI系统 - 主入口 ==========
# 使用 st.navigation 控制页面显示（隐藏商品管理）

import streamlit as st

# 页面配置
st.set_page_config(page_title="laji管理AI系统", page_icon="", layout="wide")

# 自定义导航：只显示指定的页面
pages = {
    "": [
        st.Page("web_app.py", title="首页", default=True),
    ],
    "功能模块": [
        st.Page("pages/1_rag.py", title="AI文档问答"),
        st.Page("pages/2_stock.py", title="股票智能问答"),
    ],
}

# 创建导航并运行
pg = st.navigation(pages)
pg.run()
