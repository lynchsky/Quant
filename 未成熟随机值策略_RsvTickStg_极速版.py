# -*- coding:UTF-8 -*-
from ComstarApi import *
import numpy as np
import pandas as pd



# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    逐笔成交     0       X-BondT+1        是         原始       cs1


def init(context):
    '''
    RSV策略
    主要通过当前价格相对于过去一段时间价格区间的相对位置来衡量当前趋势的强弱，当前价格接近一段时间以来的新高时，RSV指数接近于1，
    当前价格接近一段时间以来的新低时，RSV指数接近于0。
    参数：
    # 时间：2020-09-01 ~ 2020-09-03

    # period  :    50
    '''

    # =======add parameter======================================================================
    context.period = add_parameter(int, 'period', '计算周期')  # 计算周期
    # ==========================================================================================

    # =======add factor=========================================================================
    context.rsvFactor = add_factor(float, 'rsvFactor', 'rsv')
    context.priceFactor = add_factor(float, 'priceFactor', 'price')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.transact_time = ""
    context.tick_list = []
    context.oneHand = 10000000  # 每单位开仓量
    context.whetherReverse = -1  # 是否使用反转策略，1：不用反转，-1：用反转
    # ==============================================


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    context.transact_time = tick.transact_time
    context.tick_list.append(tick.price)
    context.tick_list = context.tick_list[-context.period:]
    context.priceFactor = tick.price
    # 策略主逻辑
    if len(context.tick_list) >= context.period:

        # 计算指标
        priceMin = min(context.tick_list[-context.period:])
        priceMax = max(context.tick_list[-context.period:])
        RSV = int(round((tick.price - priceMin) / (priceMax - priceMin), 1) * 100)

        # 因子展示用
        context.rsvFactor = RSV

        # 设置目标交易量
        toTradeDirect = OrderSide.NKNOWN
        targetVolume = 0
        if 20 < RSV <= 30:
            targetVolume = (-1) * context.oneHand * context.whetherReverse
        elif 0 <= RSV <= 20:
            targetVolume = (-1) * context.oneHand * context.whetherReverse
        elif 70 <= RSV < 80:
            targetVolume = 1 * context.oneHand * context.whetherReverse
        elif 80 <= RSV <= 100:
            targetVolume = 1 * context.oneHand * context.whetherReverse
        else:
            targetVolume = context.all_holding
        toTradeVolume = abs(targetVolume - context.all_holding)

        # 判断交易方向
        if np.sign(targetVolume - context.all_holding) == 1:
            toTradeDirect = OrderSide.BUY
        elif np.sign(targetVolume - context.all_holding) == -1:
            toTradeDirect = OrderSide.SELL
        else:
            toTradeDirect = OrderSide.NKNOWN

        # 发单
        if toTradeDirect != OrderSide.NKNOWN:
            send_order(platform_code=context.cs1.platform,
                       security_id=context.cs1.symbol,
                       volume=toTradeVolume,
                       price=tick.price,
                       order_type=OrderType.LIMIT,
                       side=toTradeDirect,
                       strategy_group='A')

            # 临时记录
            if toTradeDirect == OrderSide.SELL:
                context.all_holding -= toTradeVolume
            if toTradeDirect == OrderSide.BUY:
                context.all_holding += toTradeVolume


def on_order(context, order):
    pass