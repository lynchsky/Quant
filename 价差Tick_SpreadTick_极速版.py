# -*- coding:UTF-8 -*-
import numpy as np
from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    逐笔成交     0       X-BondT+1        是         原始       cs1
# T2103.CFF      逐笔成交     0       中金所            是         原始       cs2


def init(context):
    # 时间: 2020-11-02 ~ 2020-11-02

    # boll_len :     50
    # std_ratio:      2
    # =======add parameter======================================================================
    context.boll_len = add_parameter(int, 'boll_len', 'boll_len')
    context.std_ratio = add_parameter(int, 'std_ratio', 'std_ratio')
    # ==========================================================================================

    # =======add factor=========================================================================
    context.up_band_show = add_factor(float, 'up_band_show', 'f1')
    context.down_band_show = add_factor(float, 'down_band_show', 'f2')
    context.new_spread = add_factor(float, 'new_spread', 'f3')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.up_band = []
    context.down_band = []
    context.flag_1 = 0
    context.flag_2 = 0
    context.old_asset_1_time = 0
    context.old_asset_2_time = 0
    context.new_asset_1_time = 0
    context.new_asset_2_time = 0
    context.asset_1_price = []
    context.asset_2_price = []
    context.spread_list = []
    # ==============================================


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    # 转换参数
    boll_len = int(context.boll_len)
    std_ratio = int(context.std_ratio)

    context.flag_1 = 0  # if_send_order
    context.flag_2 = 0  # if_send_order

    if tick.security_id == context.cs1.symbol:  # asset_1
        context.new_asset_1_time = context.transactionTime
        context.asset_1_price.append(tick.price)

    if tick.security_id == context.cs2.symbol:  # asset_2
        context.new_asset_2_time = context.transactionTime
        context.asset_2_price.append(tick.price)

    if int(context.new_asset_1_time) > int(context.old_asset_1_time) and \
            int(context.new_asset_2_time) > int(context.old_asset_2_time):
        context.old_asset_1_time = context.new_asset_1_time
        context.old_asset_2_time = context.new_asset_2_time
        context.spread_list.append(context.asset_1_price[-1] - context.asset_2_price[-1])

        if len(context.spread_list) > boll_len:
            # 求
            boll_mean = np.nanmean(context.spread_list[-boll_len:])
            boll_std = np.nanstd(context.spread_list[-boll_len:])

            context.up_band.append(boll_mean + std_ratio * boll_std)
            context.down_band.append(boll_mean - std_ratio * boll_std)

            # factor ====
            
            context.up_band_show = round(context.up_band[-1], 4)
            context.down_band_show = round(context.down_band[-1], 4)
            context.new_spread = round(context.spread_list[-1], 4)
            # ===========

            # 设置仓位
            if context.all_holding == 0:
                volume = 10000000
            else:
                volume = 20000000

            if len(context.up_band) > 2 and len(context.down_band) > 2 and \
                    context.spread_list[-2] < context.up_band[-2] and context.spread_list[-1] > context.up_band[-1]:
                # sell spread, sell s buy b
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=volume,
                           price=context.asset_1_price[-1],
                           order_type=OrderType.LIMIT,
                           side=OrderSide.SELL,
                           strategy_group='A')
                # write_log('发单成功 卖出')
                print('发单成功 卖出')

                send_order(platform_code=context.cs2.platform,
                           security_id=context.cs2.symbol,
                           volume=volume,
                           price=context.asset_2_price[-1],
                           order_type=OrderType.LIMIT,
                           side=OrderSide.BUY,
                           strategy_group='A')
                # write_log('发单成功 买入')
                print('发单成功 买入')

            if len(context.up_band) > 2 and len(context.down_band) > 2 and \
                    context.spread_list[-2] > context.down_band[-2] and context.spread_list[-1] < context.down_band[-1]:
                # buy spread, buy s sell b
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=volume,
                           price=context.asset_1_price[-1],
                           order_type=OrderType.LIMIT,
                           side=OrderSide.BUY,
                           strategy_group='A')
                # write_log('发单成功 买入')
                print('发单成功 买入')

                send_order(platform_code=context.cs2.platform,
                           security_id=context.cs2.symbol,
                           volume=volume,
                           price=context.asset_2_price[-1],
                           order_type=OrderType.LIMIT,
                           side=OrderSide.SELL,
                           strategy_group='A')
                # write_log('发单成功 卖出')
                print('发单成功 卖出')


def on_order(context, order):
    pass