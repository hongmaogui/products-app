from sqlalchemy import create_engine,Column,Integer,String,Float,DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import func


engine = create_engine("sqlite:///xingchen.db",echo=True)

Base = declarative_base()


class Product(Base):
    __tablename__ = "porducts"

    id = Column(Integer,primary_key=True,autoincrement=True)
    spu_id = Column(String(50),unique=True,nullable=False)
    name = Column(String(200),nullable=False)
    category = Column(String(100))
    price = Column(Float,nullable=False)
    cost = Column(Float)
    created_at = Column(DateTime(),default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "spu_id": self.spu_id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "cost": self.cost,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer,primary_key=True,autoincrement=True)
    spu_id = Column(String(50),nullable=False)
    stock = Column(Integer,default=0)
    warehouse = Column(String(100),default="主仓库")
    updated_at = Column(DateTime(),default=datetime.now,onupdate=datetime.now)

    def to_dict(self):
        return{
            "id":self.id,
            "spu_id":self.spu_id,
            "stock":self.stock,
            "warehouse":self.warehouse,
            "updated_at":self.updated_at.isoformat() if self.updated_at else None
        }

class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer,primary_key=True,autoincrement=True)
    spu_id = Column(String(50),nullable=False)
    quantity = Column(Integer,nullable=False)
    amount = Column(Float,nullable=False)
    sale_date = Column(DateTime(),default=datetime.now)

    def to_dict(self):
        return {
            "id":self.id,
            "spu_id":self.spu_id,
            "quantity":self.quantity,
            "amount":self.amount,
            "sale_date":self.sale_date.strftime("%Y-%m-%d %H:%M:%S") if self.sale_date else None,
        }



Base.metadata.create_all(engine)
print("数据库表创建成功！")