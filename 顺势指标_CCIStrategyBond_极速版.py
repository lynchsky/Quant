# -*- coding:UTF-8 -*-
import numpy as np
import pandas as pd
import talib

from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      1min    X-BondT+1        是         原始       cs1


def init(context):
    """
    CCI指标是根据统计学原理，引进价格与固定期间的平均价格的偏离程度的概念，强调价格平均绝对偏差在技术分析中的重要性，是一种比较独特的技术指标。
    CCI指标的一般用法是，价格向上突破-100时，为开多信号，向上突破100时，为加多信号，价格向下跌破100时，为开空信号，向下跌破-100时，为加空信号。

    CCI策略常规用法（本策略不考虑加仓，将加仓信号视为开仓信号）：
    1、CCI值向上突破-100、100时，开多，如有空单，先平空再开多
    2、CCI值向下跌破100、-100时，开空，如有多单，先平多再开空

    注：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.period = 14
    """

    # 添加参数
    context.period = add_parameter(int, 'period', 'CCI指标计算周期')

    # 添加因子
    context.CCI = add_factor(float, 'CCI', 'CCI指标')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    if context.need_bar_number is None:
        context.need_bar_number = context.period + 10

    # 获取计算指标所需数据
    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.need_bar_number,
                          fields=['high', 'low', 'close'])
    need_data = {k: np.array(need_data[k]) for k in need_data}

    need_high = np.array(need_data['high'])
    need_low = np.array(need_data['low'])
    need_close = np.array(need_data['close'])

    # 获取到所需数据才进行指标计算和发单操作
    if (len(need_close) == context.need_bar_number) and (sum(np.isnan(need_close)) == 0):
        on_bar_cci = talib.CCI(need_high, need_low, need_close, timeperiod=context.period)

        if not pd.isna(on_bar_cci[-1]):
            # 保存因子值
            context.CCI = on_bar_cci[-1]

            if not pd.isna(on_bar_cci[-2]):
                # 出现开多信号
                if ((on_bar_cci[-2] <= -100) and (on_bar_cci[-1] > -100)) or (
                        (on_bar_cci[-2] <= 100) and (on_bar_cci[-1] > 100)):
                    # 如果有空单，先平空再开多，否则直接开多
                    if context.all_holding <= 0:
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume - context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.BUY,
                                   strategy_group='A')
                        context.all_holding = context.trade_volume

                # 出现开空信号
                if ((on_bar_cci[-2] >= 100) and (on_bar_cci[-1] < 100)) or (
                        (on_bar_cci[-2] >= -100) and (on_bar_cci[-1] < -100)):
                    # 如果有多单，先平多再开空，否则直接开空
                    if context.all_holding >= 0:
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume + context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.SELL,
                                   strategy_group='A')
                        context.all_holding = (-context.trade_volume)


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass