# ========== 商品管理页面 ==========
# Streamlit 多页面应用的商品管理模块

import streamlit as st
import requests

# 功能开关：设为 False 隐藏此页面内容
FEATURE_ENABLED = False

if not FEATURE_ENABLED:
    st.warning("️ 商品管理功能暂未开放")
    st.stop()

# API 地址（自动检测环境）
import os
if os.getenv("STREAMLIT_RUNTIME"):
    API_URL = "https://products-app-scvx.onrender.com"
else:
    API_URL = "http://localhost:8000"

# 页面标题
st.header("商品管理")

# 三个标签页：查看、新增、修改
tab1, tab2, tab3 = st.tabs(["查看商品", "新增商品", "修改商品"])

# ===== 查看商品 =====
with tab1:
    response = requests.get(f"{API_URL}/api/product/products")
    if response.status_code == 200:
        products = response.json()["products"]
        if products:
            st.dataframe(products)
        else:
            st.info("暂无商品")
    else:
        st.error("获取商品失败")

# ===== 新增商品 =====
with tab2:
    spu_id = st.text_input("SPU编号", key="new_spu")
    name = st.text_input("商品名称", key="new_name")
    category = st.text_input("分类", key="new_cat")
    price = st.number_input("价格", value=0.0, key="new_price")
    cost = st.number_input("成本价", value=0.0, key="new_cost")

    if st.button("创建商品", key="create_btn"):
        data = {"spu_id": spu_id, "name": name, "category": category, "price": price, "cost": cost}
        response = requests.post(f"{API_URL}/api/product/products", json=data)
        if response.status_code == 200:
            st.success("创建成功！")
        else:
            st.error(response.json().get("detail", "创建失败"))

# ===== 修改商品 =====
with tab3:
    spu_id = st.text_input("要修改的SPU编码", key="edit_spu")
    name = st.text_input("新名称", key="edit_name")
    price = st.number_input("新价格", value=0.0, key="edit_price")

    if st.button("修改", key="edit_btn"):
        data = {}
        if name:
            data["name"] = name
        if price:
            data["price"] = price
        response = requests.put(f"{API_URL}/api/product/products/{spu_id}", json=data)
        if response.status_code == 200:
            st.success("修改成功！")
        else:
            try:
                error_msg = response.json().get("detail", "修改失败")
            except:
                error_msg = response.text
            st.error(error_msg)
