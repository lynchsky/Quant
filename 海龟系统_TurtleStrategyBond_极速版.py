# -*- coding:UTF-8 -*-
import numpy as np
import pandas as pd

from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      1min    X-BondT+1        是         原始       cs1


def init(context):
    """
    海龟策略是比较经典的趋势跟踪策略，具体思路如下：当价格突破一定周期内的最高价或最低价，为开仓信号；在持仓状态下，当价格反向突破一定周期内的最高价或
    最低价，为平仓信号。

    海龟策略常规用法：
    1、价格突破开仓周期最高价，开多，如有空单，先平空再开多
    2、价格跌破平仓周期最低价，如有多单，平多
    3、价格跌破开仓周期最低价，开空，如有多单，先平多再开空
    4、价格突破平仓周期最高价，如有空单，平空

    注：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.open_period = 20
    context.close_period = 10
    """

    # 添加参数
    context.open_period = add_parameter(int, 'open_period', '海龟策略开仓周期')
    context.close_period = add_parameter(int, 'close_period', '海龟策略平仓周期')

    # 添加因子
    context.OPEN_BUY_LINE = add_factor(float, 'OPEN_BUY_LINE', 'OPEN_BUY_LINE指标')
    context.CLOSE_BUY_LINE = add_factor(float, 'CLOSE_BUY_LINE', 'CLOSE_BUY_LINE指标')
    context.OPEN_SELL_LINE = add_factor(float, 'OPEN_SELL_LINE', 'OPEN_SELL_LINE指标')
    context.CLOSE_SELL_LINE = add_factor(float, 'CLOSE_SELL_LINE', 'CLOSE_SELL_LINE指标')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    # 获取计算指标所需数据
    if context.need_bar_number is None:
        context.need_bar_number = max(context.open_period, context.close_period) + 1

    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.need_bar_number,
                          fields=['high', 'low', 'close'])
    need_data = {k: np.array(need_data[k]) for k in need_data}

    need_high = need_data['high']
    need_low = need_data['low']
    need_close = need_data['close']

    # 获取到所需数据才进行指标计算和发单操作
    if len(need_close) == context.need_bar_number:
        open_buy_line = np.nanmax(need_high[-context.open_period - 1: -1])
        close_buy_line = np.nanmin(need_low[-context.close_period - 1: -1])
        open_sell_line = np.nanmin(need_low[-context.open_period - 1: -1])
        close_sell_line = np.nanmax(need_high[-context.close_period - 1: -1])

        # 保存因子值
        if not pd.isna(open_buy_line):
            context.OPEN_BUY_LINE = open_buy_line

        if not pd.isna(close_buy_line):
            context.CLOSE_BUY_LINE = close_buy_line

        if not pd.isna(open_sell_line):
            context.OPEN_SELL_LINE = open_sell_line

        if not pd.isna(close_sell_line):
            context.CLOSE_SELL_LINE = close_sell_line

        if not pd.isna(need_close[-1]):
            if (need_close[-1] > open_buy_line) and (context.all_holding <= 0):
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=context.trade_volume - context.all_holding,
                           price=bar.close,
                           order_type=OrderType.LIMIT,
                           side=OrderSide.BUY,
                           strategy_group='A')
                context.all_holding = context.trade_volume

            if (need_close[-1] < close_buy_line) and (context.all_holding > 0):
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=context.all_holding,
                           price=bar.close,
                           order_type=OrderType.LIMIT,
                           side=OrderSide.SELL,
                           strategy_group='A')
                context.all_holding = 0

            if (need_close[-1] < open_sell_line) and (context.all_holding >= 0):
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=context.trade_volume + context.all_holding,
                           price=bar.close,
                           order_type=OrderType.LIMIT,
                           side=OrderSide.SELL,
                           strategy_group='A')
                context.all_holding = (-context.trade_volume)

            if (need_close[-1] > close_sell_line) and (context.all_holding < 0):
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