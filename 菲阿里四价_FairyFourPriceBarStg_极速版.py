# -*- coding:UTF-8 -*-
from ComstarApi import *
import datetime
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      5min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    菲阿里四价策略
    是一种趋势型日内交易策略。昨天高点、昨天低点、昨日收盘价、今天开盘价，可并称为菲阿里四价。
    一般认为这四个价格对日内交易最为关键。本策略中主要使用昨天高点、昨天低点。将昨天高点定为上轨，昨天低点定为下轨。
    参数：
    # 时间：2020-09-01 ~ 2020-09-30

    # Ndays          :     1
    # cleanHour      :    16
    # maxHand        :     2
    # perHandInterval:  0.05
    '''

    # =======add parameter======================================================================
    context.Ndays = add_parameter(int, 'Ndays', 'N日内关键价格')  # N日内的HH，LC，HC，LL, 默认：1
    context.cleanHour = add_parameter(int, 'cleanHour', '每日平仓时间')  # 每日平仓的时间，24小时计, 默认：16
    context.maxHand = add_parameter(int, 'maxHand', '最大开仓次数') # 最大开仓手数，默认：2
    context.perHandInterval = add_parameter(float, 'perHandInterval', '价格档位差') # 每突破多少追加1手， 默认：0.05
    # ==========================================================================================

    # =======add factor=========================================================================
    context.upFactor = add_factor(float, 'upFactor', 'f1')
    context.downFactor = add_factor(float, 'downFactor', 'f2')
    context.closePrice = add_factor(float, 'closePrice', 'f3')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    # 用户自定义策略需要的变量
    context.doClose = True # True 日内平仓，False 日内不平仓
    context.oneHand = 1000000  # 每单位开仓量
    context.historyOHLC = {}  # N日历史，开高低收高低，每日独立存放{"日期":{"Open":,"High":,"Low":,"Close":}}
    context.todayFirstOHLC = {} # 当日第一根Bar的开高低收{"Open":,"High":,"Low":,"Close":}
    context.preBar = None
    context.whetherReverse = 1  # 是否使用反转策略，1：不用反转，-1：用反转
    # ==============================================


def on_bar(context, bar):
    # 初始化前一根Bar
    if context.preBar is None:
        context.preBar = bar
    # 记录价格因子
    context.closePrice = bar.close
    # 当前bar的时间：如2020-10-16 11:09:46
    # curTime = datetime.datetime.fromtimestamp(int(int(context.transactionTime) / 1000))
    curTime = datetime.datetime.strptime(bar.transact_time,'%Y-%m-%d %H:%M:%S.%f')
    # 当前时间Str
    curTimeStr = datetime.datetime.strftime(curTime, "%Y-%m-%d %H:%M:%S")
    print(curTimeStr)
    # 当前日期str
    curDateStr = datetime.datetime.strftime(curTime.date(), "%Y-%m-%d")
    print(curDateStr)
    # 当前小时
    curHour = curTime.hour
    print(curHour)
    # 当前价格
    curPrice = bar.close
    prePrice = context.preBar.close
    print(prePrice, curPrice)
    # nDay的开高低收
    hisData = getNdayOHLD(bar, context.historyOHLC, curDateStr, context.Ndays)
    if hisData is not None:
        yesHigh = hisData[curDateStr]["High"]
        yesLow = hisData[curDateStr]["Low"]
        # 时间处于日内平仓时点前
        if curHour < context.cleanHour:
            # 上界、下界的因子
            context.upFactor = yesHigh
            context.downFactor = yesLow
            targetVolume = 0
            # 1. 突破上界，开多
            if curPrice > yesHigh:
                buyHand = int((curPrice - yesHigh)/context.perHandInterval)
                targetVolume = min(buyHand, context.maxHand) * context.oneHand * context.whetherReverse
            # 2. 突破下界，开空
            elif curPrice < yesLow:
                sellHand = int((yesLow - curPrice)/context.perHandInterval)
                targetVolume = -min(sellHand, context.maxHand) * context.oneHand * context.whetherReverse
            # 3. 其他情况保持仓位不动
            else:
                targetVolume = context.all_holding
            # 交易方向判断、交易量
            toTradeVolume = targetVolume - context.all_holding
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
                           price=round(bar.close + 0.005 * np.sign(targetVolume - context.all_holding),4),
                           order_type=OrderType.LIMIT,
                           side=toTradeDirect,
                           strategy_group='A')
                # 临时记录
                if toTradeDirect == OrderSide.SELL:
                    context.all_holding -= toTradeVolume
                if toTradeDirect == OrderSide.BUY:
                    context.all_holding += toTradeVolume
        #16点后平仓
        else:
            if context.doClose:
                targetVolume = 0
                # 交易方向判断、交易量
                toTradeVolume = targetVolume - context.all_holding
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
                               price=round(bar.close + 0.005 * np.sign(targetVolume - context.all_holding),4),
                               order_type=OrderType.LIMIT,
                               side=toTradeDirect,
                               strategy_group='A')
                    # 临时记录
                    if toTradeDirect == OrderSide.SELL:
                        context.all_holding -= toTradeVolume
                    if toTradeDirect == OrderSide.BUY:
                        context.all_holding += toTradeVolume
            context.upFactor = ""
            context.downFactor = ""
    # 最后更新priBar
    context.preBar = bar


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass


# 获得n日合并的开高低收
def getNdayOHLD(bar, hisDataStruct, curTimeKey, nDay):
    result = {curTimeKey: {"Open": None, "High": None, "Low": None, "Close": None}}
    # 该日第一个bar
    if hisDataStruct.get(curTimeKey, None) is None:
        result[curTimeKey]["Open"] = float(bar.open)
        result[curTimeKey]["High"] = float(bar.high)
        result[curTimeKey]["Low"] = float(bar.low)
        result[curTimeKey]["Close"] = float(bar.close)
        hisDataStruct[curTimeKey] = result[curTimeKey].copy()
    # 该日已存在bar
    else:
        hisDataStruct[curTimeKey]["High"] = max(float(bar.high), float(hisDataStruct[curTimeKey]["High"]))
        hisDataStruct[curTimeKey]["Low"] = min(float(bar.low), float(hisDataStruct[curTimeKey]["Low"]))
        hisDataStruct[curTimeKey]["Close"] = float(bar.close)
    # 数量达到nDay
    if len(hisDataStruct.keys()) >= nDay + 1:
        if len(hisDataStruct.keys()) > nDay + 1:
            del hisDataStruct[list(hisDataStruct.keys())[0]]
        result[curTimeKey]["Open"] = list(hisDataStruct.values())[-(nDay + 1)]["Open"]
        result[curTimeKey]["High"] = max([one["High"] for one in list(hisDataStruct.values())[-(nDay + 1):-1]])
        result[curTimeKey]["Low"] = min([one["Low"] for one in list(hisDataStruct.values())[-(nDay + 1):-1]])
        result[curTimeKey]["Close"] = list(hisDataStruct.values())[-2]["Close"]
    # 数量不足
    else:
        result = None
    return result


# 当日第一根Bar的开高低收{"Open":,"High":,"Low":,"Close":}
def getTodayFirstOHLD(bar, todayFirstStruct, curTimeKey):
    result = {curTimeKey: {"Open": None, "High": None, "Low": None, "Close": None}}
    # 该日第一个bar
    if todayFirstStruct.get(curTimeKey, None) is None:
        result[curTimeKey]["Open"] = float(bar.open)
        result[curTimeKey]["High"] = float(bar.high)
        result[curTimeKey]["Low"] = float(bar.low)
        result[curTimeKey]["Close"] = float(bar.close)
        todayFirstStruct[curTimeKey] = result[curTimeKey]
        return todayFirstStruct[curTimeKey]
    else:
        return todayFirstStruct[curTimeKey]