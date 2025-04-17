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
    DMI指标是通过分析价格在涨跌过程中买卖双方力量均衡点的变化情况，即多空双方的力量的变化受价格波动的影响而发生由均衡到失衡的循环过程，从而提供对趋势
    判断依据的一种技术指标。

    DMI策略常规用法：
    1、PDI金叉MDI且ADX上升，开多，如有空单，先平空再开多
    2、PDI死叉MDI，如有多单，平多
    3、PDI死叉MDI且ADX下降，开空，如有多单，先平多再开空
    4、PDI金叉MDI，如有空单，平空

    注1：本策略未用到ADXR线，故未计算。
    注2：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.period = 20
    """

    # 添加参数
    context.period = add_parameter(int, 'period', 'DMI指标计算周期')

    # 添加因子
    context.PDI = add_factor(float, 'PDI', 'PDI指标')
    context.MDI = add_factor(float, 'MDI', 'MDI指标')
    context.ADX = add_factor(float, 'ADX', 'ADX指标')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    if context.need_bar_number is None:
        context.need_bar_number = context.period * 2 + 10

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
        on_bar_pdi = talib.PLUS_DI(need_high, need_low, need_close, timeperiod=context.period)
        on_bar_mdi = talib.MINUS_DI(need_high, need_low, need_close, timeperiod=context.period)
        on_bar_adx = talib.ADX(need_high, need_low, need_close, timeperiod=context.period)

        if not pd.isna(on_bar_adx[-1]):
            # 保存因子值
            context.PDI = on_bar_pdi[-1]
            context.MDI = on_bar_mdi[-1]
            context.ADX = on_bar_adx[-1]

            if not pd.isna(on_bar_adx[-2]):
                # PDI金叉MDI
                if (on_bar_pdi[-2] <= on_bar_mdi[-2]) and (on_bar_pdi[-1] > on_bar_mdi[-1]) and (
                        context.all_holding <= 0):
                    if on_bar_adx[-1] > on_bar_adx[-2]:  # 如果ADX向上，开多，如果有空单，先平空再开多
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume - context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.BUY,
                                   strategy_group='A')
                        context.all_holding = context.trade_volume
                    else:  # 如果ADX不向上，即非多头市场，如果有空单，只平空
                        if context.all_holding < 0:
                            send_order(platform_code=context.cs1.platform,
                                       security_id=context.cs1.symbol,
                                       volume=(-context.all_holding),
                                       price=bar.close,
                                       order_type=OrderType.LIMIT,
                                       side=OrderSide.BUY,
                                       strategy_group='A')
                            context.all_holding = 0

                # PDI死叉MDI
                if (on_bar_pdi[-2] >= on_bar_mdi[-2]) and (on_bar_pdi[-1] < on_bar_mdi[-1]) and (
                        context.all_holding >= 0):
                    if on_bar_adx[-1] < on_bar_adx[-2]:  # 如果ADX向下，开空，如果有多单，先平多再开空
                        send_order(platform_code=context.cs1.platform,
                                   security_id=context.cs1.symbol,
                                   volume=context.trade_volume + context.all_holding,
                                   price=bar.close,
                                   order_type=OrderType.LIMIT,
                                   side=OrderSide.SELL,
                                   strategy_group='A')
                        context.all_holding = (-context.trade_volume)
                    else:  # 如果ADX不向下，即非空头市场，如果有多单，只平多
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