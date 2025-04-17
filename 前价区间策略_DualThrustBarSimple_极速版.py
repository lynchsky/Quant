# -*- coding:UTF-8 -*-
from ComstarApi import *
import datetime
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      1min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    Dual Thrust 日内交易策略。仅支持 Bar
    计算N日High的最高价HH, 计算N日Close的最低价LC，计算N日Close的最高价HC，N日Low的最低价LL
    Range = Max(HH-LC,HC-LL), BuyLine = Open + K1*Range, SellLine = Open - K2*Range
    参数：
    # 时间：2020-09-01 ~ 2020-09-30

    # Ndays   :     1
    # upK1    :   0.1
    # downK2  :   0.1
    '''

    # =======add parameter======================================================================
    context.Ndays = add_parameter(int, 'Ndays', 'N日内关键价格')  # N日内的HH，LC，HC，LL, 默认：1
    context.upK1 = add_parameter(float, 'upK1', '上轨系数')  # 上轨系数，默认：0.1
    context.downK2 = add_parameter(float, 'downK2', '下轨系数')  # 下轨系数，默认：0.1
    # ==========================================================================================

    # =======add factor=========================================================================
    context.curCloseFactor = add_factor(float, 'curCloseFactor', 'curClose')
    context.buyFactor = add_factor(float, 'buyFactor', 'f1')
    context.sellFactor = add_factor(float, 'sellFactor', 'f2')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.oneHand = 1000000  # 每单位开仓量
    # 用户自定义策略需要的变量
    context.hisData = {}  # 存历史数据字典，日期为key
    context.whetherReverse = 1  # 是否使用反转策略，1：不用反转，-1：用反转
    # ==============================================


def on_bar(context, bar):
    # 当前bar的时间：如2020-10-16 11:09:46
    print(bar.transact_time)
    # curTime = datetime.datetime.fromtimestamp(int(int(context.transactionTime) / 1000))
    curTime = datetime.datetime.strptime(bar.transact_time,'%Y-%m-%d %H:%M:%S.%f')
    print(f'curTime:{curTime}')
    # 当前日期
    curDate = curTime.date()
    strcurDate = datetime.datetime.strftime(curDate, "%Y-%m-%d")

    # 新的一天,处理n日
    if context.hisData.get(strcurDate, None) is None:
        context.hisData[strcurDate] = {"open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close}
        # context.Ndays + 当前天，累计超出删掉
        if len(list(context.hisData.keys())) > context.Ndays + 1:
            del context.hisData[list(context.hisData.keys())[0]]
    # 日内更新开高低收
    else:
        context.hisData[strcurDate]["high"] = max(context.hisData[strcurDate]["high"], bar.high)
        context.hisData[strcurDate]["low"] = min(context.hisData[strcurDate]["low"], bar.low)
        context.hisData[strcurDate]["close"] = bar.close
    # 满足过去n天
    if len(list(context.hisData.keys())) == context.Ndays + 1:
        # 临近日终
        if curTime.hour > 15:
            targetVolume = 0
            toTradeVolume = abs(targetVolume - context.all_holding)
            toTradeDirect = OrderSide.NKNOWN
            if context.all_holding < 0:
                toTradeDirect = OrderSide.BUY
            elif context.all_holding > 0:
                toTradeDirect = OrderSide.SELL
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
            print(toTradeVolume, toTradeDirect)
            context.buyFactor = ""
            context.sellFactor = ""
        # 日内交易逻辑
        else:

            HH = np.nanmax([context.hisData[one]["high"] for one in list(context.hisData.keys())[:-1]])
            HC = np.nanmax([context.hisData[one]["close"] for one in list(context.hisData.keys())[:-1]])
            LC = np.nanmin([context.hisData[one]["close"] for one in list(context.hisData.keys())[:-1]])
            LL = np.nanmin([context.hisData[one]["low"] for one in list(context.hisData.keys())[:-1]])
            # HH,HC,LC,LL没问题
            pRange = max(HH - LC, HC - LL)
            # 计算上下轨
            buyLine = context.hisData[strcurDate]["open"] + context.upK1 * pRange
            sellLine = context.hisData[strcurDate]["open"] - context.downK2 * pRange
            # 记录AR、BR因子
            context.buyFactor = buyLine
            context.sellFactor = sellLine
            # 初始化 目标持仓，待交易量
            targetVolume = 0
            toTradeVolume = 0
            # 触发买入
            if bar.close > buyLine:
                targetVolume = context.whetherReverse * context.oneHand
                toTradeVolume = targetVolume - context.all_holding
            # 触发卖出
            elif bar.close < sellLine:
                targetVolume = context.whetherReverse * (-context.oneHand)
                toTradeVolume = targetVolume - context.all_holding
            # 交易方向判断
            toTradeDirect = OrderSide.NKNOWN
            if toTradeVolume > 0:
                toTradeDirect = OrderSide.BUY
            elif toTradeVolume < 0:
                toTradeDirect = OrderSide.SELL
            else:
                toTradeDirect = OrderSide.NKNOWN
            toTradeVolume = abs(toTradeVolume)
            if toTradeVolume != 0 and toTradeDirect != OrderSide.NKNOWN:
                send_order(platform_code=context.cs1.platform,
                           security_id=context.cs1.symbol,
                           volume=toTradeVolume,
                           price=bar.close + 0.005 * np.sign(targetVolume - context.all_holding),
                           order_type=OrderType.LIMIT,
                           side=toTradeDirect,
                           strategy_group='A')
                # 临时记录
                if toTradeDirect == OrderSide.SELL:
                    context.all_holding -= toTradeVolume
                if toTradeDirect == OrderSide.BUY:
                    context.all_holding += toTradeVolume
    # 尚不满足
    else:
        pass
    context.curCloseFactor = bar.close


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass