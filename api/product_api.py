# ========== 商品管理路由模块 ==========
# 包含：商品 CRUD、库存管理、销售管理、统计接口

# FastAPI 路由组件
# APIRouter: 创建独立的路由模块，最后注册到主 app
# HTTPException: 抛出 HTTP 错误
from fastapi import APIRouter, HTTPException
# BaseModel: 定义请求数据结构
from pydantic import BaseModel
# Optional: 可选参数
from typing import Optional
# SQLAlchemy 会话和聚合函数
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
# 导入数据库引擎和数据模型
from db.models import engine, Product, Inventory, SalesRecord

# ========== 数据库会话 ==========

# 创建会话工厂，每个请求用独立会话
SessionLocal = sessionmaker(bind=engine)

# ========== 创建路由 ==========

# 创建路由器实例
# 所有路由都会自动加上 /api/product 前缀
router = APIRouter(prefix="/api/product", tags=["商品管理"])

# ========== 数据模型（Pydantic） ==========

# 创建商品的请求格式
class ProductCreate(BaseModel):
    spu_id: str                     # SPU 编号，必填
    name: str                       # 商品名称，必填
    category: Optional[str] = None  # 分类，可选
    price: float                    # 售价，必填
    cost: Optional[float] = None    # 成本价，可选

# 修改商品的请求格式（所有字段可选）
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None

# ==============================
# 商品 CRUD 接口
# ==============================

@router.get("/products")
def get_products():
    """获取所有商品列表"""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return {"products": [p.to_dict() for p in products]}
    finally:
        db.close()

@router.get("/products/{spu_id}")
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

@router.post("/products")
def create_product(data: ProductCreate):
    """创建新商品"""
    db = SessionLocal()
    try:
        # 检查 SPU 是否已存在
        existing = db.query(Product).filter(Product.spu_id == data.spu_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"SPU编号 {data.spu_id} 已存在")
        # 创建商品
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

@router.put("/products/{spu_id}")
def update_product(spu_id: str, data: ProductUpdate):
    """修改商品信息"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        # 只更新传入的字段
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

@router.delete("/products/{spu_id}")
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
# 库存管理接口
# ==============================

@router.get("/inventory/{spu_id}")
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

@router.post("/inventory")
def upsert_inventory(spu_id: str, stock: int, warehouse: str = "主仓库"):
    """新增或更新库存（先检查商品是否存在）"""
    db = SessionLocal()
    try:
        # 检查商品是否存在
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 {spu_id} 不存在，无法添加库存")
        # 查找或创建库存记录
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if inventory:
            inventory.stock = stock
            inventory.warehouse = warehouse
        else:
            inventory = Inventory(spu_id=spu_id, stock=stock, warehouse=warehouse)
            db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return {"message": "库存更新成功", "inventory": inventory.to_dict()}
    finally:
        db.close()

# ==============================
# 销售管理接口
# ==============================

@router.post("/sales")
def create_sales(spu_id: str, quantity: int, amount: float):
    """记录销售（检查商品→检查库存→扣减库存→记录销售）"""
    db = SessionLocal()
    try:
        # 1. 检查商品
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 {spu_id} 不存在")
        # 2. 检查库存
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if not inventory:
            raise HTTPException(status_code=400, detail=f"商品 {spu_id} 没有库存记录")
        # 3. 检查库存充足
        if inventory.stock < quantity:
            raise HTTPException(status_code=400, detail=f"库存不足，当前{inventory.stock}件，需要{quantity}件")
        # 4. 扣库存 + 记销售
        inventory.stock -= quantity
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

@router.get("/sales")
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
# 统计接口
# ==============================

@router.get("/stats/summary")
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
