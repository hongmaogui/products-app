# ========== 股票数据工具函数 ==========
# 使用 AKShare 库获取免费A股数据（东方财富/新浪等数据源）
# 每个函数都是一个"工具"，Agent 会根据用户问题自动选择调用

# 导入 akshare 库，用来获取股票数据
import akshare as ak
# 导入 pandas，用来处理表格数据
import pandas as pd
# 导入 json，用来把数据转成文本
import json
# 导入 traceback，用来获取详细错误信息
import traceback
# 导入时间模块，用于缓存过期判断
import time

# ========== 数据缓存 ==========
# 缓存结构：{"data": DataFrame, "timestamp": 时间戳}
# 缓存有效期：5分钟（300秒），避免频繁调用AKShare拉取全量数据
_cache = {
    "spot_data": None,      # 全量A股实时行情缓存
    "cache_time": 0,        # 缓存时间戳
    "cache_ttl": 300        # 缓存有效期（秒）
}


def _get_spot_data_cached() -> pd.DataFrame:
    """
    获取全量A股实时行情数据（带缓存）
    如果缓存未过期，直接返回缓存数据；否则重新拉取并更新缓存
    """
    current_time = time.time()

    # 检查缓存是否有效（有数据且未过期）
    if _cache["spot_data"] is not None and (current_time - _cache["cache_time"]) < _cache["cache_ttl"]:
        return _cache["spot_data"]

    # 缓存过期或无缓存，重新拉取数据
    print("正在从AKShare拉取全量A股数据...")
    df = ak.stock_zh_a_spot_em()
    print(f"拉取完成，共 {len(df)} 条数据")

    # 更新缓存
    _cache["spot_data"] = df
    _cache["cache_time"] = current_time

    return df


def get_stock_quote(symbol: str) -> str:
    """
    查询某只股票的实时行情（当前价格、涨跌幅、成交量等）
    参数 symbol: 股票代码，如 "000001"（平安银行）、"600519"（贵州茅台）
    返回: 行情信息的文本描述
    """
    try:
        # 使用缓存获取全量A股实时行情（避免重复拉取）
        df = _get_spot_data_cached()

        # 从全部A股数据中筛选出目标股票
        stock = df[df["代码"] == symbol]

        # 如果没有找到这只股票
        if stock.empty:
            return f"未找到股票代码 {symbol}，请检查代码是否正确"

        # 取第一行数据（理论上代码唯一，只有一行）
        row = stock.iloc[0]

        # 把关键字段提取出来，组成易读的文本
        result = (
            f"股票：{row['名称']}（{row['代码']}）\n"
            f"当前价格：{row['最新价']} 元\n"
            f"涨跌幅：{row['涨跌幅']}%\n"
            f"涨跌额：{row['涨跌额']} 元\n"
            f"成交量：{row['成交量']} 手\n"
            f"成交额：{row['成交额']} 元\n"
            f"最高价：{row['最高']} 元\n"
            f"最低价：{row['最低']} 元\n"
            f"开盘价：{row['今开']} 元\n"
            f"昨收价：{row['昨收']} 元\n"
        )

        return result

    except Exception as e:
        # 如果出错，返回详细错误信息方便排查
        return f"查询行情失败：{str(e)}\n{traceback.format_exc()}"


def get_stock_history(symbol: str, period: str = "daily", days: int = 30) -> str:
    """
    查询某只股票的历史K线数据
    参数 symbol: 股票代码，如 "000001"
    参数 period: K线周期，"daily"=日线, "weekly"=周线, "monthly"=月线
    参数 days: 最近多少天的数据，默认30天
    返回: 历史K线数据的文本描述
    """
    try:
        # 调用 AKShare 获取个股历史行情
        # adjust="qfq" 表示前复权（把分红送股的影响去掉，价格更连续）
        df = ak.stock_zh_a_hist(
            symbol=symbol,        # 股票代码
            period=period,         # K线周期
            adjust="qfq"           # 前复权
        )

        # 如果返回数据为空
        if df.empty:
            return f"未找到股票 {symbol} 的历史数据"

        # 只取最近 days 天的数据
        df = df.tail(days)

        # 构造返回文本：先给一个总结，再列出每天的数据
        result = f"股票 {symbol} 最近 {days} 天的{period}K线数据：\n\n"

        for _, row in df.iterrows():
            result += (
                f"日期：{row['日期']} | "
                f"开盘：{row['开盘']} | "
                f"收盘：{row['收盘']} | "
                f"最高：{row['最高']} | "
                f"最低：{row['最低']} | "
                f"成交量：{row['成交量']}手 | "
                f"涨跌幅：{row['涨跌幅']}%\n"
            )

        return result

    except Exception as e:
        return f"查询历史数据失败：{str(e)}\n{traceback.format_exc()}"


def get_stock_info(symbol: str) -> str:
    """
    查询某只股票的基本信息（公司名称、行业、总市值等）
    参数 symbol: 股票代码，如 "000001"
    返回: 股票基本信息的文本描述
    """
    try:
        # 使用缓存获取全部A股的实时行情数据（里面包含名称、最新价、总市值等）
        df = _get_spot_data_cached()

        # 筛选目标股票
        stock = df[df["代码"] == symbol]

        if stock.empty:
            return f"未找到股票代码 {symbol}"

        row = stock.iloc[0]

        # 提取基本信息字段
        result = (
            f"股票基本信息：\n"
            f"代码：{row['代码']}\n"
            f"名称：{row['名称']}\n"
            f"最新价：{row['最新价']} 元\n"
            f"总市值：{row['总市值']} 元\n"
            f"流通市值：{row['流通市值']} 元\n"
            f"市盈率（动态）：{row['市盈率-动态']}\n"
            f"市净率：{row['市净率']}\n"
            f"52周最高：{row['52周最高']} 元\n"
            f"52周最低：{row['52周最低']} 元\n"
        )

        return result

    except Exception as e:
        return f"查询基本信息失败：{str(e)}\n{traceback.format_exc()}"


def get_market_index() -> str:
    """
    查询主要大盘指数的实时行情（上证指数、深证成指、创业板指）
    不需要参数，直接返回三大指数数据
    """
    try:
        # 获取A股大盘指数实时行情
        df = ak.stock_zh_index_spot_em()

        # 我们只关心三个主要指数
        target_codes = ["000001", "399001", "399006"]
        target_names = {
            "000001": "上证指数",
            "399001": "深证成指",
            "399006": "创业板指"
        }

        result = "主要大盘指数行情：\n\n"

        # 遍历三个指数代码，从数据中筛选
        for code in target_codes:
            index_data = df[df["代码"] == code]
            if not index_data.empty:
                row = index_data.iloc[0]
                result += (
                    f"{target_names[code]}：\n"
                    f"  当前点位：{row['最新价']}\n"
                    f"  涨跌幅：{row['涨跌幅']}%\n"
                    f"  涨跌额：{row['涨跌额']}\n"
                    f"  成交量：{row['成交量']} 手\n"
                    f"  成交额：{row['成交额']} 元\n\n"
                )

        return result

    except Exception as e:
        return f"查询大盘指数失败：{str(e)}\n{traceback.format_exc()}"


def search_stock_by_name(name: str) -> str:
    """
    根据股票名称模糊搜索股票代码
    参数 name: 股票名称关键词，如 "平安"、"茅台"
    返回: 匹配的股票列表
    """
    try:
        # 使用带缓存的全量数据获取函数，避免重复拉取（5分钟内复用缓存）
        df = _get_spot_data_cached()

        # 用 str.contains 做模糊匹配（名称中包含关键词）
        matched = df[df["名称"].str.contains(name, na=False)]

        if matched.empty:
            return f"未找到名称包含「{name}」的股票"

        # 只取前10条结果，避免返回太多
        matched = matched.head(10)

        result = f"名称包含「{name}」的股票（最多显示10条）：\n\n"

        for _, row in matched.iterrows():
            result += f"代码：{row['代码']} | 名称：{row['名称']} | 最新价：{row['最新价']} 元\n"

        return result

    except Exception as e:
        return f"搜索股票失败：{str(e)}\n{traceback.format_exc()}"


def get_sector_performance(sector_type: str = "行业") -> str:
    """
    查询板块行情（行业板块或概念板块的涨跌幅排行）
    参数 sector_type: 板块类型，"行业"=行业板块（默认），"概念"=概念板块
    返回: 板块涨跌幅排行（前10名）
    """
    try:
        # 根据板块类型调用不同的AKShare接口
        if sector_type == "概念":
            df = ak.stock_board_concept_name_em()  # 概念板块
        else:
            df = ak.stock_board_industry_name_em()  # 行业板块

        # 按涨跌幅排序，取前10名
        df_sorted = df.sort_values("涨跌幅", ascending=False).head(10)

        result = f"{sector_type}板块涨幅前10名：\n\n"

        for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
            result += (
                f"{i}. {row['板块名称']} | "
                f"涨跌幅：{row['涨跌幅']}% | "
                f"总市值：{row['总市值']}亿 | "
                f"上涨家数：{row['上涨家数']} | "
                f"下跌家数：{row['下跌家数']}\n"
            )

        return result

    except Exception as e:
        return f"查询板块行情失败：{str(e)}\n{traceback.format_exc()}"


def get_capital_flow(symbol: str) -> str:
    """
    查询某只股票的资金流向（主力资金、超大单、大单、中单、小单）
    参数 symbol: 股票代码，如 "000001"
    返回: 资金流向数据
    """
    try:
        # 获取个股资金流向数据
        df = ak.stock_individual_fund_flow_rank(indicator="今日")

        # 筛选目标股票
        stock = df[df["代码"] == symbol]

        if stock.empty:
            return f"未找到股票代码 {symbol} 的资金流向数据"

        row = stock.iloc[0]

        result = (
            f"股票 {row['名称']}（{row['代码']}）资金流向：\n\n"
            f"最新价：{row['最新价']} 元\n"
            f"涨跌幅：{row['涨跌幅']}%\n\n"
            f"【主力资金】\n"
            f"  净流入：{row['主力净流入-净额']} 元\n"
            f"  净占比：{row['主力净流入-净占比']}%\n\n"
            f"【超大单】\n"
            f"  净流入：{row['超大单净流入-净额']} 元\n"
            f"  净占比：{row['超大单净流入-净占比']}%\n\n"
            f"【大单】\n"
            f"  净流入：{row['大单净流入-净额']} 元\n"
            f"  净占比：{row['大单净流入-净占比']}%\n\n"
            f"【中单】\n"
            f"  净流入：{row['中单净流入-净额']} 元\n"
            f"  净占比：{row['中单净流入-净占比']}%\n\n"
            f"【小单】\n"
            f"  净流入：{row['小单净流入-净额']} 元\n"
            f"  净占比：{row['小单净流入-净占比']}%\n"
        )

        return result

    except Exception as e:
        return f"查询资金流向失败：{str(e)}\n{traceback.format_exc()}"


def get_top_gainers_losers(top_n: int = 10) -> str:
    """
    查询A股涨跌幅排行榜（涨幅前N名和跌幅前N名）
    参数 top_n: 显示前N名，默认10
    返回: 涨幅榜和跌幅榜
    """
    try:
        # 使用带缓存的全量数据获取函数，避免重复拉取（5分钟内复用缓存）
        df = _get_spot_data_cached()

        # 过滤掉ST股和新股（涨跌幅异常的）
        df = df[~df["名称"].str.contains("ST|N|C", na=False)]

        # 涨幅前N名
        top_gainers = df.nlargest(top_n, "涨跌幅")
        result = f"📈 涨幅榜前{top_n}名：\n\n"

        for i, (_, row) in enumerate(top_gainers.iterrows(), 1):
            result += (
                f"{i}. {row['名称']}（{row['代码']}）| "
                f"价格：{row['最新价']}元 | "
                f"涨幅：{row['涨跌幅']}%\n"
            )

        # 跌幅前N名
        top_losers = df.nsmallest(top_n, "涨跌幅")
        result += f"\n📉 跌幅榜前{top_n}名：\n\n"

        for i, (_, row) in enumerate(top_losers.iterrows(), 1):
            result += (
                f"{i}. {row['名称']}（{row['代码']}）| "
                f"价格：{row['最新价']}元 | "
                f"跌幅：{row['涨跌幅']}%\n"
            )

        return result

    except Exception as e:
        return f"查询涨跌排行失败：{str(e)}\n{traceback.format_exc()}"
