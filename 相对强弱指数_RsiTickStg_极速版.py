# -*- coding:UTF-8 -*-
from ComstarApi import *
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    逐笔成交     0       X-BondT+1        是         原始       cs1


def init(context):
    '''
    RSI策略
    相对强弱指数RSI是根据一定时期内上涨和下跌幅度之和的比率制作出的一种技术曲线。
    能够反映出市场在一定时期内的景气程度。以向上的力量与向下的力量进行比较，若向上的力量较大，则计算出来的指标上升；
    若向下的力量较大，则指标下降，由此测算出市场走势的强弱。
    参数：
    # 时间：2020-09-01 ~ 2020-09-03

    # period  :    50
    '''

    # =======add parameter======================================================================
    context.period = add_parameter(int, 'period', '计算周期')  # 默认：50
    # ==========================================================================================

    # =======add factor=========================================================================
    context.rsiFactor = add_factor(float, 'rsiFactor', 'rsi')
    # ==========================================================================================

    # =======global variable====================================================================
    context.all_holding = 0  # position
    context.targetPos = 0  # 目标仓位
    context.tick_list = []
    context.oneHand = 1000000  # 每单位开仓量
    context.whetherReverse = 1# 是否使用反转策略，1：不用反转，-1：用反转
    # ==========================================================================================


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    context.tick_list.append(tick.price)
    context.tick_list = context.tick_list[-(1 + context.period):]
    
    if len(context.tick_list) >= (1 + context.period):
        # RSI = 0
        period = context.period
        rsiDiffPct = (np.array(context.tick_list[-period:]) - np.array(context.tick_list[-(1 + period):-1])) / \
                     np.array(np.array(context.tick_list[-(1 + period):-1]))
        # 计算指标
        on_tick_up = np.nansum(rsiDiffPct[rsiDiffPct > 0])
        on_tick_down = np.nansum(rsiDiffPct[rsiDiffPct < 0])
        RSI = int(round(on_tick_up / (on_tick_up - on_tick_down), 1) * 100)

        # 因子展示用
        context.rsiFactor = RSI

        # 设置目标交易量、交易方向
        toTradeDirect = OrderSide.NKNOWN
        if 30 <= RSI <= 40 or 90 < RSI:
            context.targetPos = 1*context.oneHand * context.whetherReverse
        elif 10 <= RSI <= 20:
            context.targetPos = 2*context.oneHand * context.whetherReverse
        elif RSI < 10 or 60 <= RSI <= 70:
            context.targetPos = -1*context.oneHand * context.whetherReverse
        elif 80 <= RSI <= 90:
            context.targetPos = -2*context.oneHand * context.whetherReverse
        else:
            context.targetPos = context.all_holding
        toTradeVolume = abs(context.targetPos - context.all_holding)
        if context.targetPos > context.all_holding:
            toTradeDirect = OrderSide.BUY
        elif context.targetPos < context.all_holding:
            toTradeDirect = OrderSide.SELL

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
            context.holdFactor = context.all_holding


def on_order(context, order):
    pass