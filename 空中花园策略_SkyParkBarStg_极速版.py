# -*- coding:UTF-8 -*-
from ComstarApi import *
import datetime
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      5min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    空中花园策略
    空中花园策略是一种日内交易策略，当开盘价出现向上或向下跳空时，该日考虑进场。
    并认为当天的第一根bar最为重要，以该bar的最高价和最低价为上轨、下轨，当价格突破该区间时下单，
    突破上轨开多单，突破下轨开空单。
    参数：
    # 时间：2020-09-01 ~ 2020-09-30

    # Ndays          :     2
    # cleanHour      :    16
    # jumpRange      :0.0002
    # maxHand        :     3
    # perHandInterval:  0.02
    '''

    # =======add parameter======================================================================
    context.Ndays = add_parameter(int, 'Ndays', 'N日内关键价格')        # N日内的HH，LC，HC，LL, 默认：2
    context.cleanHour = add_parameter(int, 'cleanHour', '每日平仓时间') # 每日平仓的时间，24小时计,默认：16
    context.jumpRange = add_parameter(float, 'jumpRange', '跳空幅度')     # 默认：0.0002
    context.maxHand = add_parameter(int, 'maxHand', '最大开仓次数')     # 最大开仓手数， 默认：3
    context.perHandInterval = add_parameter(float, 'perHandInterval', '价格档位差') # 每突破多少追加1手， 默认：0.02
    # ==========================================================================================

    # =======add factor=========================================================================
    context.upFactor = add_factor(float, 'upFactor', 'up')
    context.downFactor = add_factor(float, 'downFactor', 'down')
    context.closePrice = add_factor(float, 'closePrice', 'close')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    # 用户自定义策略需要的变量
    context.oneHand = 1000000  # 每单位开仓量， 默认：1百万
    context.doClose = True # True 日内平仓，False 日内不平仓
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
    # 当前日期str
    curDateStr = datetime.datetime.strftime(curTime.date(), "%Y-%m-%d")
    # 当前小时
    curHour = curTime.hour
    # 当前价格
    curPrice = bar.close
    # nDay的开高低收
    hisData = getNdayOHLD(bar, context.historyOHLC, curDateStr, context.Ndays)
    if hisData is not None:
        yesClose = hisData[curDateStr]["Close"]
        todayFirst = getTodayFirstOHLD(bar, context.todayFirstOHLC, curDateStr)
        # 有跳空，开始交易判断，并且时间处于日内平仓时点前
        if (todayFirst["Open"] > yesClose * (1 + context.jumpRange) or
            todayFirst["Open"] < yesClose * (1 - context.jumpRange)) and curHour < context.cleanHour:
            # 上界、下界的因子
            context.upFactor = todayFirst["High"]
            context.downFactor = todayFirst["Low"]
            targetVolume = 0
            # 1. 突破上界，开多
            if curPrice > todayFirst["High"]:
                buyHand = int((curPrice - todayFirst["High"])/context.perHandInterval)
                targetVolume = min(buyHand, context.maxHand) * context.oneHand * context.whetherReverse
            # 2. 突破下界，开空
            elif curPrice < todayFirst["Low"]:
                sellHand = int((todayFirst["Low"] - curPrice)/context.perHandInterval)
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
            context.upFactor = ""
            context.downFactor = ""
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