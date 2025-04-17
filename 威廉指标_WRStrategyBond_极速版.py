# -*- coding:UTF-8 -*-
import numpy as np
import pandas as pd

from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      1min    X-BondT+1        是         原始       cs1


def init(context):
    """
    WR(威廉指标)是一个振荡类指标，是依价格的摆动点来度量行情是否处于超买或超卖的现象。当价格进入超买区间时，反向开空；当价格进入超卖区间时，反向开多。

    WR策略常规用法：
    1、WR值高于80时，开多，如有空单，先平空再开多
    2、WR值低于20时，开空，如有多单，先平多再开空

    注：本策略为本币CTA趋势反转策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.period = 14
    """

    # 添加参数
    context.period = add_parameter(int, 'period', 'WR指标计算周期')

    # 添加因子
    context.WR = add_factor(float, 'WR', 'WR指标')

    context.wr_list = []  # 保存WR指标的列表
    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量


def on_bar(context, bar):
    # 获取计算指标所需数据
    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.period,
                          fields=['high', 'low', 'close'])
    need_data = {k: np.array(need_data[k]) for k in need_data}

    need_high = need_data['high']
    need_low = need_data['low']
    need_close = need_data['close']

    # 获取到所需数据才进行指标计算和发单操作
    if (len(need_high) == context.period) and (not pd.isna(need_close[-1])):
        max_high = np.nanmax(need_high)
        min_low = np.nanmin(need_low)

        if (max_high - min_low) > 0.000000001:  # 被除数非零判断
            on_bar_wr = (max_high - need_close[-1]) / (max_high - min_low) * 100
        else:
            on_bar_wr = 50.0  # 如果计算周期内的最高价等于最低价，即价格无波动，设置指标值为50.0

        # 保存计算的指标
        context.wr_list.append(on_bar_wr)

        # 保存因子值
        if not pd.isna(on_bar_wr):
            context.WR = on_bar_wr

        if (len(context.wr_list) >= 2) and (not pd.isna(context.wr_list[-2])) and (not pd.isna(context.wr_list[-1])):
            # WR值跌破20时，开空，如有多单，先平多再开空
            if (context.wr_list[-2] >= 20) and (context.wr_list[-1] < 20) and (context.all_holding >= 0):
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=context.trade_volume + context.all_holding,
                           price=bar.close,
                           order_type=OrderType.LIMIT,
                           side=OrderSide.SELL,
                           strategy_group='A')
                context.all_holding = (-context.trade_volume)

            # WR值高于80时，开多，如有空单，先平空再开多
            if (context.wr_list[-2] <= 80) and (context.wr_list[-1] > 80) and (context.all_holding <= 0):
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