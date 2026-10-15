from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from models import engine,Product,Inventory,SalesRecord
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

SessionLocal = sessionmaker(bind=engine)


@tool
def query_product(spu_id:str) -> str:
    """根据商品编号查询商品信息。参数 spu_id 是商品编号，比如 SP001。"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.spu_id == spu_id).first()
        if not product:
            return f"商品 {spu_id} 不存在"
        return f"编号：{product.spu_id}，名称：{product.name}，分类：{product.category}，价格：{product.price}元，成本：{product.cost}元"
    finally:
        db.close()

@tool
def list_products(category:str = "") -> str:
    """查询商品列表，可按分类筛选。参数 category 是分类名称，不传则返回所有商品。"""
    db = SessionLocal()
    try:
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        products = query.all()
        if not products:
            return "没有找到商品"
        result = []
        for p in products:
            result.append(f"{p.spu_id}-{p.name}({p.category}) {p.price}元")
        return "\n".join(result)
    finally:
        db.close()

@tool
def check_inventory(spu_id:str) -> str:
    """查询商品库存。参数 spu_id 是商品编号。"""
    db = SessionLocal()
    try:
        inventory = db.query(Inventory).filter(Inventory.spu_id == spu_id).first()
        if not inventory:
            return f"商品{spu_id} 没有库存记录"
        if inventory.stock < 50:
            return f"⚠️ {inventory.spu_id} 库存只剩 {inventory.stock} 件（{inventory.warehouse}），请及时补货！"
        return f"{inventory.spu_id} 当前库存 {inventory.stock} 件（{inventory.warehouse}），库存充足。"
    finally:
        db.close()


@tool
def get_sales_data(spu_id:str) -> str:
    """查询商品销售数据。参数 spu_id 是商品编号。"""
    db = SessionLocal()
    try:
        records = db.query(SalesRecord).filter(SalesRecord.spu_id == spu_id).all()
        if not records:
            return f"商品 {spu_id} 没有销售记录"
        total_qty = sum(r.quantity for r in records)
        total_amount = sum(r.quantity for r in records)
        return f"{spu_id} 共 {len(records)} 笔销售记录，总销量 {total_qty} 件，总销售额 {total_amount} 元。"
    finally:
        db.close()

@tool
def get_stats() -> str:
    """获取整体统计概览：商品总数、总库存、总销售额。"""
    db = SessionLocal()
    try:
        product_count = db.query(Product).count()
        total_stock = db.query(func.sum(Inventory.stock)).scalar() or 0
        total_sales = db.query(func.sum(SalesRecord.amount)).scalar() or 0
        return f"商品总数：{product_count}，总库存：{total_stock} 件，总销售额：{total_sales} 元。"
    finally:
        db.close()

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key="0f5150f6824b46798493bad132e9e981.KlIXMBcsTBD3mm8z"
)

agent = create_react_agent(llm,tools=[query_product,list_products,check_inventory,get_sales_data,get_stats])


thread_store = {}

def chat(user_id:str,user_input:str) -> str:
    history = thread_store.get(user_id,[])
    history.append({"role":"user","content":user_input})
    result = agent.invoke({"messages":history})
    ai_rely = result["messages"][-1].content
    history.append({"role":"assistant","content":ai_rely})
    thread_store[user_id] = history
    return ai_rely

if __name__ == "__main__":
    print("=" * 50)
    print("  星辰商品管理 AI 助手（连接真实数据库）")
    print("  输入 quit 退出")
    print("=" * 50)

    while True:
        user_input = input("\n你：").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("再见！")
            break
        print("AI:",chat("user1",user_input))
    