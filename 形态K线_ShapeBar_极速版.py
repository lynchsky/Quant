# -*- coding:UTF-8 -*-
from ComstarApi import *
import numpy as np

# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      5min    X-BondT+1        是         原始       cs1


def init(context):
    # 时间: 2020-09-01 ~ 2020-09-30

    # shape_len :     20
    # =======add parameter======================================================================
    context.shape_len = add_parameter(int, 'shape_len', 'shape_len')

    # =======add factor=========================================================================
    context.volumed = add_factor(float, 'volumed', '累计报价量')

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.bar_open = []
    context.bar_close = []
    context.temp_volumed = 0


def on_bar(context, bar):
    shape_len = int(context.shape_len)

    a_n = get_bar_n(cic_code=context.cs1.cic_code,
                    interval=context.cs1.interval,
                    count=shape_len,
                    fields=['open', 'high', 'low', 'close'])
    # a_n = {k: format_data(a_n[k]) for k in a_n}
    a_n = {k: np.array(a_n[k]) for k in a_n}

    if not a_n:
        return
    # write_log('a_n:{}'.format(a_n))

    if context.all_holding == 0:
        volume = 10000000
    else:
        volume = 20000000

    if a_n['close'][-2] >= a_n['open'][-2] and a_n['close'][-1] >= a_n['open'][-1]:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=volume,
                   price=bar.close,
                   order_type=OrderType.LIMIT,
                   side=OrderSide.BUY,
                   strategy_group='A')
        context.temp_volumed += volume
        context.volumed = context.temp_volumed

    if a_n['close'][-2] <= a_n['open'][-2] and a_n['close'][-1] <= a_n['open'][-1]:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=volume,
                   price=bar.close,
                   order_type=OrderType.LIMIT,
                   side=OrderSide.SELL,
                   strategy_group='A')
        context.temp_volumed += volume
        context.volumed = context.temp_volumed


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass