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
    TRIMA(三角移动平均线)相比于其它移动平均线能够更快地对价格变化作出反应，TRIMA产生的线条比其它移动平均线产生的线条更平滑、更像波浪。

    TRIMA策略常规用法：
    1、短期三角移动平均线金叉长期三角移动平均线，开多，如有空单，先平空再开多
    2、短期三角移动平均线死叉长期三角移动平均线，开空，如有多单，先平多再开空

    注：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.fast_period = 10
    context.slow_period = 30
    """

    # 添加参数
    context.fast_period = add_parameter(int, 'fast_period', '短期三角移动平均线周期')
    context.slow_period = add_parameter(int, 'slow_period', '长期三角移动平均线周期')

    # 添加因子
    context.Fast = add_factor(float, 'Fast', '短期三角移动平均线')
    context.Slow = add_factor(float, 'Slow', '长期三角移动平均线')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    if context.need_bar_number is None:
        context.need_bar_number = context.slow_period + 10

    # 获取计算指标所需数据
    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.need_bar_number,
                          fields=['close'])
    need_close = np.array(need_data['close'])

    # 获取到所需数据才进行指标计算和发单操作
    if (len(need_close) == context.need_bar_number) and (sum(np.isnan(need_close)) == 0):
        on_bar_fast = talib.TRIMA(need_close, timeperiod=context.fast_period)
        on_bar_slow = talib.TRIMA(need_close, timeperiod=context.slow_period)

        if (not pd.isna(on_bar_fast[-1])) and (not pd.isna(on_bar_slow[-1])):
            # 保存因子值
            context.Fast = on_bar_fast[-1]
            context.Slow = on_bar_slow[-1]

            if (not pd.isna(on_bar_fast[-2])) and (not pd.isna(on_bar_slow[-2])):
                # 均线下穿，做空
                if (on_bar_slow[-2] <= on_bar_fast[-2]) and (on_bar_slow[-1] > on_bar_fast[-1]):
                    if context.all_holding >= 0:  # 如果有多仓, 先平多, 再开空；否则直接开空
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume + context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.SELL,
                                   strategy_group='A')
                        context.all_holding = (-context.trade_volume)

                # 均线上穿，做多
                if (on_bar_fast[-2] <= on_bar_slow[-2]) and (on_bar_fast[-1] > on_bar_slow[-1]):
                    if context.all_holding <= 0:  # 如果有空仓，先平空，再开多；否则直接开多
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume - context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.BUY,
                                   strategy_group='A')
                        context.all_holding = context.trade_volume


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass