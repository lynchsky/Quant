# -*- coding:UTF-8 -*-
from ComstarApi import *
import numpy as np


# 行情设置
# 行情码          类型        频率    下单平台           是否撮合    数据清洗    全域变量
# 200210.CFXO    K-Bar      5min    X-BondT+1        是         原始       cs1


def init(context):
    '''
    网格策略
    1. 计算过去 t 个bar收盘价的 mean和 std。
    2. 计算当前收盘价偏离均值几倍标准差
    3. 根据事先设定的标准，价格偏离均值达到不同的倍数，则使仓位达到不同的程度。

    # 时间：2020-09-01 ~ 2020-09-30

    # stdPeriod:   20
    # stdLevel1:  1.2
    # stdLevel2:  1.8
    '''

    # =======add parameter======================================================================
    context.stdPeriod = add_parameter(int, 'stdPeriod', '计算周期')   # 计算周期， 默认：20
    context.stdLevel1 = add_parameter(float, 'stdLevel1', 'std1宽度阈值')  # std1宽度阈值， 默认：1.2
    context.stdLevel2 = add_parameter(float, 'stdLevel2', 'std2宽度阈值')  # std2宽度阈值， 默认：1.8
    # ==========================================================================================

    # =======add factor=========================================================================
    context.nstdLevel2Factor = add_factor(float, 'nstdLevel2Factor', 'nstd2')  # 负std2，最低
    context.nstdLevel1Factor = add_factor(float, 'nstdLevel1Factor', 'nstd1')  # 负std1，次低
    context.meanFactor = add_factor(float, 'meanFactor', 'mean')  # 均值，中
    context.stdLevel1Factor = add_factor(float, 'stdLevel1Factor', 'std1')  # 正std1，次高
    context.stdLevel2Factor = add_factor(float, 'stdLevel2Factor', 'std2')  # 正std2，最高
    context.stdFactor = add_factor(float, 'stdFactor', 'std')  # 正std2，最高
    # ==========================================================================================

    # ==========global variable=====================
    context.all_Holding = 0  # position
    context.oneHand = 100_0000
    context.whetherReverse = 1
    # ==============================================


def on_bar(context, bar):
    his_data = get_bar_n(cic_code=context.cs1.cic_code,
                         interval=context.cs1.interval,
                         count=context.stdPeriod,
                         fields=['open', 'high', 'low', 'close'])
    his_data = {k: np.array(his_data[k]) for k in his_data}

    # 计算指标
    std = np.nanstd(his_data['close'], ddof=1)
    mean = np.nanmean(his_data['close'])
    stdLevel2Line = mean + context.stdLevel2 * std
    stdLevel1Line = mean + context.stdLevel1 * std
    nstdLevel2Line = mean - context.stdLevel2 * std
    nstdLevel1Line = mean - context.stdLevel1 * std

    # 画因子
    context.nstdLevel2Factor = nstdLevel2Line  # 负std2，最低
    context.nstdLevel1Factor = nstdLevel1Line  # 负std1，次低
    context.meanFactor = mean  # 均值，中
    context.stdLevel1Factor = stdLevel1Line  # 正std1，次高
    context.stdLevel2Factor = stdLevel2Line  # 正std2，最高

    # 设置目标交易量
    targetVolume = 0
    if bar.close < nstdLevel2Line:
        targetVolume = -2 * context.oneHand * context.whetherReverse
    elif nstdLevel2Line <= bar.close < nstdLevel1Line:
        targetVolume = -1 * context.oneHand * context.whetherReverse
    elif nstdLevel1Line <= bar.close < stdLevel1Line:
        targetVolume = 0 * context.oneHand * context.whetherReverse
    elif stdLevel1Line <= bar.close < stdLevel2Line:
        targetVolume = 1 * context.oneHand * context.whetherReverse
    elif stdLevel2Line <= bar.close:
        targetVolume = 2 * context.oneHand * context.whetherReverse

    # 设置交易方向
    toTradeDirect = OrderSide.NKNOWN
    if targetVolume > context.all_Holding:
        toTradeDirect = OrderSide.BUY
    elif targetVolume < context.all_Holding:
        toTradeDirect = OrderSide.SELL
    else:
        toTradeDirect = OrderSide.NKNOWN

    # 发单量
    toTradeVolume = abs(targetVolume - context.all_Holding)
    if toTradeVolume != 0 and toTradeDirect != OrderSide.NKNOWN:
        send_order(platform_code=context.cs1.platform,
                   security_id=context.cs1.symbol,
                   volume=toTradeVolume,
                   price=round(bar.close + 0.005 * np.sign(targetVolume - context.all_Holding),4),
                   order_type=OrderType.LIMIT,
                   side=toTradeDirect,
                   strategy_group='A')
        # 临时记录
        if toTradeDirect == OrderSide.SELL:
            context.all_Holding -= toTradeVolume
        if toTradeDirect == OrderSide.BUY:
            context.all_Holding += toTradeVolume


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass