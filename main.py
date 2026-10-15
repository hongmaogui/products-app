# ========== 导入区 ==========

# FastAPI 核心组件
# FastAPI: 创建 API 应用
# HTTPException: 抛出 HTTP 错误（如 404、400）
# UploadFile, File: 处理文件上传
from fastapi import FastAPI, HTTPException, UploadFile, File
# CORS 中间件：允许前端跨域访问后端
from fastapi.middleware.cors import CORSMiddleware
# BaseModel: 定义请求/响应的数据结构
from pydantic import BaseModel
# Optional: 表示参数可以为空
from typing import Optional
# SQLAlchemy 数据库相关
# sessionmaker: 创建数据库会话
from sqlalchemy.orm import sessionmaker
# func: 调用数据库聚合函数（SUM、COUNT 等）
from sqlalchemy import func
# 导入数据模型：Product（商品）、Inventory（库存）、SalesRecord（销售记录）
from models import engine, Product, Inventory, SalesRecord
# ChromaDB 向量数据库，用于 RAG 文档检索
import chromadb
# 文本分割器，把长文档切成小块
from langchain_text_splitters import RecursiveCharacterTextSplitter
# LangChain 大模型和消息类型
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
# os 模块：处理文件路径
import os

# ========== 数据库会话 ==========

# 创建数据库会话工厂，每次请求都通过它创建独立的数据库连接
SessionLocal = sessionmaker(bind=engine)

# ========== 创建 FastAPI 应用 ==========

# 创建应用实例，设置标题
app = FastAPI(title="星辰商品管理AI系统")

# 配置 CORS 跨域，允许前端（Streamlit）访问后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 允许任何来源（开发环境）
    allow_credentials=True,     # 允许携带凭证
    allow_methods=["*"],        # 允许所有 HTTP 方法
    allow_headers=["*"],        # 允许所有请求头
)

# ========== 初始化 ChromaDB 向量数据库 ==========

# 获取项目根目录路径（main.py 所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ChromaDB 数据存放路径
CHROMA_PATH = os.path.join(BASE_DIR, "rag_docs")
# 创建持久化客户端，数据保存到磁盘
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
# 获取或创建文档集合
rag_collection = chroma_client.get_or_create_collection(name="tech_docs")

# ========== 初始化大模型 ==========

# 创建智谱 AI 聊天模型实例
llm = ChatOpenAI(
    base_url="https://open.bigmodel.cn/api/paas/v4",  # 智谱 AI 的 OpenAI 兼容接口
    model="glm-4-flash",                                # 使用 glm-4-flash 模型
    api_key="0f5150f6824b46798493bad132e9e981.KlIXMBcsTBD3mm8z",  # API 密钥
)

# ========== 数据模型定义（Pydantic） ==========

# 创建商品时的请求格式
class ProductCreate(BaseModel):
    spu_id: str                     # 商品 SPU 编号，必填
    name: str                       # 商品名称，必填
    category: Optional[str] = None  # 商品分类，可选
    price: float                    # 售价，必填
    cost: Optional[float] = None    # 成本价，可选

# 修改商品时的请求格式（所有字段可选）
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None

# RAG 问答的请求格式
class QuestionRequest(BaseModel):
    question: str  # 用户的问题

# RAG 问答的响应格式
class AnswerResponse(BaseModel):
    question: str       # 用户的问题
    answer: str         # 大模型生成的回答
    sources: list[str]  # 参考的文档片段

# 文档上传的响应格式
class UploadResponse(BaseModel):
    filename: str       # 上传的文件名
    chunk_count: int    # 切成了多少块
    total_chunks: int   # 知识库总块数

# ==============================
# 第一部分：商品管理接口
# ==============================

@app.get("/")
def root():
    """根路径，确认 API 正常运行"""
    return {"message": "星辰商品管理AI系统 API 运行中"}

@app.get("/products")
def get_products():
    """获取所有商品列表"""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return {"products": [p.to_dict() for p in products]}
    finally:
        db.close()

@app.get("/products/{spu_id}")
def get_product(spu_id: str):
    """根据 SPU 编号获取单个商品"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        return product.to_dict()
    finally:
        db.close()

@app.post("/products")
def create_product(data: ProductCreate):
    """创建新商品"""
    db = SessionLocal()
    try:
        # 检查 SPU 编号是否已存在
        existing = db.query(Product).filter(Product.spu_id == data.spu_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"SPU编号 {data.spu_id} 已存在")
        # 创建商品对象
        product = Product(
            spu_id=data.spu_id,
            name=data.name,
            category=data.category,
            price=data.price,
            cost=data.cost,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return {"message": "创建成功", "product": product.to_dict()}
    finally:
        db.close()

@app.put("/products/{spu_id}")
def update_product(spu_id: str, data: ProductUpdate):
    """修改商品信息"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        # 只更新传入的字段（None 表示不修改）
        if data.name is not None:
            product.name = data.name
        if data.category is not None:
            product.category = data.category
        if data.price is not None:
            product.price = data.price
        if data.cost is not None:
            product.cost = data.cost
        db.commit()
        db.refresh(product)
        return {"message": "修改成功", "product": product.to_dict()}
    finally:
        db.close()

@app.delete("/products/{spu_id}")
def delete_product(spu_id: str):
    """删除商品"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        db.delete(product)
        db.commit()
        return {"message": "删除成功"}
    finally:
        db.close()

# ==============================
# 第二部分：库存管理接口
# ==============================

@app.get("/inventory/{spu_id}")
def get_inventory(spu_id: str):
    """查询某个商品的库存"""
    db = SessionLocal()
    try:
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if not inventory:
            raise HTTPException(status_code=404, detail="库存记录不存在")
        return inventory.to_dict()
    finally:
        db.close()

@app.post("/inventory")
def upsert_inventory(spu_id: str, stock: int, warehouse: str = "主仓库"):
    """新增或更新库存（先检查商品是否存在）"""
    db = SessionLocal()
    try:
        # 先检查商品是否存在
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 {spu_id} 不存在，无法添加库存")
        # 查找是否已有库存记录
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if inventory:
            # 已有记录，更新
            inventory.stock = stock
            inventory.warehouse = warehouse
        else:
            # 没有记录，新建
            inventory = Inventory(spu_id=spu_id, stock=stock, warehouse=warehouse)
            db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return {"message": "库存更新成功", "inventory": inventory.to_dict()}
    finally:
        db.close()

# ==============================
# 第三部分：销售管理接口
# ==============================

@app.post("/sales")
def create_sales(spu_id: str, quantity: int, amount: float):
    """记录销售（检查商品→检查库存→扣减库存→记录销售）"""
    db = SessionLocal()
    try:
        # 1. 检查商品是否存在
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 {spu_id} 不存在")
        # 2. 检查库存记录是否存在
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if not inventory:
            raise HTTPException(status_code=400, detail=f"商品 {spu_id} 没有库存记录，无法销售")
        # 3. 检查库存是否充足
        if inventory.stock < quantity:
            raise HTTPException(status_code=400, detail=f"库存不足，当前库存 {inventory.stock}件，需要{quantity}件")
        # 4. 扣减库存
        inventory.stock -= quantity
        # 5. 创建销售记录
        sales = SalesRecord(spu_id=spu_id, quantity=quantity, amount=amount)
        db.add(sales)
        db.commit()
        db.refresh(sales)
        db.refresh(inventory)
        return {
            "message": "销售成功",
            "sales": sales.to_dict(),
            "remaining_stock": inventory.stock,
        }
    finally:
        db.close()

@app.get("/sales")
def get_sales(spu_id: Optional[str] = None):
    """获取销售记录（可按 SPU 筛选）"""
    db = SessionLocal()
    try:
        query = db.query(SalesRecord)
        if spu_id:
            query = query.filter(SalesRecord.spu_id == spu_id)
        records = query.all()
        return {"sales": [s.to_dict() for s in records]}
    finally:
        db.close()

# ==============================
# 第四部分：统计接口
# ==============================

@app.get("/stats/summary")
def get_stats_summary():
    """获取经营概览统计"""
    db = SessionLocal()
    try:
        product_count = db.query(Product).count()
        total_stock = db.query(func.sum(Inventory.stock)).scalar() or 0
        total_sales = db.query(func.sum(SalesRecord.amount)).scalar() or 0
        return {
            "product_count": product_count,
            "total_stock": total_stock,
            "total_sales": total_sales,
        }
    finally:
        db.close()

# ==============================
# 第五部分：RAG 文档问答接口
# ==============================

@app.get("/health")
def health_check():
    """健康检查，返回知识库文档数量"""
    return {
        "status": "ok",
        "doc_count": rag_collection.count(),
    }

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """RAG 问答：检索相关文档，让大模型基于文档回答问题"""
    question = request.question

    # 第一步：从 ChromaDB 检索最相关的文档片段
    results = rag_collection.query(
        query_texts=[question],   # 用户的问题
        n_results=2,              # 返回最相关的 2 条
    )

    # 提取检索到的文档片段
    sources = results["documents"][0]

    # 拼接成参考文档字符串
    context = ""
    for i, doc in enumerate(sources):
        context += f"[{i+1}] {doc}\n\n"

    # 构造系统提示词，让大模型基于参考文档回答
    system_prompt = f"""你是一个技术文档问答助手。请根据以下参考文档内容回答用户的问题。
如果参考文档中没有相关信息，请如实说"文档中没有相关内容"，不要编造答案。

参考文档：
{context}"""

    # 组装消息列表
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]

    # 调用大模型生成回答
    response = llm.invoke(messages)

    # 返回结构化响应
    return AnswerResponse(
        question=question,
        answer=response.content,
        sources=sources,
    )

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """文档上传：接收 txt 文件，自动切块存入知识库"""
    # 只允许 .txt 文件
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="只支持 .txt 文件")

    # 读取文件内容
    content = (await file.read()).decode("utf-8")

    # 创建文本分割器
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    # 切块
    chunks = splitter.split_text(content)

    # 获取当前文档数量，用于生成不重复的 id
    current_count = rag_collection.count()

    # 逐块存入 ChromaDB
    for i, chunk in enumerate(chunks):
        rag_collection.add(
            documents=[chunk],
            metadatas=[{"source": file.filename, "chunk_index": i}],
            ids=[f"upload_{current_count + i}"],
        )

    return UploadResponse(
        filename=file.filename,
        chunk_count=len(chunks),
        total_chunks=rag_collection.count(),
    )

# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
