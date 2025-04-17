# -*- coding:UTF-8 -*-
from ComstarApi import *
import datetime
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      5min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    R-breaker策略:
        是一种中高频的日内交易策略，R-Breaker策略结合了趋势和反转两种交易方式，
    所以交易机会相对较多，比较适合日内1分钟K线或者5分钟K线级别的数据。
        根据昨日的开高低收价位计算出今日的6个目标价位，按照价格高低依次是：
    突破买入价（Bbreak）、观察卖出价（Ssetup）、
    反转卖出价（Senter）、反转买入价（Benter）、
    观察买入价（Bsetup）、突破卖出价（Sbreak）。
    参数：
    # 时间：2020-09-01 ~ 2020-09-30

    # Ndays   :     1
    # percent : 0.001
    # maxHand :     1
    # cleanHour:   16
    '''
    # =======add parameter======================================================================
    context.Ndays = add_parameter(int, 'Ndays', 'N日内关键价格')  # N日内的HH，LC，HC，LL, 默认：1
    context.percent = add_parameter(float, 'percent', '价格档位差')  # 价格突破每 context.percent 加1手, 默认：0.001
    context.maxHand = add_parameter(int, 'maxHand', '最大开仓手数')  # 最大开仓手数,  默认：1
    context.cleanHour = add_parameter(int, 'cleanHour', '每日平仓时间')  # 每日平仓的时间，24小时计,  默认：16
    # ==========================================================================================

    # =======add factor=========================================================================
    context.bBreakFactor = add_factor(float, 'bBreakFactor', 'f1')
    context.sEnterFactor = add_factor(float, 'sEnterFactor', 'f2')
    context.bEnterFactor = add_factor(float, 'bEnterFactor', 'f3')
    context.sBreakFactor = add_factor(float, 'sBreakFactor', 'f4')
    context.closePrice = add_factor(float, 'closePrice', 'f5')
    # ==========================================================================================

    # ==========global variable=====================
    context.all_holding = 0  # position
    context.targetPos = 0  # 目标仓位
    context.oneHand = 1000000  # 每单位开仓量
    # 用户自定义策略需要的变量
    context.doClose = True # True 日内平仓，False 日内不平仓
    context.historyOHLC = {}  # N日历史，开高低收高低，每日独立存放{"日期":{"Open":,"High":,"Low":,"Close":}}
    context.preBar = None  # 记录上一根bar
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
    # 当前日期
    curDate = curTime.date()
    print(curDate)
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
        nHigh = hisData[curDateStr]["High"]
        nLow = hisData[curDateStr]["Low"]
        nClose = hisData[curDateStr]["Close"]
        pivot = (nHigh + nLow + nClose) / 3
        bBreak = nHigh + 2 * (pivot - nLow)  # 突破买入价
        # sSetup = pivot + (nHigh - nLow)      # 观察卖出价
        sEnter = 2 * pivot - nLow  # 反转卖出价
        bEnter = 2 * pivot - nHigh  # 反转买入价
        # bSetup = pivot - (nHigh - nLow)      # 观察买入价
        sBreak = nLow - 2 * (nHigh - pivot)  # 突破卖出价
        # 日内可交易时间,目前不能画线段
        if curHour < context.cleanHour:
            context.bBreakFactor = bBreak
            context.sEnterFactor = sEnter
            context.bEnterFactor = bEnter
            context.sBreakFactor = sBreak
            targetVolume = 0
            # 1. 大于突破买入价，开多2手
            if curPrice > bBreak:
                targetVolume = 2 * context.oneHand * context.whetherReverse
            # 2. 价格上穿bEnter，开多1手
            elif prePrice < bEnter and curPrice >= bEnter:
                targetVolume = 1 * context.oneHand * context.whetherReverse
            # 3. 价格下穿sEnter，开空1手
            elif prePrice > sEnter and curPrice <= sEnter:
                targetVolume = -1 * context.oneHand * context.whetherReverse
            # 4. 小于突破卖出价，开空2手
            elif curPrice < sBreak:
                targetVolume = -2 * context.oneHand * context.whetherReverse
            # 5. 其他情况保持仓位不动
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
        # 16点后平仓
        else:
            context.bBreakFactor = ""
            context.sEnterFactor = ""
            context.bEnterFactor = ""
            context.sBreakFactor = ""
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