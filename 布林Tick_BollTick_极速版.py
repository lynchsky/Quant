# -*- coding:UTF-8 -*-
import numpy as np
from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    逐笔成交     0       X-BondT+1        是         原始       cs1


def init(context):
    # 时间: 2020-09-01 ~ 2020-09-03

    # boll_len   :     20
    # std_ratio  :      2
    # =======add parameter======================================================================
    context.boll_len = add_parameter(int, 'boll_len', 'boll_len')
    context.std_ratio = add_parameter(float, 'std_ratio', 'std_ratio')
    # ==========================================================================================

    # =======add factor=========================================================================
    context.up_band_show = add_factor(float, 'up_band_show', 'up_band_show')
    context.down_band_show = add_factor(float, 'down_band_show', 'down_band_show')
    context.new_px = add_factor(float, 'new_px', 'new_px')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.up_band = []
    context.down_band = []
    # ==============================================


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    boll_len = int(context.boll_len)
    std_ratio = float(context.std_ratio)

    # =============================================================================
    his_tick = get_bar_n(cic_code=context.cs1.cic_code,
                         interval=context.cs1.interval,
                         count=boll_len,
                         fields=['price'])

    his_tick = list(np.array(his_tick['price']))

    if not his_tick:
        return
    # =============================================================================

    on_tick_mean = np.nanmean(his_tick)
    on_tick_std = np.nanstd(his_tick)

    on_tick_up_band = round(on_tick_mean + std_ratio * on_tick_std, 4)
    on_tick_down_band = round(on_tick_mean - std_ratio * on_tick_std, 4)

    context.up_band.append(on_tick_up_band)
    context.down_band.append(on_tick_down_band)

    # factor ============================================
    context.up_band_show = context.up_band[-1]
    context.down_band_show = context.down_band[-1]
    context.new_px = tick.price
    # ===================================================

    if context.all_holding == 0:
        volumed = 1000000
    else:
        volumed = 2000000

    if len(context.up_band) > 3 and len(context.down_band) > 3 and his_tick[-2] < \
            context.up_band[-2] and his_tick[-1] >= context.up_band[-1]:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=volumed,
                   price=tick.price,
                   order_type=OrderType.LIMIT,
                   side=OrderSide.SELL,
                   strategy_group='A')

    if len(context.up_band) > 3 and len(context.down_band) > 3 and his_tick[-2] > \
            context.down_band[-2] and his_tick[-1] <= context.down_band[-1]:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=volumed,
                   price=tick.price,
                   order_type=OrderType.LIMIT,
                   side=OrderSide.BUY,
                   strategy_group='A')


def on_order(context, order):
    pass