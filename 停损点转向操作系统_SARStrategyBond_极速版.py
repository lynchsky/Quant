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
    SAR(抛物线指标)也称为停损点转向指标，属于价格与时间并重的指标类型。SAR指标计算较为复杂，但在具体使用时可将其视为一条特殊的趋势线，买卖信号的生成
    与单均线基本一致。

    SAR策略常规用法：
    1、价格从SAR曲线下方向上突破SAR曲线时，开多，如有空单，先平空再开多
    2、价格从SAR曲线上方向下跌破SAR曲线时，开空，如有多单，先平多再开空

    注：本策略为本币CTA趋势跟踪策略，适用于Bar数据，暂不适用于Tick数据。

    本策略默认参数如下：
    回测区间：2020-09-01 - 2020-09-30

    context.af_step = 0.02
    context.max_af = 0.2
    """

    # 添加参数
    context.af_step = add_parameter(float, 'af_step', '加速因子步长')
    context.max_af = add_parameter(float, 'max_af', '加速因子最大值')

    # 添加因子
    context.SAR = add_factor(float, 'SAR', 'SAR指标')

    context.all_holding = 0  # 保存持仓数量
    context.trade_volume = 10000000  # 开仓数量
    context.need_bar_number = 50  # 保存需要获取的K线根数的变量


def on_bar(context, bar):
    # 获取计算指标所需数据
    need_data = get_bar_n(cic_code=context.cs1.cic_code,
                          interval=context.cs1.interval,
                          count=context.need_bar_number,
                          fields=['high', 'low', 'close'])
    # need_data = {k: format_data(need_data[k]) for k in need_data}
    need_data = {k:np.array(need_data[k]) for k in need_data}

    need_high = np.array(need_data['high'])
    need_low = np.array(need_data['low'])
    need_close = np.array(need_data['close'])

    # 获取到所需数据才进行指标计算和发单操作
    if (len(need_close) == context.need_bar_number) and (sum(np.isnan(need_close)) == 0):
        on_bar_sar = talib.SAR(need_high, need_low, acceleration=context.af_step, maximum=context.max_af)

        if not pd.isna(on_bar_sar[-1]):
            # 保存因子值
            context.SAR = on_bar_sar[-1]

            if (not pd.isna(on_bar_sar[-2])) and (not pd.isna(need_close[-2])) and (not pd.isna(need_close[-1])):
                # 价格从SAR曲线下方向上突破SAR曲线时，开多，如有空单，先平空再开多
                if (need_close[-2] <= on_bar_sar[-2]) and (need_close[-1] > on_bar_sar[-1]) and (
                        context.all_holding <= 0):
                    send_order(platform_code=context.cs1.platform,
                               security_id=context.cs1.symbol,
                               volume=context.trade_volume - context.all_holding,
                               price=bar.close,
                               order_type=OrderType.LIMIT,
                               side=OrderSide.BUY,
                               strategy_group='A')
                    context.all_holding = context.trade_volume

                # 价格从SAR曲线上方向下跌破SAR曲线时，开空，如有多单，先平多再开空
                if (need_close[-2] >= on_bar_sar[-2]) and (need_close[-1] < on_bar_sar[-1]) and (
                        context.all_holding >= 0):
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