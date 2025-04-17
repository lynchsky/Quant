# -*- coding:UTF-8 -*-
import numpy as np
from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      5min    X-BondT+1        是         原始       cs1


def init(context):
    # 时间: 2020-09-01 ~ 2020-09-30

    # boll_len   :     20
    # std_ratio  :      2
    # =======add parameter======================================================================
    context.boll_len = add_parameter(int, 'boll_len', 'boll_len')
    context.std_ratio = add_parameter(float, 'std_ratio', 'std_ratio')
    # ==========================================================================================

    # =======add factor=========================================================================
    context.show_up_band = add_factor(float, 'show_up_band', 'up_band')
    context.show_down_band = add_factor(float, 'show_down_band', 'down_band')
    context.show_bar_close = add_factor(float, 'show_bar_close', 'bar_close')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.up_band = []
    context.down_band = []
    context.bar_close = []
    # ==============================================


def on_bar(context, bar):
    boll_len = int(context.boll_len)
    std_ratio = float(context.std_ratio)

    # =============================================================================
    a_n = get_bar_n(cic_code=context.cs1.cic_code,
                    interval=context.cs1.interval,
                    count=boll_len,
                    fields=['open', 'high', 'low', 'close'])
    a_n = {k: np.array(a_n[k]) for k in a_n}

    if not a_n:
        return
    # =============================================================================

    on_bar_mean = np.nanmean(a_n['close'])
    on_bar_std = np.nanstd(a_n['close'])

    on_bar_up_band = on_bar_mean + std_ratio * on_bar_std
    on_bar_down_band = on_bar_mean - std_ratio * on_bar_std

    # ==============append list=================
    context.up_band.append(on_bar_up_band)
    context.down_band.append(on_bar_down_band)
    context.bar_close.append(bar.close)
    # ==============append list=================

    # ==============for chart=========================
    context.show_up_band = on_bar_up_band
    context.show_down_band = on_bar_down_band
    context.show_bar_close = bar.close
    # ==============for chart=========================

    if context.all_holding == 0:
        order_volume = 10000000
    else:
        order_volume = 20000000

    if len(context.up_band) > 3 and len(context.down_band) > 3 and context.bar_close[-2] < \
            context.up_band[-2] and context.bar_close[-1] >= context.up_band[-1]:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=order_volume,
                   price=bar.close,
                   order_type=OrderType.LIMIT,
                   side=OrderSide.SELL,
                   strategy_group='A')

    if len(context.up_band) > 3 and len(context.down_band) > 3 and context.bar_close[-2] > \
            context.down_band[-2] and context.bar_close[-1] <= context.down_band[-1]:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=order_volume,
                   price=bar.close,
                   order_type=OrderType.LIMIT,
                   side=OrderSide.BUY,
                   strategy_group='A')


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass