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
    MACD(指数平滑异同平均线)是最经典的技术指标，其优点是除掉了均线系统产生的频繁出现的买入、卖出信号，使发出信号的要求和限制增加，避免假信号的出现，
    用起来比均线系统更有把握。

    MACD策略常规用法：
    1、零轴之上MACD金叉，开多，如有空单，先平空再开多
    2、MACD死叉，如有多单，平多
    3、零轴之下MACD死叉，开空，如有多单，先平多再开空
    4、MACD金叉，如有空单，平空

    注1：零轴之上代表多头趋势，零轴之下代表空头趋势，只在多头趋势开多，只在空头趋势开空，但无论是多头趋势还是空头趋势，只要出现与持仓反向的信号即平仓。
    注2：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.short_period = 12
    context.long_period = 26
    context.macd_period = 9
    context.macd_period = 9
    """

    # 添加参数
    context.short_period = add_parameter(int, 'short_period', 'MACD快速参数')
    context.long_period = add_parameter(int, 'long_period', 'MACD慢速参数')
    context.macd_period = add_parameter(int, 'macd_period', 'MACD平滑参数')

    # 添加因子
    context.DIFF = add_factor(float, 'DIFF', 'DIFF指标')
    context.DEA = add_factor(float, 'DEA', 'DEA指标')
    context.MACD = add_factor(float, 'MACD', 'MACD指标')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    if context.need_bar_number is None:
        context.need_bar_number = context.long_period + context.macd_period + 10

    # 获取计算指标所需数据
    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.need_bar_number,
                          fields=['close'])
    # need_close = format_data(need_data['close'])
    need_close = np.array(need_data['close'])

    # 获取到所需数据才进行指标计算和发单操作
    if (len(need_close) == context.need_bar_number) and (sum(np.isnan(need_close)) == 0):
        on_bar_diff, on_bar_dea, on_bar_macd = talib.MACD(need_close,
                                                          fastperiod=context.short_period,
                                                          slowperiod=context.long_period,
                                                          signalperiod=context.macd_period)

        if not pd.isna(on_bar_macd[-1]):
            # 保存因子值
            context.DIFF = on_bar_diff[-1]
            context.DEA = on_bar_dea[-1]
            context.MACD = on_bar_macd[-1]

            if not pd.isna(on_bar_macd[-2]):
                # 零轴之上MACD金叉，开多，如有空单，先平空再开多
                if (on_bar_diff[-2] <= on_bar_dea[-2]) and (on_bar_diff[-1] > on_bar_dea[-1]) and (
                        on_bar_diff[-2] > 0) and (on_bar_dea[-1] > 0):
                    if context.all_holding <= 0:
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume - context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.BUY,
                                   strategy_group='A')
                        context.all_holding = context.trade_volume

                # MACD死叉，如有多单，平多
                if (on_bar_diff[-2] >= on_bar_dea[-2]) and (on_bar_diff[-1] < on_bar_dea[-1]) and (
                        context.all_holding > 0):
                    send_order(platform_code=context.cs1.platform,
                               security_id=context.cs1.symbol,
                               volume=context.all_holding,
                               price=bar.close,
                               order_type=OrderType.LIMIT,
                               side=OrderSide.SELL,
                               strategy_group='A')
                    context.all_holding = 0

                # 零轴之下MACD死叉，开空，如有多单，先平多再开空
                if (on_bar_diff[-2] >= on_bar_dea[-2]) and (on_bar_diff[-1] < on_bar_dea[-1]) and (
                        on_bar_diff[-2] < 0) and (on_bar_dea[-1] < 0):
                    if context.all_holding >= 0:
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume + context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.SELL,
                                   strategy_group='A')
                        context.all_holding = (-context.trade_volume)

                # MACD金叉，如有空单，平空
                if (on_bar_diff[-2] <= on_bar_dea[-2]) and (on_bar_diff[-1] > on_bar_dea[-1]) and (
                        context.all_holding < 0):
                    send_order(platform_code=context.cs1.platform,
                               security_id=context.cs1.symbol,
                               volume=(-context.all_holding),
                               price=bar.close,
                               order_type=OrderType.LIMIT,
                               side=OrderSide.BUY,
                               strategy_group='A')
                    context.all_holding = 0


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass