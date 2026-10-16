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


def get_technical_analysis(symbol: str, period: str = "daily", days: int = 60) -> str:
    """
    获取股票技术指标分析（MA均线、MACD、KDJ、RSI）
    参数 symbol: 股票代码，如 "000001"（平安银行）、"600519"（贵州茅台）
    参数 period: K线周期，"daily"=日线（默认），"weekly"=周线，"monthly"=月线
    参数 days: 获取最近多少天的数据，默认60天
    返回: 技术指标分析结果
    """
    try:
        # 获取历史K线数据（前复权）
        # adjust="qfq" 表示前复权，消除除权除息对价格的影响
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date="20200101",  # 起始日期，多取一些用于计算指标
            end_date="20261231",    # 结束日期
            adjust="qfq"
        )

        # 只取最近N天数据用于分析
        df = df.tail(days).copy()

        if df.empty:
            return f"未获取到股票 {symbol} 的历史数据"

        # 获取最新一天的数据
        latest = df.iloc[-1]
        latest_date = latest["日期"]
        latest_close = latest["收盘"]

        # ========== 1. 计算均线 MA ==========
        # MA = 最近N天收盘价的平均值
        # MA5 = 5日均线，MA10 = 10日均线，以此类推
        df["MA5"] = df["收盘"].rolling(window=5).mean()
        df["MA10"] = df["收盘"].rolling(window=10).mean()
        df["MA20"] = df["收盘"].rolling(window=20).mean()
        df["MA60"] = df["收盘"].rolling(window=60).mean()

        ma5 = df["MA5"].iloc[-1]
        ma10 = df["MA10"].iloc[-1]
        ma20 = df["MA20"].iloc[-1]
        ma60 = df["MA60"].iloc[-1] if not pd.isna(df["MA60"].iloc[-1]) else None

        # 判断均线多头/空头排列
        # 多头排列：MA5 > MA10 > MA20 > MA60（上涨趋势）
        # 空头排列：MA5 < MA10 < MA20 < MA60（下跌趋势）
        if ma5 and ma10 and ma20 and ma60:
            if ma5 > ma10 > ma20 > ma60:
                ma_trend = "多头排列（上涨趋势）"
            elif ma5 < ma10 < ma20 < ma60:
                ma_trend = "空头排列（下跌趋势）"
            else:
                ma_trend = "交叉整理（震荡趋势）️"
        else:
            ma_trend = "数据不足"

        # ========== 2. 计算 MACD ==========
        # MACD = 指数平滑异同移动平均线
        # DIF = EMA12 - EMA26（快线减慢线）
        # DEA = DIF的9日EMA（信号线）
        # MACD柱 = (DIF - DEA) * 2
        ema12 = df["收盘"].ewm(span=12, adjust=False).mean()
        ema26 = df["收盘"].ewm(span=26, adjust=False).mean()
        df["DIF"] = ema12 - ema26
        df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
        df["MACD"] = (df["DIF"] - df["DEA"]) * 2

        dif = df["DIF"].iloc[-1]
        dea = df["DEA"].iloc[-1]
        macd = df["MACD"].iloc[-1]

        # MACD 金叉/死叉判断
        # 金叉：DIF 从下向上穿越 DEA（买入信号）
        # 死叉：DIF 从上向下穿越 DEA（卖出信号）
        if len(df) >= 2:
            prev_dif = df["DIF"].iloc[-2]
            prev_dea = df["DEA"].iloc[-2]
            if prev_dif <= prev_dea and dif > dea:
                macd_signal = "金叉（买入信号）"
            elif prev_dif >= prev_dea and dif < dea:
                macd_signal = "死叉（卖出信号）"
            elif dif > dea:
                macd_signal = "DIF在DEA上方（多头）"
            else:
                macd_signal = "DIF在DEA下方（空头）"
        else:
            macd_signal = "数据不足"

        # ========== 3. 计算 KDJ ==========
        # KDJ = 随机指标，用于判断超买超卖
        # RSV = (收盘价 - N日最低价) / (N日最高价 - N日最低价) * 100
        # K = RSV的3日移动平均
        # D = K的3日移动平均
        # J = 3K - 2D
        low_list = df["最低"].rolling(window=9, min_periods=9).min()
        high_list = df["最高"].rolling(window=9, min_periods=9).max()
        rsv = (df["收盘"] - low_list) / (high_list - low_list) * 100

        # 计算K、D、J值
        k_values = []
        d_values = []
        j_values = []

        # 初始化第一个K、D值
        prev_k = 50
        prev_d = 50

        for rsv_val in rsv:
            if pd.isna(rsv_val):
                k_values.append(prev_k)
                d_values.append(prev_d)
                j_values.append(3 * prev_k - 2 * prev_d)
            else:
                # K = 2/3 * 前一日K + 1/3 * 当日RSV
                k = 2/3 * prev_k + 1/3 * rsv_val
                # D = 2/3 * 前一日D + 1/3 * 当日K
                d = 2/3 * prev_d + 1/3 * k
                # J = 3K - 2D
                j = 3 * k - 2 * d

                k_values.append(k)
                d_values.append(d)
                j_values.append(j)

                prev_k = k
                prev_d = d

        df["K"] = k_values
        df["D"] = d_values
        df["J"] = j_values

        k_val = df["K"].iloc[-1]
        d_val = df["D"].iloc[-1]
        j_val = df["J"].iloc[-1]

        # KDJ 超买超卖判断
        # J > 100：超买区（可能回调）
        # J < 0：超卖区（可能反弹）
        if j_val > 100:
            kdj_signal = "超买区（注意回调风险）"
        elif j_val < 0:
            kdj_signal = "超卖区（可能反弹）"
        elif k_val > d_val:
            kdj_signal = "K在D上方（偏多）"
        else:
            kdj_signal = "K在D下方（偏空）"

        # ========== 4. 计算 RSI ==========
        # RSI = 相对强弱指标，衡量涨跌力度
        # RSI = 100 - 100 / (1 + RS)
        # RS = N日平均涨幅 / N日平均跌幅
        def calc_rsi(series, period):
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))

        df["RSI6"] = calc_rsi(df["收盘"], 6)
        df["RSI12"] = calc_rsi(df["收盘"], 12)
        df["RSI24"] = calc_rsi(df["收盘"], 24)

        rsi6 = df["RSI6"].iloc[-1]
        rsi12 = df["RSI12"].iloc[-1]
        rsi24 = df["RSI24"].iloc[-1]

        # RSI 超买超卖判断
        # RSI > 80：超买
        # RSI < 20：超卖
        if rsi6 > 80:
            rsi_signal = "超买（短期可能回调）"
        elif rsi6 < 20:
            rsi_signal = "超卖（短期可能反弹）"
        else:
            rsi_signal = "正常区间"

        # ========== 组装返回结果 ==========
        result = f"股票 {symbol} 技术指标分析（{latest_date}）\n\n"
        result += f"最新收盘价：{latest_close} 元\n\n"

        result += "【均线系统 MA】\n"
        result += f"  MA5（5日均线）：{ma5:.2f}\n"
        result += f"  MA10（10日均线）：{ma10:.2f}\n"
        result += f"  MA20（20日均线）：{ma20:.2f}\n"
        if ma60:
            result += f"  MA60（60日均线）：{ma60:.2f}\n"
        result += f"  趋势判断：{ma_trend}\n\n"

        result += "【MACD 指标】\n"
        result += f"  DIF（快线）：{dif:.4f}\n"
        result += f"  DEA（慢线）：{dea:.4f}\n"
        result += f"  MACD柱：{macd:.4f}\n"
        result += f"  信号判断：{macd_signal}\n\n"

        result += "【KDJ 随机指标】\n"
        result += f"  K值：{k_val:.2f}\n"
        result += f"  D值：{d_val:.2f}\n"
        result += f"  J值：{j_val:.2f}\n"
        result += f"  信号判断：{kdj_signal}\n\n"

        result += "【RSI 相对强弱】\n"
        result += f"  RSI6（6日）：{rsi6:.2f}\n"
        result += f"  RSI12（12日）：{rsi12:.2f}\n"
        result += f"  RSI24（24日）：{rsi24:.2f}\n"
        result += f"  信号判断：{rsi_signal}\n\n"

        result += "提示：技术指标仅供参考，不构成投资建议"

        return result

    except Exception as e:
        return f"获取技术指标失败：{str(e)}\n{traceback.format_exc()}"
