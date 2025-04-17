# -*- coding:UTF-8 -*-
from ComstarApi import *
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      1min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    BRAR策略
    1.AR指标是通过比较一段周期内的开盘价在该周期价格中的高低。从而反映市场买卖人气的技术指标。以计算周期为日为例，其计算公式为：
      N日AR=(N日内（H－O）之和除以N日内（O－L）之和)*100,其中，H为当日最高价，L为当日最低价，O为当日开盘价，N为设定的时间参数
    2.BR指标是通过比较一段周期内的收盘价在该周期价格波动中的地位，来反映市场买卖意愿程度的技术指标。以计算周期为日为例，其计算公式为：
      N日BR=N日内（H－CY）之和除以N日内（CY－L）之和*100, 其中H－CY、CY－L都要大于0.其中，H为当日最高价，L为当日最低价，
      CY为前一交易日的收盘价，N为设定的时间参数。
    参数：
    # 时间：2020-09-01 ~ 2020-09-30

    # period  :    20
    # BRup    :   140
    # BRdown  :    70
    '''
    # =======add parameter======================================================================
    context.period = add_parameter(int, 'period', '指标长度')
    context.BRup = add_parameter(int, 'BRup', 'BR上界')
    context.BRdown = add_parameter(int, 'BRdown', 'BR下界')
    # ==========================================================================================

    # =======add factor=========================================================================
    context.arFactor = add_factor(float, 'arFactor', 'f1')
    context.brFactor = add_factor(float, 'brFactor', 'f2')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.targetPos = 0  # 目标仓位
    context.oneHand = 1000000        # 每单位开仓量
    # ==============================================


def on_bar(context, bar):
    his_data = get_bar_n(cic_code=context.cs1.cic_code,
                         interval=context.cs1.interval,
                         count=(context.period + 1),
                         fields=['open', 'high', 'low', 'close'])
    his_data = {k: np.array(his_data[k]) for k in his_data}

    if len(his_data['close']) >= (context.period+1):
        his_open = his_data['open'][1:]
        his_high = his_data['high'][1:]
        his_low = his_data['low'][1:]
        his_close = his_data['close'][:-1]
        # 1. 计算n Bar内 high - open, open - low, high - yesterdayclose, yesterdayclose - low均值
        AR = 100
        BR = 100
        highOpen = np.nansum(np.array(his_high) - np.array(his_open))
        openLow = np.nansum(np.array(his_open) - np.array(his_low))
        # H - CY 取正值 否则取0
        BrCondition1 = (np.array(his_high) - np.array(his_close)) > 0
        highYestdayClose = np.nansum(np.where(BrCondition1, np.array(his_high) - np.array(his_close), 0))
        # CY - L 取正值 否则取0
        BrCondition2 = (np.array(his_close) - np.array(his_low)) > 0
        yestdayCloseLow = np.nansum(np.where(BrCondition2, np.array(his_close) - np.array(his_low), 0))
        # 防止分母为0
        if openLow != 0:
            AR = highOpen / openLow * 100
        if yestdayCloseLow != 0:
            BR = highYestdayClose / yestdayCloseLow * 100
        # 记录AR、BR因子
        context.arFactor = AR
        context.brFactor = BR
        # 2.判断即将下单的tradeVolume量, 以及交易方向
        targetVolume = 0
        # br <= ar 且 br <= 70, 开空
        if BR <= AR and BR <= context.BRdown:
            targetVolume = -1 * context.oneHand
        # br >= ar 且 br >= 140, 开多
        elif BR >= AR and BR >= context.BRup:
            targetVolume = 1 * context.oneHand
        # 平仓
        elif (BR >= 120 and AR >= 120 and context.all_holding < 0) or (BR <= 80 and AR <= 80 and context.all_holding > 0):
            targetVolume = 0
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
            # 临时记录
            if toTradeDirect == OrderSide.SELL:
                context.all_holding -= toTradeVolume
            if toTradeDirect == OrderSide.BUY:
                context.all_holding += toTradeVolume


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass