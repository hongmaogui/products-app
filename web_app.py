# 导入 Streamlit，用来快速构建网页界面
import streamlit as st
# 导入 requests，用来向 FastAPI 后端发送 HTTP 请求
import requests
# 导入 pandas，用来处理表格数据
import pandas as pd

# ========== 页面基础配置 ==========

# 设置网页标题和布局
st.set_page_config(page_title="星辰商品管理AI系统", layout="wide")
# 显示页面主标题
st.title("星辰商品管理AI系统")

# API 后端地址（部署后改成 Render 的地址）
API_URL = "http://localhost:8000"

# ========== 侧边栏导航 ==========

# 用 radio 组件做侧边栏导航，5 个功能页面
page = st.sidebar.radio(
    "选择功能",
    ["商品管理", "库存管理", "销售分析", "AI助手", "文档问答"],
)

# ==============================
# 页面 1：商品管理
# ==============================

if page == "商品管理":
    st.header("商品管理")
    # 用 tabs 分成三个标签页
    tab1, tab2, tab3 = st.tabs(["查看商品", "新增商品", "修改商品"])

    with tab1:
        # 请求后端获取所有商品
        response = requests.get(f"{API_URL}/products")
        if response.status_code == 200:
            products = response.json()["products"]
            if products:
                st.dataframe(products)  # 用表格展示
            else:
                st.info("暂无商品")
        else:
            st.error("获取商品失败")

    with tab2:
        # 新增商品的表单
        spu_id = st.text_input("SPU编号")
        name = st.text_input("商品名称")
        category = st.text_input("分类")
        price = st.number_input("价格", value=0.0)
        cost = st.number_input("成本价", value=0.0)
        if st.button("创建商品"):
            data = {"spu_id": spu_id, "name": name, "category": category, "price": price, "cost": cost}
            response = requests.post(f"{API_URL}/products", json=data)
            if response.status_code == 200:
                st.success("创建成功！")
            else:
                st.error(response.json().get("detail", "创建失败"))

    with tab3:
        # 修改商品的表单
        spu_id = st.text_input("要修改的SPU编码", key="edit_spu")
        name = st.text_input("新名称", key="edit_name")
        price = st.number_input("新价格", value=0.0, key="edit_price")
        if st.button("修改", key="edit_btn"):
            data = {}
            if name:
                data["name"] = name
            if price:
                data["price"] = price
            response = requests.put(f"{API_URL}/products/{spu_id}", json=data)
            if response.status_code == 200:
                st.success("修改成功！")
            else:
                try:
                    error_msg = response.json().get("detail", "修改失败")
                except:
                    error_msg = response.text
                st.error(error_msg)

# ==============================
# 页面 2：库存管理
# ==============================

elif page == "库存管理":
    st.header("库存管理")
    spu_id = st.text_input("商品编号")
    stock = st.number_input("库存数量", value=0)
    warehouse = st.text_input("仓库名称", value="主仓库")
    if st.button("更新库存"):
        response = requests.post(
            f"{API_URL}/inventory",
            params={"spu_id": spu_id, "stock": stock, "warehouse": warehouse},
        )
        if response.status_code == 200:
            st.success(response.json()["message"])
        else:
            st.error(response.json().get("detail", "更新失败"))

    if st.button("查询库存"):
        response = requests.get(f"{API_URL}/inventory/{spu_id}")
        if response.status_code == 200:
            st.json(response.json())
        else:
            st.error(response.json().get("detail", "查询失败"))

# ==============================
# 页面 3：销售分析
# ==============================

elif page == "销售分析":
    st.header("销售分析")

    # 显示经营概览统计
    response = requests.get(f"{API_URL}/stats/summary")
    if response.status_code == 200:
        stats = response.json()
        col1, col2, col3 = st.columns(3)
        col1.metric("商品总数", stats["product_count"])
        col2.metric("总库存", f"{stats['total_stock']}件")
        col3.metric("总销售额", f"{stats['total_sales']}元")

    # 销售对比柱状图
    st.subheader("各商品销售对比")
    response = requests.get(f"{API_URL}/sales")
    if response.status_code == 200:
        sales_list = response.json()["sales"]
        if sales_list:
            sales_by_product = {}
            for s in sales_list:
                spu = s["spu_id"]
                if spu not in sales_by_product:
                    sales_by_product[spu] = 0
                sales_by_product[spu] += s["amount"]

            df = pd.DataFrame(list(sales_by_product.items()), columns=["商品编号", "销售额"])
            st.bar_chart(df.set_index("商品编号"))
        else:
            st.info("暂无销售数据")

        # 导出 Excel
        st.subheader("导出数据")
        if sales_list:
            if st.button("导出为Excel"):
                df = pd.DataFrame(sales_list)
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="销售记录")
                output.seek(0)
                st.download_button(
                    label="下载excel文件",
                    data=output,
                    file_name="销售记录.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                st.success("文件已准备好，点击按钮下载")
            else:
                st.info("暂无数据可导出")

    # 记录销售
    st.subheader("记录销售")
    spu_id = st.text_input("商品编号", key="sales_spu")
    quantity = st.number_input("销售数量", value=1, key="sales_qty")
    amount = st.number_input("销售金额", value=0.0, key="sales_amount")
    if st.button("记录销售", key="sales_btn"):
        response = requests.post(
            f"{API_URL}/sales",
            params={"spu_id": spu_id, "quantity": quantity, "amount": amount},
        )
        if response.status_code == 200:
            result = response.json()
            st.success(f"销售成功！剩余库存：{result['remaining_stock']} 件")
        else:
            st.error(response.json().get("detail", "记录失败"))

# ==============================
# 页面 4：AI 助手（商品管理 AI Agent）
# ==============================

elif page == "AI助手":
    st.header("AI智能助手")
    st.caption("用自然语言查询商品、库存、销售数据")

    # 初始化对话历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 用户输入
    user_input = st.chat_input("输入你的问题...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # 调用 AI Agent
        from ai_agent import chat
        with st.chat_message("assistant"):
            with st.spinner("AI思考中..."):
                reply = chat("web_user", user_input)
                st.write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ==============================
# 页面 5：文档问答（RAG）
# ==============================

elif page == "文档问答":
    st.header("技术文档 AI 问答")
    st.caption("基于 RAG 技术，从技术文档中检索并生成回答")

    # 侧边栏显示知识库状态和上传功能
    with st.sidebar:
        st.subheader("知识库状态")
        try:
            health = requests.get(f"{API_URL}/health").json()
            st.metric("文档块数量", health["doc_count"])
        except:
            st.error("后端服务未启动")

        st.divider()
        st.subheader("上传文档")
        st.caption("上传 .txt 格式的技术文档")
        uploaded_file = st.file_uploader("选择文件", type=["txt"])
        if uploaded_file is not None:
            if st.button("上传到知识库", use_container_width=True):
                try:
                    response = requests.post(
                        f"{API_URL}/upload",
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

    # 快捷问题按钮
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

    # 问题输入框
    if "rag_auto_q" in st.session_state:
        default_q = st.session_state["rag_auto_q"]
        del st.session_state["rag_auto_q"]
    else:
        default_q = ""

    user_input = st.text_input(
        "输入你的问题：",
        value=default_q,
        placeholder="例如：Python 的继承怎么用？",
        key="rag_question",
    )

    # 发送并显示回答
    if st.button("发送", type="primary"):
        if user_input:
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": user_input},
                )
                if response.status_code == 200:
                    data = response.json()
                    st.subheader(f"❓ {data['question']}")
                    st.subheader("回答")
                    st.write(data["answer"])
                    st.subheader("参考文档")
                    for i, source in enumerate(data["sources"]):
                        with st.expander(f"参考文档 {i+1}"):
                            st.text(source)
                else:
                    st.error(f"请求失败：{response.text}")
            except Exception as e:
                st.error(f"无法连接后端服务：{e}")
        else:
            st.warning("请先输入问题")
