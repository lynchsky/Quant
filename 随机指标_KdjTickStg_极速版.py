# -*- coding:UTF-8 -*-
from ComstarApi import *


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    逐笔成交     0       X-BondT+1        是         原始       cs1


def init(context):
    '''
    KDJ策略
    随机指标KDJ一般是用于股票分析的统计体系，根据统计学原理，通过一个特定的周期内出现过的最高价、
    最低价及最后一个计算周期的收盘价及这三者之间的比例关系，来计算最后一个计算周期的未成熟随机值RSV，
    然后根据平滑移动平均线的方法来计算K值、D值与J值，并绘成曲线图来研判走势。
    参数：
    # 时间：2020-09-01 ~ 2020-09-03

    # period       :    30
    # upThreshold  :    70
    # downThreshold:    30
    '''

    # =======add parameter======================================================================
    context.period = add_parameter(int, 'period', '计算周期')  # 计算周期， 默认：30
    context.upThreshold = add_parameter(int, 'upThreshold', '上边界阈值')  # 上边界阈值， 默认：70
    context.downThreshold = add_parameter(int, 'downThreshold', '下边界阈值')  # 下边界阈值， 默认：30
    # ==========================================================================================

    # =======add factor=========================================================================
    context.rsvFactor = add_factor(float, 'rsvFactor', 'f1')
    context.KFactor = add_factor(float, 'KFactor', 'f2')
    context.DFactor = add_factor(float, 'DFactor', 'f3')
    context.JFactor = add_factor(float, 'JFactor', 'f4')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.targetPos = 0  # 目标仓位
    context.tick_list = []

    context.rsvList = []
    context.KList = []
    context.DList = []
    context.JList = []
    context.oneHand = 1000000  # 每单位开仓量
    # ==============================================


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    context.tick_list.append(tick.price)
    context.tick_list = context.tick_list[-context.period:]

    # 策略主逻辑
    if len(context.tick_list) >= context.period:
        period = context.period

        # 计算指标
        priceMin = min(context.tick_list[-period:])
        priceMax = max(context.tick_list[-period:])
        RSV = int(round((tick.price - priceMin) / (priceMax - priceMin), 2) * 100)
        K = int(round(2 / 3 * context.rsvList[-1] + 1 / 3 * RSV, 0))
        D = int(round(2 / 3 * context.KList[-1] + 1 / 3 * K, 0))
        J = 3 * K - 2 * D

        # 收集指标
        context.rsvList.append(RSV)
        context.KList.append(K)
        context.DList.append(D)
        context.JList.append(J)

        # 因子展示用
        context.rsvFactor = context.rsvList[-1]
        context.KFactor = context.KList[-1]
        context.DFactor = context.DList[-1]
        context.JFactor = context.JList[-1]

        # 设置目标交易量、交易方向
        toTradeDirect = OrderSide.NKNOWN
        # K值上穿D值，且K值大于上界
        if context.KList[-2] < context.DList[-2] and context.KList[-1] >= context.DList[-1] and context.KList[
            -1] > context.upThreshold:
            context.targetPos = context.oneHand
        # K值下穿D值，且K值小于下界
        elif context.KList[-2] >= context.DList[-2] and context.KList[-1] < context.DList[-1] and context.KList[
            -1] < context.downThreshold:
            context.targetPos = -context.oneHand
        else:
            context.targetPos = context.all_holding
        toTradeVolume = int(round(abs(context.targetPos - context.all_holding) / 1000000, 0)) * 1000000
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
    else:
        context.rsvList.append(50)
        context.KList.append(50)
        context.DList.append(50)
        context.JList.append(50)


def on_order(context, order):
    pass