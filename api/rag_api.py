# ========== RAG 文档问答路由模块 ==========
# 包含：文档问答、文档上传、健康检查

# FastAPI 路由组件
from fastapi import APIRouter, HTTPException, UploadFile, File
# Pydantic 数据模型
from pydantic import BaseModel
from typing import Optional
# ChromaDB 向量数据库
import chromadb
# 文本分割器
from langchain_text_splitters import RecursiveCharacterTextSplitter
# LangChain 大模型和消息类型
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
# 文件处理
from PyPDF2 import PdfReader
from io import BytesIO
import os
# 导入 dotenv，用来从 .env 文件加载配置
from dotenv import load_dotenv
# 加载 .env 文件中的环境变量
load_dotenv()

# ========== 初始化依赖 ==========

# 获取项目根目录（api/的父目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ChromaDB 客户端和集合（数据文件放在 data/rag_docs）
CHROMA_PATH = os.path.join(BASE_DIR, "data", "rag_docs")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
rag_collection = chroma_client.get_or_create_collection(name="tech_docs")

# 智谱 AI 大模型（从 .env 读取配置）
llm = ChatOpenAI(
    base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
    model=os.getenv("ZHIPU_MODEL", "glm-4-flash"),
    api_key=os.getenv("ZHIPU_API_KEY"),
)

# ========== 创建路由 ==========

# 所有路由加 /api/rag 前缀
router = APIRouter(prefix="/api/rag", tags=["RAG文档问答"])

# ========== 文档解析工具 ==========

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    根据文件扩展名提取纯文本
    支持 .txt、.md、.pdf 三种格式
    """
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        # PDF：用 PyPDF2 逐页提取
        reader = PdfReader(BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    else:
        # .txt 和 .md 直接解码
        return file_content.decode("utf-8")

# ========== 启动时自动加载预置文档 ==========

if rag_collection.count() == 0:
    docs_dir = os.path.join(BASE_DIR, "docs")
    if os.path.exists(docs_dir):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        chunk_id = 0
        for filename in os.listdir(docs_dir):
            if any(filename.lower().endswith(ext) for ext in [".txt", ".md", ".pdf"]):
                filepath = os.path.join(docs_dir, filename)
                with open(filepath, "rb") as f:
                    file_content = f.read()
                content = extract_text_from_file(file_content, filename)
                chunks = splitter.split_text(content)
                for chunk in chunks:
                    rag_collection.add(
                        documents=[chunk],
                        metadatas=[{"source": filename, "chunk_index": chunk_id}],
                        ids=[f"doc_{chunk_id}"],
                    )
                    chunk_id += 1
        print(f"[RAG] 自动加载预置文档完成，共 {chunk_id} 块")

# ========== 数据模型（Pydantic） ==========

# 对话历史消息
class ChatMessage(BaseModel):
    role: str       # "user" 或 "assistant"
    content: str    # 消息内容

# 问答请求
class QuestionRequest(BaseModel):
    question: str                       # 用户问题
    n_results: int = 3                  # 返回几条文档，默认 3
    source_filter: Optional[str] = None # 来源过滤，为空搜全部
    history: list[ChatMessage] = []     # 对话历史

# 问答响应
class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]

# 上传响应
class UploadResponse(BaseModel):
    filename: str
    chunk_count: int
    total_chunks: int

# ==============================
# 接口定义
# ==============================

@router.get("/health")
def health_check():
    """健康检查，返回知识库文档数量"""
    return {"status": "ok", "doc_count": rag_collection.count()}

@router.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """RAG 问答：检索文档 + 大模型生成回答"""
    question = request.question
    n_results = request.n_results
    source_filter = request.source_filter

    # 构建过滤条件
    where_filter = {"source": source_filter} if source_filter else None

    # 检索相关文档
    results = rag_collection.query(
        query_texts=[question],
        n_results=n_results,
        where=where_filter,
    )

    sources = results["documents"][0]

    # 拼接参考文档
    context = ""
    for i, doc in enumerate(sources):
        context += f"[{i+1}] {doc}\n\n"

    # 系统提示词
    system_prompt = f"""你是一个技术文档问答助手。请根据以下参考文档内容回答用户的问题。
如果参考文档中没有相关信息，请如实说"文档中没有相关内容"，不要编造答案。

参考文档：
{context}"""

    # 组装消息：系统提示 + 历史对话 + 当前问题
    messages = [SystemMessage(content=system_prompt)]
    for msg in request.history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
    messages.append(HumanMessage(content=question))

    # 调用大模型
    response = llm.invoke(messages)

    return AnswerResponse(
        question=question,
        answer=response.content,
        sources=sources,
    )

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """文档上传：解析、切块、存入知识库"""
    # 检查文件格式
    allowed_ext = [".txt", ".md", ".pdf"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail="只支持 .txt、.md、.pdf 文件")

    # 读取并解析
    file_content = await file.read()
    content = extract_text_from_file(file_content, file.filename)

    # 切块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_text(content)

    # 存入 ChromaDB
    current_count = rag_collection.count()
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
