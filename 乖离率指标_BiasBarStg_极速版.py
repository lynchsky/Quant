# -*- coding:UTF-8 -*-
from ComstarApi import *
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      1min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    BIAS策略
    乖离率(BIAS)，又称偏离率，是通过计算收盘价与移动平均线之间的差距百分比，以反映一定时期内价格与其MA偏离程度的指标，
    从而得出价格在剧烈波动时因偏离移动平均趋势而造成回档或反弹的可能性，以及价格在正常波动范围内移动而形成继续原有势的可信度。
    参数：
    # 时间：2020-09-01 ~ 2020-09-30

    # threshold  :0.0002
    # shortPeriod:     5
    # longPeriod :    20
    '''
    # =======add parameter======================================================================
    context.threshold = add_parameter(float, 'threshold', '突破的阈值')  # 突破的阈值，默认：0.0002
    context.shortPeriod = add_parameter(int, 'shortPeriod', '短期Bias')  # 短期Bias回看根数，默认：5
    context.longPeriod = add_parameter(int, 'longPeriod', '长期Bias')  # 长期Bias回看根数，默认：20
    # ==========================================================================================

    # =======add factor=========================================================================
    context.shortFactor = add_factor(float, 'shortFactor', 'short')
    context.longFactor = add_factor(float, 'longFactor', 'long')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.oneHand = 1000000  # 每单位开仓量
    context.whetherReverse = 1  # 是否使用反转策略，1：不用反转，-1：用反转
    # ==============================================


def on_bar(context, bar):
    his_data = get_bar_n(cic_code=context.cs1.cic_code,
                         interval=context.cs1.interval,
                         count=(context.longPeriod + 1),
                         fields=['open', 'high', 'low', 'close'])
    his_data = {k: np.array(his_data[k]) for k in his_data}

    # 取到足够数据
    if len(his_data['close']) >= (context.longPeriod + 1):
        # 计算长短Bias
        longMean = float(np.nanmean(his_data['close'][-context.longPeriod:]))
        shortMean = float(np.nanmean(his_data['close'][-context.shortPeriod:]))
        longBias = float((his_data['close'][-1] - longMean) / longMean)
        shortBias = float((his_data['close'][-1] - shortMean) / shortMean)

        # 因子记录
        context.shortFactor = shortBias
        context.longFactor = longBias

        # 2.判断即将下单的tradeVolume量, 以及交易方向
        targetVolume = 0
        # 短期Bias > 长期Bias
        if shortBias > longBias and shortBias >= context.threshold:
            targetVolume = 1 * context.oneHand * context.whetherReverse
        # 短期Bias < 长期Bias
        elif shortBias < longBias and shortBias <= -context.threshold:
            targetVolume = -1 * context.oneHand * context.whetherReverse
        # 保持仓位
        else:
            targetVolume = context.all_holding
        if np.sign(targetVolume - context.all_holding) == 1:
            toTradeDirect = OrderSide.BUY
        elif np.sign(targetVolume - context.all_holding) == -1:
            toTradeDirect = OrderSide.SELL
        else:
            toTradeDirect = OrderSide.NKNOWN
        # 判断交易量
        toTradeVolume = abs(targetVolume - context.all_holding)
        # 3.根据tradeVolume，tradeDirection下单
        # -- 需要调仓 (Base已有仓位百分比 与 Base应持有量不同)
        if toTradeVolume != 0 and toTradeDirect != OrderSide.NKNOWN:
            send_order(platform_code=context.cs1.platform,
                       security_id=context.cs1.symbol,
                       volume=toTradeVolume,
                       price=round(bar.close + 0.005 * np.sign(targetVolume - context.all_holding),4),
                       order_type=OrderType.LIMIT,
                       side=toTradeDirect,
                       strategy_group='A')

            # 记录持仓量
            if toTradeDirect == OrderSide.SELL:
                context.all_holding -= toTradeVolume
            if toTradeDirect == OrderSide.BUY:
                context.all_holding += toTradeVolume
    else:
        context.shortFactor = ""
        context.longFactor = ""
        context.test1Factor = ""
        context.test1Factor = ""


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass