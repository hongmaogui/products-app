# ========== 股票智能问答 Agent ==========
# 基于 LangChain + 智谱AI，能理解自然语言并自动调用股票工具

# 导入 os 模块，用来读取环境变量
import os
# 导入 dotenv，用来从 .env 文件加载配置
from dotenv import load_dotenv
# 加载 .env 文件中的环境变量（自动查找项目根目录的 .env）
load_dotenv()

# 导入 LangChain 的 ChatOpenAI，用来调用智谱AI大模型
from langchain_openai import ChatOpenAI
# 导入 @tool 装饰器，把普通函数变成 Agent 可识别的工具
from langchain_core.tools import tool
# 导入 create_react_agent，用来创建"思考-行动-观察"循环的Agent
from langgraph.prebuilt import create_react_agent

# 导入 tools 包里的股票工具函数
from tools.stock_tools import (
    get_stock_quote,          # 查实时行情
    get_stock_history,        # 查历史K线
    get_stock_info,           # 查基本信息
    get_market_index,         # 查大盘指数
    search_stock_by_name,     # 按名称搜股票
    get_sector_performance,   # 查板块行情
    get_capital_flow,         # 查资金流向
    get_top_gainers_losers,   # 查涨跌排行
    get_technical_analysis,   # 查技术指标（MA/MACD/KDJ/RSI）
)

# ========== 用 @tool 装饰器把函数注册成 Agent 工具 ==========
# 每个工具需要：函数名、参数说明、功能描述（Agent靠描述来决定调用哪个）

@tool
def query_stock_quote(symbol: str) -> str:
    """
    查询某只A股的实时行情，包括当前价格、涨跌幅、成交量、最高最低价等。
    参数 symbol 是6位股票代码，例如 "000001" 代表平安银行，"600519" 代表贵州茅台。
    如果不知道股票代码，先用 search_stock 工具按名称搜索。
    """
    # 直接调用 tools 包里的函数，返回结果文本
    return get_stock_quote(symbol)


@tool
def query_stock_history(symbol: str, period: str = "daily", days: int = 30) -> str:
    """
    查询某只A股的历史K线数据，可以看到每天的开盘价、收盘价、最高最低价和成交量。
    参数 symbol: 6位股票代码，如 "000001"。
    参数 period: K线周期，"daily"=日线（默认），"weekly"=周线，"monthly"=月线。
    参数 days: 最近多少天的数据，默认30天。
    适用场景：用户问"最近走势怎么样"、"过去一个月涨了多少"等问题。
    """
    return get_stock_history(symbol, period, days)


@tool
def query_stock_info(symbol: str) -> str:
    """
    查询某只A股的基本信息，包括公司名称、总市值、流通市值、市盈率、市净率、52周高低点等。
    参数 symbol: 6位股票代码，如 "600519"。
    适用场景：用户问"市值多少"、"市盈率是多少"等基本面问题。
    """
    return get_stock_info(symbol)


@tool
def query_market_index() -> str:
    """
    查询A股主要大盘指数的实时行情，包括上证指数、深证成指、创业板指。
    不需要参数，直接返回三大指数的当前点位和涨跌幅。
    适用场景：用户问"今天大盘怎么样"、"上证指数多少点"等问题。
    """
    return get_market_index()


@tool
def search_stock(name: str) -> str:
    """
    根据股票名称关键词模糊搜索A股，返回匹配的股票代码和名称列表。
    参数 name: 名称关键词，如 "平安"、"茅台"、"宁德"。
    适用场景：用户不知道股票代码时，先用这个工具搜索，拿到代码后再查行情。
    """
    return search_stock_by_name(name)


@tool
def query_sector_performance(sector_type: str = "行业") -> str:
    """
    查询A股板块行情排行（行业板块或概念板块的涨跌幅前10名）。
    参数 sector_type: 板块类型，"行业"=行业板块（默认），"概念"=概念板块。
    适用场景：用户问"今天哪个板块涨得好"、"热门概念板块有哪些"等问题。
    """
    return get_sector_performance(sector_type)


@tool
def query_capital_flow(symbol: str) -> str:
    """
    查询某只A股的资金流向数据，包括主力资金、超大单、大单、中单、小单的净流入额和净占比。
    参数 symbol: 6位股票代码，如 "000001"。
    适用场景：用户问"茅台主力资金流向"、"宁德时代资金流入还是流出"等问题。
    """
    return get_capital_flow(symbol)


@tool
def query_top_gainers_losers(top_n: int = 10) -> str:
    """
    查询A股涨跌幅排行榜（涨幅前N名和跌幅前N名，自动过滤ST股和新股）。
    参数 top_n: 显示前N名，默认10。
    适用场景：用户问"今天涨停的股票有哪些"、"跌幅最大的股票"等问题。
    """
    return get_top_gainers_losers(top_n)


@tool
def query_technical_analysis(symbol: str, period: str = "daily", days: int = 60) -> str:
    """
    查询某只A股的技术指标分析，包括均线系统（MA5/10/20/60）、MACD（金叉/死叉）、
    KDJ随机指标（超买/超卖）、RSI相对强弱指标。
    参数 symbol: 6位股票代码，如 "000001"。
    参数 period: K线周期，"daily"=日线（默认），"weekly"=周线，"monthly"=月线。
    参数 days: 最近多少天的数据，默认60天。
    适用场景：用户问"茅台的技术面怎么样"、"平安银行MACD金叉了吗"、"KDJ超买了吗"等技术分析问题。
    """
    return get_technical_analysis(symbol, period, days)


# ========== 创建 Agent ==========

# 把所有工具放进一个列表，Agent 运行时会自动从中选择
stock_tools_list = [
    query_stock_quote,          # 工具1：查实时行情
    query_stock_history,        # 工具2：查历史K线
    query_stock_info,           # 工具3：查基本信息
    query_market_index,         # 工具4：查大盘指数
    search_stock,               # 工具5：按名称搜索
    query_sector_performance,   # 工具6：查板块行情
    query_capital_flow,         # 工具7：查资金流向
    query_top_gainers_losers,   # 工具8：查涨跌排行
    query_technical_analysis,   # 工具9：查技术指标（MA/MACD/KDJ/RSI）
]

# 系统提示词：告诉Agent它的角色、能力、以及回答规则
stock_system_prompt = """
你是一个专业的A股股票分析助手。你可以帮用户查询：
- 股票行情（实时价格、涨跌幅、成交量等）
- 历史K线（日线、周线、月线走势）
- 基本面信息（市值、市盈率、市净率等）
- 大盘指数（上证指数、深证成指、创业板指）
- 板块行情（行业板块、概念板块涨跌幅排行）
- 资金流向（主力资金、超大单、大单等净流入）
- 涨跌排行榜（涨幅榜、跌幅榜）
- 技术指标分析（MA均线、MACD金叉死叉、KDJ超买超卖、RSI相对强弱）

你的工作流程：
1. 如果用户提到股票名称但没说代码，先用 search_stock 工具搜索股票代码。
2. 拿到代码后，根据用户的问题选择合适的工具查询数据。
3. 拿到数据后，用通俗易懂的中文给用户总结和分析。

注意事项：
- 只回答A股（中国大陆股票）相关问题，不回答港股、美股。
- 不要编造数据，所有数据必须来自工具查询结果。
- 如果用户问的问题超出股票范围，礼貌地告诉他你只能回答A股相关问题。
- 回答时先给结论，再给数据支撑。
- 股票代码是6位数字，如 000001、600519。
- 技术指标分析仅供参考，不构成投资建议，回答时记得提醒用户。
"""

# 创建智谱AI大模型实例
# 从 .env 文件读取配置，避免硬编码敏感信息
# model="glm-4-flash" 是免费模型，速度快，适合工具调用场景
# temperature=0.1 表示回答尽量确定、不随意发挥（查数据需要准确）
stock_llm = ChatOpenAI(
    model=os.getenv("ZHIPU_MODEL", "glm-4-flash"),
    base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
    api_key=os.getenv("ZHIPU_API_KEY"),
    temperature=0.1,
)

# 创建 ReAct Agent（思考→行动→观察→思考→...→回答）
# 第一个参数是模型（位置参数），tools 是工具列表
# 注意：langgraph 版本的 create_react_agent 不支持 prompt 参数
stock_agent = create_react_agent(
    stock_llm,
    tools=stock_tools_list,
)

# ========== 对话记忆 ==========
# 用字典存储每个会话的聊天历史，key是会话ID，value是消息列表
stock_chat_memory = {}


def chat_with_stock_agent(question: str, session_id: str = "default", history: list = None) -> dict:
    """
    和股票Agent对话的主函数
    参数 question: 用户的问题
    参数 session_id: 会话ID，用来区分不同用户的对话
    参数 history: 之前的对话历史（用于多轮对话）
    返回: {"answer": "回答内容", "sources": ["工具调用记录"]}
    """
    # 如果没有传历史，就用 session_id 从记忆中取
    if history is None:
        history = stock_chat_memory.get(session_id, [])

    # 把历史消息转成 LangChain 能用的消息格式
    messages = []
    # 先加入系统提示词，告诉Agent它的角色和规则
    messages.append({"role": "system", "content": stock_system_prompt})
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})

    # 加上当前用户的问题
    messages.append({"role": "user", "content": question})

    # 调用 Agent，让它思考并调用工具
    try:
        result = stock_agent.invoke({"messages": messages})

        # 从结果中提取Agent的最终回答（langgraph版本返回messages列表）
        answer = result["messages"][-1].content

        # 提取中间步骤（Agent调用了哪些工具）作为参考来源
        sources = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                tool_name = step[0].tool        # 工具名称
                tool_input = step[0].tool_input  # 工具输入参数
                sources.append(f"调用工具：{tool_name}({tool_input})")

    except Exception as e:
        # 如果Agent执行出错，返回错误信息
        answer = f"抱歉，出错了：{str(e)}"
        sources = []

    # 把当前对话存入记忆（用户问题 + Agent回答）
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    stock_chat_memory[session_id] = history

    # 返回回答和来源
    return {"answer": answer, "sources": sources}
