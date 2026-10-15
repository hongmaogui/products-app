from fastapi import FastAPI,HTTPException  
from pydantic import BaseModel
from typing import Optional
from models import engine,Product,Inventory,SalesRecord
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="laji商品管理系统")

class ProductCreate(BaseModel):
    spu_id:str
    name:str
    category:Optional[str] = None
    price:float
    cost:Optional[float] = None


class ProductUpdate(BaseModel):
    name:Optional[str] = None 
    category:Optional[str] = None
    price:Optional[float] = None
    cost:Optional[float] = None


@app.get("/")
def root():
    return {"message":"laji商品管理系统API运行"}

@app.get("/products")
def get_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return {"products":[p.to_dict() for p in products]}
    finally:
        db.close()

@app.get("/products/{spu_id}")
def get_product(spu_id:str):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404,detail="商品不存在")
        return product.to_dict()
    finally:
        db.close()

@app.post("/products")
def create_product(data:ProductCreate):
    db = SessionLocal()
    try:
        existing = db.query(Product).filter(Product.spu_id == data.spu_id).first()
        if existing:
            raise HTTPException(status_code=400,detail=f"SPU编号 {data.spu_id} 已存在")

        product = Product(
            spu_id = data.spu_id,
            name = data.name,
            category=data.category,
            price = data.price,
            cost = data.cost
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return {"message":"创建成功","product":product.to_dict()}
    finally:
        db.close()

@app.put("/products/{spu_id}")
def update_product(spu_id:str,data:ProductUpdate):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404,detail="商品不存在")
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
        return {"message":"修改成功","product":product.to_dict()}
    finally:
        db.close()

@app.delete("/products/{spu_id}")
def delete_product(spu_id:str):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404,detail="商品不存在")
        db.delete(product)
        db.commit()
        return {"messages":"删除成功"}
    finally:
        db.close()

@app.get("/inventory/{spu_id}")
def get_inventory(spu_id:str):
    db = SessionLocal()
    try:
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if not inventory:
            raise HTTPException(status_code=404,detail="库存记录不存在")
        return inventory.to_dict()
    finally:
        db.close()

@app.post("/inventory")
def upsert_inventory(spu_id:str,stock:int,warehouse:str="主仓库"):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404,detail=f"商品 {spu_id} 不存在，无法添加库存")
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if inventory:
            inventory.stcok = stock
            inventory.warehouse = warehouse
        else:
            inventory = Inventory(spu_id=spu_id,stock=stock,warehouse=warehouse)
            db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return {"message":"库存更新成功","inventory":inventory.to_dict()}
    finally:
        db.close()

@app.post("/sales")
def creat_sales(spu_id:str,quantity:int,amount:float):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            raise HTTPException(status_code=404,detail=f"商品 {spu_id} 不存在")
        inventory = db.query(Inventory).filter(Inventory.spu_id==spu_id).first()
        if not inventory:
            raise HTTPException(status_code=400,detail=f"商品 {spu_id} 没有库存记录，无法销售")
        if inventory.stock < quantity:
            raise HTTPException(status_code=400,detail=f"库存不足，当前库存 {inventory.stock}件，需要{quantity}件")
        inventory.stock -= quantity

        sales = SalesRecord(spu_id=spu_id,quantity=quantity,amount=amount)
        db.add(sales)
        db.commit()
        db.refresh(sales)
        db.refresh(inventory)
        return {
            "message":"销售成功",
            "sales":sales.to_dict(),
            "remaining_stock":inventory.stock,
        }
    finally:
        db.close()

@app.get("/sales")
def get_sales(spu_id:Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(SalesRecord)
        if spu_id:
            query = query.filter(SalesRecord.spu_id == spu_id)
        records = query.all()
        return {"sales":[s.to_dict() for s in records]}
    finally:
        db.close()

@app.get("/stats/summary")
def get_stats_summary():
    db = SessionLocal()
    try:
        product_count = db.query(Product).count()
        total_stock = db.query(func.sum(Inventory.stock)).scalar() or 0
        total_sales = db.query(func.sum(SalesRecord.amount)).scalar() or 0
        return {
            "product_count":product_count,
            "total_stock":total_stock,
            "total_sales":total_sales
        }

    finally:
        db.close()
