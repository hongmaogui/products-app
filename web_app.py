import streamlit as st

import requests 

import pandas as pd


st.set_page_config(page_title="laji商品管理系统",layout="wide")
st.title("laji商品管理系统")

API_URL = "http://localhost:8000"

page = st.sidebar.radio("选择功能",["商品管理","库存管理","销售分析","AI助手"])

if page == "商品管理":
    st.header("商品管理")
    tab1,tab2,tab3 = st.tabs(["查看商品","新增商品","修改商品"])

    with tab1:
        response = requests.get(f"{API_URL}/products")
        if response.status_code == 200:
            products = response.json()["products"]
            if products:
                st.dataframe(products)
            else:
                st.info("暂无商品")
        else:
            st.error("获取商品失败")

    with tab2:
        spu_id = st.text_input("SPU编号")
        name = st.text_input("商品名称")
        category = st.text_input("分类")
        price = st.number_input("价格",value=0.0)
        cost = st.number_input("成本价",value=0.0)
        if st.button("创建商品"):
            data = {"spu_id":spu_id,"name":name,"category":category,"price":price,"cost":cost}
            response = requests.post(f"{API_URL}/products",json=data)
            if response.status_code == 200:
                st.success("创建成功！")
            else:
                st.error(response.json().get("detail","创建失败"))

    with tab3:
        spu_id = st.text_input("要修改的SPU编码",key="edit_spu")
        name = st.text_input("新名词",key="edit_name")
        price = st.number_input("新价格",value=0.0,key="edit_price")
        if st.button("修改",key="edit_btn"):
            data = {}
            if name:
                data["name"] = name
            if price:
                data["price"] = price
            response = requests.put(f"{API_URL}/products/{spu_id}",json=data)
            if response.status_code == 200:
                st.success("修改成功！")
            else:
                try:
                    error_msg = response.json().get("detail","修改失败")
                except:
                    error_msg = response.text
                st.error(error_msg)

elif page == "库存管理":
    st.header("库存管理")
    spu_id = st.text_input("商品编号")
    stock = st.number_input("库存数量",value=0)
    warehouse = st.text_input("仓库名称",value="主仓库")
    if st.button("更新库存"):
        response = requests.post(f"{API_URL}/inventory",params={"spu_id":spu_id,"stock":stock,"warehouse":warehouse})
        if response.status_code == 200:
            st.success(response.json()["message"])
        else:
            st.error(response.json().get("detail","更新失败"))

    if st.button("查询库存"):
        response = requests.get(f"{API_URL}/inventory/{spu_id}")
        if response.status_code == 200:
            st.json(response.json())
        else:
            st.error(response.json().get("detail","查询失败"))

elif page == "销售分析":
    st.header("销售分析")

    response = requests.get(f"{API_URL}/stats/summary")
    if response.status_code == 200:
        stats = response.json()
        col1,col2,col3 = st.columns(3)
        col1.metric("商品总数",stats["product_count"])
        col2.metric("总库存",f"{stats['total_stock']}件")
        col3.metric("总销售额",f"{stats['total_sales']}元")

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

            
            df = pd.DataFrame(list(sales_by_product.items()),columns = ["商品编号","销售额"])
            st.bar_chart(df.set_index("商品编号"))
        else:
            st.info("暂无销售数据")

        st.subheader("导出数据")
        if sales_list:
            if st.button("导出为Excel"):
                df = pd.DataFrame(sales_list)
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output,engine="openpyxl") as writer:
                    df.to_excel(writer,index=False,sheet_name="销售记录")
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

    st.subheader("记录销售")
    spu_id = st.text_input("商品编号",key="sales_spu")
    quantity = st.number_input("销售数量",value=1,key="sales_qty")
    amout = st.number_input("销售金额",value=0.0,key="sales_anount")
    if st.button("记录销售",key="sales_btn"):
        response = requests.post(f"{API_URL}/sales",params={"spu_id":spu_id,"quantity":quantity,"amout":amout})
        if response.status_code == 200:
            result = response.json()
            st.success(f"销售成功！剩余库存：{result['remaining_stock']} 件")
        else:
            st.error(response.json().get("detail","记录失败"))

elif page == "AI助手":
    st.header("AI智能助手")
    st.caption("用自然语言查询商品、库存、销售数据")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("输入你的问题...")
    if user_input:
        st.session_state.messages.append({"role":"user","content":"user_input"})
        with st.chat_message("user"):
            st.write(user_input)

        from ai_agent import chat
        with st.chat_message("assistant"):
            with st.spinner("AI思考中..."):
                reply = chat("web_user",user_input)
                st.write(reply)
        st.session_state.messages.append({"role":"assistant","content":reply})
