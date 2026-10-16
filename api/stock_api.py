# ========== 股票问答路由模块 ==========
# 提供股票智能问答的API接口

# FastAPI 路由组件
# APIRouter: 创建独立的路由模块，最后注册到主 app
# HTTPException: 抛出 HTTP 错误
from fastapi import APIRouter, HTTPException
# BaseModel: 定义请求数据结构
from pydantic import BaseModel
# Optional: 可选参数
from typing import Optional, List

# 导入股票Agent的对话函数
from agents.stock_agent import chat_with_stock_agent

# ========== 创建路由 ==========

# 创建路由器，所有接口路径前缀为 /api/stock，标签为"股票智能问答"
router = APIRouter(prefix="/api/stock", tags=["股票智能问答"])


# ========== 请求数据模型 ==========

class StockQuestionRequest(BaseModel):
    """
    股票问答的请求数据结构
    question: 用户的问题（必填）
    session_id: 会话ID，用于区分不同对话（可选，默认"default"）
    history: 之前的对话历史，用于多轮对话（可选）
    """
    question: str                          # 用户的问题
    session_id: str = "default"            # 会话ID，默认"default"
    history: Optional[List[dict]] = None   # 对话历史，默认None


# ========== API 接口 ==========

@router.post("/ask")
def stock_ask(request: StockQuestionRequest):
    """
    股票智能问答接口
    接收用户问题，Agent自动调用工具查询数据并回答
    返回: {"answer": "回答内容", "sources": ["工具调用记录"]}
    """
    try:
        # 调用Agent对话函数
        result = chat_with_stock_agent(
            question=request.question,          # 用户问题
            session_id=request.session_id,      # 会话ID
            history=request.history,            # 对话历史
        )

        # 返回Agent的回答
        return result

    except Exception as e:
        # 如果出错，返回500错误
        raise HTTPException(status_code=500, detail=f"股票问答失败：{str(e)}")


@router.get("/health")
def stock_health():
    """
    股票服务健康检查接口
    返回: {"status": "ok", "message": "股票Agent服务正常"}
    """
    return {"status": "ok", "message": "股票Agent服务正常"}
