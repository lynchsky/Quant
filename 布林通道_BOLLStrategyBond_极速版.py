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
    BOLL通道是具有统计学意义的技术指标，根据统计学原理，价格在95%的情况下应出现在一定周期均线加减两倍标准差的价格范围之内，因此当价格突破上下轨后又
    重新回到上下轨之内，可视为平仓信号；布林中轨代表趋势方向，价格突破中轨，为多头趋势，可视为买入信号，价格跌破中轨，为空头趋势，可视为卖出信号。

    BOLL通道策略常规用法：
    1、价格突破布林中轨，开多，如有空单，先平空再开多
    2、价格突破布林上轨后又跌破上轨，如有多单，平多
    3、价格跌破布林中轨，开空，如有多单，先平多再开空
    4、价格跌破布林下轨后又突破下轨，如有空单，平空

    注1：之所以不在突破上下轨时平仓，是由于强烈的趋势行情往往沿着上轨或下轨运行。
    注2：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.period = 26
    context.multiple = 2
    """

    # 添加参数
    context.period = add_parameter(int, 'period', '布林通道计算周期')
    context.multiple = add_parameter(float, 'multiple', '布林通道标准差倍数')

    # 添加因子
    context.Middle = add_factor(float, 'Middle', '布林中轨')
    context.Upper = add_factor(float, 'Upper', '布林上轨')
    context.Lower = add_factor(float, 'Lower', '布林下轨')

    context.all_holding = 0  # 持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = None  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    if context.need_bar_number is None:
        context.need_bar_number = context.period +10

    # 获取计算指标所需数据
    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.need_bar_number,
                          fields=['close'])
    need_close = np.array(need_data['close'])

    # 获取到所需数据才进行指标计算和发单操作
    if (len(need_close) == context.need_bar_number) and (sum(np.isnan(need_close)) == 0):
        upper, middle, lower = talib.BBANDS(need_close, timeperiod=context.period, nbdevup=context.multiple,
                                            nbdevdn=context.multiple, matype=0)

        if not pd.isna(middle[-1]):
            # 保存因子值
            context.Middle = middle[-1]
            context.Upper = upper[-1]
            context.Lower = lower[-1]

            if (not pd.isna(middle[-2])) and (not pd.isna(need_close[-2])) and (not pd.isna(need_close[-1])):
                # 价格跌破布林中轨，开空，如有多单，先平多再开空
                if (context.all_holding >= 0) and (need_close[-2] >= middle[-2]) and (need_close[-1] < middle[-1]):
                    send_order(platform_code=context.cs1.platform,
                               security_id=context.cs1.symbol,
                               volume=context.trade_volume + context.all_holding,
                               price=bar.close,
                               order_type=OrderType.LIMIT,
                               side=OrderSide.SELL,
                               strategy_group='A')
                    context.all_holding = (-context.trade_volume)

                # 价格突破布林上轨后又跌破上轨，如有多单，平多
                if (context.all_holding > 0) and (need_close[-2] >= upper[-2]) and (need_close[-1] < upper[-1]):
                    send_order(platform_code=context.cs1.platform,
                               security_id=context.cs1.symbol,
                               volume=context.all_holding,
                               price=bar.close,
                               order_type=OrderType.LIMIT,
                               side=OrderSide.SELL,
                               strategy_group='A')
                    context.all_holding = 0

                # 价格突破布林中轨，开多，如有空单，先平空再开多
                if (context.all_holding <= 0) and (need_close[-2] <= middle[-2]) and (need_close[-1] > middle[-1]):
                    send_order(platform_code=context.cs1.platform,
                               security_id=context.cs1.symbol,
                               volume=context.trade_volume - context.all_holding,
                               price=bar.close,
                               order_type=OrderType.LIMIT,
                               side=OrderSide.BUY,
                               strategy_group='A')
                    context.all_holding = context.trade_volume

                # 价格跌破布林下轨后又突破下轨，如有空单，平空
                if (context.all_holding < 0) and (need_close[-2] <= lower[-2]) and (need_close[-1] > lower[-1]):
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