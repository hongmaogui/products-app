# ========== laji管理AI系统 - 主入口 ==========
# 只负责：创建 FastAPI 应用、配置中间件、注册路由模块

# FastAPI 核心
from fastapi import FastAPI
# CORS 跨域中间件
from fastapi.middleware.cors import CORSMiddleware

# 导入路由模块
# from api.product_api import router as product_router  # 管理功能已隐藏
from api.rag_api import router as rag_router
from api.stock_api import router as stock_router

# ========== 创建应用 ==========

app = FastAPI(title="laji管理AI系统")

# 配置 CORS，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 注册路由 ==========

# 管理路由（商品/库存/销售/统计）- 已隐藏
# app.include_router(product_router)

# RAG 文档问答路由（问答/上传/健康检查）
app.include_router(rag_router)

# 股票智能问答路由（问答/健康检查）
app.include_router(stock_router)

# ========== 根路径 ==========

@app.get("/")
def root():
    """根路径，确认 API 正常运行"""
    return {"message": "laji管理AI系统 API 运行中"}

# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
