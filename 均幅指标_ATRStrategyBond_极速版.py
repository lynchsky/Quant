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
    ATR代表价格波动区间的大小，当较小周期的ATR大于较大周期的ATR的一定倍数时，代表价格波动加大，预示着有较大行情出现，当较小周期的ATR小于较大周期的
    ATR的一定倍数时，代表着价格进入盘整状态，为清仓信号。

    ATR策略常规用法（以下用法中的数字作为参数，可自行调节）：
    1、10周期ATR大于20周期ATR的1.25倍：如果当前收盘价高于上一根收盘价加上2倍的10周期ATR，开多，如有空单，先平空再开多
                                   如果当前收盘价低于上一根收盘价减去2倍的10周期ATR，开空，如有多单，先平多再开空
    2、10周期ATR小于20周期ATR的0.75倍，清仓

    注：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.short_period = 10
    context.long_period = 20
    context.expand_multiple = 1.25
    context.shrink_multiple = 0.75
    context.open_multiple = 2
    """

    # 添加参数
    context.short_period = add_parameter(int, 'short_period', '较小周期的ATR参数')
    context.long_period = add_parameter(int, 'long_period', '较大周期的ATR参数')
    context.expand_multiple = add_parameter(float, 'expand_multiple', '预示走势波动加大的倍数')
    context.shrink_multiple = add_parameter(float, 'shrink_multiple', '预示走势波动缩小的倍数')
    context.open_multiple = add_parameter(float, 'open_multiple', '判断开仓信号的倍数')

    # 添加因子
    context.ATRShort = add_factor(float, 'ATRShort', '短周期ATR指标')
    context.ATRLong = add_factor(float, 'ATRLong', '长周期ATR指标')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    if context.need_bar_number is None:
        context.need_bar_number = context.long_period + 10

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
        on_bar_atr_short = talib.ATR(need_high, need_low, need_close, timeperiod=context.short_period)[-1]
        on_bar_atr_long = talib.ATR(need_high, need_low, need_close, timeperiod=context.long_period)[-1]

        if (not pd.isna(on_bar_atr_short)) and (not pd.isna(on_bar_atr_long)):
            # 保存因子值
            context.ATRShort = on_bar_atr_short
            context.ATRLong = on_bar_atr_long

            if (not pd.isna(need_close[-2])) and (not pd.isna(need_close[-1])):
                if on_bar_atr_short >= (on_bar_atr_long * context.expand_multiple):
                    if need_close[-1] >= (need_close[-2] + on_bar_atr_short * context.open_multiple):
                        if context.all_holding <= 0:
                            send_order(platform_code=context.cs1.platform,
                                       security_id=context.cs1.symbol,
                                       volume=context.trade_volume - context.all_holding,
                                       price=bar.close,
                                       order_type=OrderType.LIMIT,
                                       side=OrderSide.BUY,
                                       strategy_group='A')
                            context.all_holding = context.trade_volume

                    if need_close[-1] <= (need_close[-2] - on_bar_atr_short * context.open_multiple):
                        if context.all_holding >= 0:
                            send_order(platform_code=context.cs1.platform,
                                       security_id=context.cs1.symbol,
                                       volume=context.trade_volume + context.all_holding,
                                       price=bar.close,
                                       order_type=OrderType.LIMIT,
                                       side=OrderSide.SELL,
                                       strategy_group='A')
                            context.all_holding = (-context.trade_volume)

                if on_bar_atr_short <= (on_bar_atr_long * context.shrink_multiple):
                    if context.all_holding < 0:
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=(-context.all_holding),
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.BUY,
                                   strategy_group='A')
                        context.all_holding = 0

                    if context.all_holding > 0:
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.SELL,
                                   strategy_group='A')
                        context.all_holding = 0


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass