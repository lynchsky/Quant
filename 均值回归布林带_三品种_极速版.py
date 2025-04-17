import numpy as np
import talib
import pandas as pd
from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码和BAR级别仅供参考，可根据需要进行修改）

    行情码                          类型       频率     下单平台                      是否撮合    数据清洗    全域变量
    220205.CFXO / FR007_10Y.CFX    逐笔成交    0        X-BondT+1 / X-Swap实时承接    是         原始        cs1
    220203.CFXO / FR007_5Y.CFX     逐笔成交    0        X-BondT+1 / X-Swap实时承接    是         原始        cs2
    220201.CFXO / FR007_1Y.CFX     逐笔成交    0        X-BondT+1 / X-Swap实时承接    是         原始        cs3
    220205.CFXO / FR007_10Y.CFX    K-Bar      10min    X-BondT+1 / X-Swap实时承接    否         原始        cs4
    220203.CFXO / FR007_5Y.CFX     K-Bar      10min    X-BondT+1 / X-Swap实时承接    否         原始        cs5
    220201.CFXO / FR007_1Y.CFX     K-Bar      10min    X-BondT+1 / X-Swap实时承接    否         原始        cs6

    策略逻辑

    计算相同类别（现券或IRS）三个不同品种过去N根K-BAR的价差（短期限 + 长期限 - 2 * 中期限）及价差的布林通道。
    当实时价差突破布林上轨时卖出价差；当实时价差跌破布林下轨时买入价差。
    """

    # 接收参数
    context.boll_period = add_parameter(int, 'boll_period', '布林通道计算周期')
    context.multiple = add_parameter(float, 'multiple', '标准差倍数')
    context.cs1_trade_volume = add_parameter(int, 'cs1_trade_volume', 'CS1下单量')
    context.cs2_trade_volume = add_parameter(int, 'cs2_trade_volume', 'CS2下单量')
    context.cs3_trade_volume = add_parameter(int, 'cs3_trade_volume', 'CS3下单量')

    # 添加因子
    context.tick_spread = add_factor(float, 'tick_spread', '实时价差')
    context.bar_spread = add_factor(float, 'bar_spread', 'BAR价差')
    context.boll_upper = add_factor(float, 'boll_upper', '布林上轨')
    context.boll_lower = add_factor(float, 'boll_lower', '布林下轨')

    # 添加全局变量
    context.strategy_group = 'A'
    context.cur_boll_upper = None
    context.cur_boll_lower = None
    context.cs1_price = None
    context.cs2_price = None
    context.cs3_price = None
    context.buy_flag = True
    context.sell_flag = True
    context.first_open = True


def on_bar(context, bar):
    # 获取短期限品种与中期限品种收盘价的价差数据
    # short_middle_bar_spread_data = get_diff_history_n(first_cic_code=context.cs6.cic_code,
    #                                                   first_category='deal',
    #                                                   first_interval=context.cs6.interval,
    #                                                   first_field='close',
    #                                                   second_cic_code=context.cs5.cic_code,
    #                                                   second_category='deal',
    #                                                   second_interval=context.cs5.interval,
    #                                                   second_field='close',
    #                                                   count=context.boll_period)

    # # 对获取到的数据进行填充操作
    # short_middle_bar_spread_data = format_data(short_middle_bar_spread_data['close-close'], method='fill')

    bar_data_1 = get_bar_n(cic_code=context.cs6.cic_code,
                                interval=context.cs6.interval,
                                count=context.boll_period,
                                fields=['close'])
    bar_data_2 = get_bar_n(cic_code=context.cs5.cic_code,
                            interval=context.cs5.interval,
                            count=context.boll_period,
                            fields=['close'])
    bar_data_1 = pd.Series(bar_data_1['close'])
    bar_data_1.fillna(method='ffill',inplace=True)
    bar_data_1 = np.array(bar_data_1)
    bar_data_2 = pd.Series(bar_data_2['close'])
    bar_data_2.fillna(method='ffill',inplace=True)
    bar_data_2 = np.array(bar_data_2)
    short_middle_bar_spread_data = bar_data_1 - bar_data_2

    # 获取长期限品种与中期限品种收盘价的价差数据
    # long_middle_bar_spread_data = get_diff_history_n(first_cic_code=context.cs4.cic_code,
    #                                                  first_category='deal',
    #                                                  first_interval=context.cs4.interval,
    #                                                  first_field='close',
    #                                                  second_cic_code=context.cs5.cic_code,
    #                                                  second_category='deal',
    #                                                  second_interval=context.cs5.interval,
    #                                                  second_field='close',
    #                                                  count=context.boll_period)

    # # 对获取到的数据进行填充操作
    # long_middle_bar_spread_data = format_data(long_middle_bar_spread_data['close-close'], method='fill')

    bar_data_3 = get_bar_n(cic_code=context.cs4.cic_code,
                                interval=context.cs4.interval,
                                count=context.boll_period,
                                fields=['close'])
    bar_data_4 = get_bar_n(cic_code=context.cs5.cic_code,
                            interval=context.cs5.interval,
                            count=context.boll_period,
                            fields=['close'])
    bar_data_3 = pd.Series(bar_data_3['close'])
    bar_data_3.fillna(method='ffill',inplace=True)
    bar_data_3 = np.array(bar_data_3)
    bar_data_4 = pd.Series(bar_data_4['close'])
    bar_data_4.fillna(method='ffill',inplace=True)
    bar_data_4 = np.array(bar_data_4)
    long_middle_bar_spread_data = bar_data_3 - bar_data_4

    # 如果填充后的价差数据的数据量完整且不含NaN值，则进行后续操作
    if (len(short_middle_bar_spread_data) == len(long_middle_bar_spread_data) == context.boll_period) and (
            sum(np.isnan(short_middle_bar_spread_data)) == 0) and (sum(np.isnan(long_middle_bar_spread_data)) == 0):
        # 计算三品种收盘价的价差数据（短期限 + 长期限 - 2 * 中期限）
        bar_spread_data = short_middle_bar_spread_data + long_middle_bar_spread_data

        # 计算三品种收盘价的价差数据的布林通道上下轨
        upper, _, lower = talib.BBANDS(bar_spread_data,
                                       timeperiod=context.boll_period,
                                       nbdevup=context.multiple,
                                       nbdevdn=context.multiple,
                                       matype=0)

        # 因子赋值
        context.bar_spread = bar_spread_data[-1]
        context.boll_upper = upper[-1]
        context.boll_lower = lower[-1]

        # 全局变量赋值
        context.cur_boll_upper = upper[-1]
        context.cur_boll_lower = lower[-1]


def on_tick(context, tick):
    # 如果接收到的是长期限品种的TICK数据，记录TICK的price值
    if tick.cic_code == context.cs1.cic_code:
        context.cs1_price = tick.price

    # 如果接收到的是中期限品种的TICK数据，记录TICK的price值
    if tick.cic_code == context.cs2.cic_code:
        context.cs2_price = tick.price

    # 如果接收到的是短期限品种的TICK数据，记录TICK的price值
    if tick.cic_code == context.cs3.cic_code:
        context.cs3_price = tick.price

    # 获取短期限品种与中期限品种TICK的price字段的价差数据
    # short_middle_tick_spread_data = get_diff_history_n(first_cic_code=context.cs3.cic_code,
    #                                                    first_category='deal',
    #                                                    first_interval=context.cs3.interval,
    #                                                    first_field='price',
    #                                                    second_cic_code=context.cs2.cic_code,
    #                                                    second_category='deal',
    #                                                    second_interval=context.cs2.interval,
    #                                                    second_field='price',
    #                                                    count=2)

    # # 对获取到的数据进行填充操作
    # short_middle_tick_spread_data = format_data(short_middle_tick_spread_data['price-price'], method='fill')
    tick_data_1 = get_deal_n(cic_code=context.cs3.cic_code,
                                count=context.boll_period,
                                fields=['price'])
    tick_data_2 = get_deal_n(cic_code=context.cs2.cic_code,
                            count=context.boll_period,
                            fields=['price'])
    print(tick_data_1)
    tick_data_1 = pd.Series(tick_data_1['price'])
    print(tick_data_1)
    tick_data_1.fillna(method='ffill',inplace=True)
    print(tick_data_1)
    tick_data_1 = np.array(tick_data_1)
    tick_data_2 = pd.Series(tick_data_2['price'])
    tick_data_2.fillna(method='ffill',inplace=True)
    tick_data_2 = np.array(tick_data_2)
    print(tick_data_1)
    short_middle_tick_spread_data = tick_data_1 - tick_data_2

    # 获取长期限品种与中期限品种TICK的price字段的价差数据
    # long_middle_tick_spread_data = get_diff_history_n(first_cic_code=context.cs1.cic_code,
    #                                                   first_category='deal',
    #                                                   first_interval=context.cs1.interval,
    #                                                   first_field='price',
    #                                                   second_cic_code=context.cs2.cic_code,
    #                                                   second_category='deal',
    #                                                   second_interval=context.cs2.interval,
    #                                                   second_field='price',
    #                                                   count=2)

    # # 对获取到的数据进行填充操作
    # long_middle_tick_spread_data = format_data(long_middle_tick_spread_data['price-price'], method='fill')
    tick_data_3 = get_deal_n(cic_code=context.cs1.cic_code,
                                count=context.boll_period,
                                fields=['price'])
    tick_data_4 = get_deal_n(cic_code=context.cs2.cic_code,
                            count=context.boll_period,
                            fields=['price'])
    print(tick_data_3)
    tick_data_3 = pd.Series(tick_data_3['price'])
    print(tick_data_3)
    tick_data_3.fillna(method='ffill',inplace=True)
    print(tick_data_3)
    tick_data_3 = np.array(tick_data_3)
    tick_data_4 = pd.Series(tick_data_4['price'])
    tick_data_4.fillna(method='ffill',inplace=True)
    tick_data_4 = np.array(tick_data_4)
    print(tick_data_1)
    long_middle_tick_spread_data = tick_data_1 - tick_data_4

    # 如果填充后的价差数据的数据量不为0条且最后一条不为NaN值，则进行因子赋值
    if (len(short_middle_tick_spread_data) >= 1) and (len(long_middle_tick_spread_data) >= 1) and (
            not np.isnan(short_middle_tick_spread_data[-1])) and (not np.isnan(long_middle_tick_spread_data[-1])):
        # 因子赋值
        context.tick_spread = short_middle_tick_spread_data[-1] + long_middle_tick_spread_data[-1]

    # 如果填充后的价差数据的数据量完整且不含NaN值，则进行后续操作
    if (len(short_middle_tick_spread_data) == len(long_middle_tick_spread_data) == 2) and (
            sum(np.isnan(short_middle_tick_spread_data)) == 0) and (sum(np.isnan(long_middle_tick_spread_data)) == 0):
        # 计算三品种TICK的price字段的价差数据（短期限 + 长期限 - 2 * 中期限）
        tick_spread_data = short_middle_tick_spread_data + long_middle_tick_spread_data

        # 如果计算出的三品种收盘价的价差数据的布林通道上轨有值（上轨有值，则下轨也有值）且保存的三品种TICK的price字段有值，则进行后续操作
        if (context.cur_boll_upper is not None) and (context.cs1_price is not None) and (
                context.cs2_price is not None) and (context.cs3_price is not None):

            # 如果可以卖出价差且TICK的价差突破BAR价差的布林通道的上轨时，卖出价差
            if context.sell_flag and (tick_spread_data[-2] < context.cur_boll_upper < tick_spread_data[-1]):
                # 卖出价差即卖出长期限和短期限品种，买入中期限品种
                cs1_side = cs3_side = OrderSide.SELL
                cs2_side = OrderSide.BUY

                # 如果是首次开仓，下单量为参数设置的初始下单量
                if context.first_open:
                    cs1_trade_volume = context.cs1_trade_volume
                    cs2_trade_volume = context.cs2_trade_volume
                    cs3_trade_volume = context.cs3_trade_volume

                    # 首次开仓之后，将首次开仓标志置为False
                    context.first_open = False
                # 如果非首次开仓，下单量为参数设置的初始下单量的2倍（该策略为在市策略，2倍的下单量为平仓和反向开仓的下单量之和）
                else:
                    cs1_trade_volume = context.cs1_trade_volume * 2
                    cs2_trade_volume = context.cs2_trade_volume * 2
                    cs3_trade_volume = context.cs3_trade_volume * 2

                # 发出订单（卖出长期限品种），发单价格为保存的长期限品种TICK的price字段
                cs1_order_id = send_order(platform_code=context.cs1.platform,
                                          security_id=context.cs1.symbol,
                                          volume=cs1_trade_volume,
                                          price=context.cs1_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs1_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs1_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, cs1_side, context.cs1_price, cs1_trade_volume))

                # 发出订单（买入中期限品种），发单价格为保存的中期限品种TICK的price字段
                cs2_order_id = send_order(platform_code=context.cs2.platform,
                                          security_id=context.cs2.symbol,
                                          volume=cs2_trade_volume,
                                          price=context.cs2_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs2_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs2_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs2.cic_code, cs2_side, context.cs2_price, cs2_trade_volume))

                # 发出订单（卖出短期限品种），发单价格为保存的短期限品种TICK的price字段
                cs3_order_id = send_order(platform_code=context.cs3.platform,
                                          security_id=context.cs3.symbol,
                                          volume=cs3_trade_volume,
                                          price=context.cs3_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs3_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs3_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs3.cic_code, cs3_side, context.cs3_price, cs3_trade_volume))

                # 为防止价格连续突破布林上轨导致重复卖出价差，因此在卖出价差后需要更新买卖标志，后续只能买入价差，不能卖出价差
                context.buy_flag = True
                context.sell_flag = False

            # 如果可以买入价差且TICK的价差跌破BAR价差的布林通道的下轨时，买入价差
            if context.buy_flag and (tick_spread_data[-2] > context.cur_boll_lower > tick_spread_data[-1]):
                # 买入价差即买入长期限和短期限品种，卖出中期限品种
                cs1_side = cs3_side = OrderSide.BUY
                cs2_side = OrderSide.SELL

                # 如果是首次开仓，下单量为参数设置的初始下单量
                if context.first_open:
                    cs1_trade_volume = context.cs1_trade_volume
                    cs2_trade_volume = context.cs2_trade_volume
                    cs3_trade_volume = context.cs3_trade_volume

                    # 首次开仓之后，将首次开仓标志置为False
                    context.first_open = False
                # 如果非首次开仓，下单量为参数设置的初始下单量的2倍（该策略为在市策略，2倍的下单量为平仓和反向开仓的下单量之和）
                else:
                    cs1_trade_volume = context.cs1_trade_volume * 2
                    cs2_trade_volume = context.cs2_trade_volume * 2
                    cs3_trade_volume = context.cs3_trade_volume * 2

                # 发出订单（买入长期限品种），发单价格为保存的长期限品种TICK的price字段
                cs1_order_id = send_order(platform_code=context.cs1.platform,
                                          security_id=context.cs1.symbol,
                                          volume=cs1_trade_volume,
                                          price=context.cs1_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs1_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs1_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, cs1_side, context.cs1_price, cs1_trade_volume))

                # 发出订单（卖出中期限品种），发单价格为保存的中期限品种TICK的price字段
                cs2_order_id = send_order(platform_code=context.cs2.platform,
                                          security_id=context.cs2.symbol,
                                          volume=cs2_trade_volume,
                                          price=context.cs2_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs2_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs2_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs2.cic_code, cs2_side, context.cs2_price, cs2_trade_volume))

                # 发出订单（买入短期限品种），发单价格为保存的短期限品种TICK的price字段
                cs3_order_id = send_order(platform_code=context.cs3.platform,
                                          security_id=context.cs3.symbol,
                                          volume=cs3_trade_volume,
                                          price=context.cs3_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs3_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs3_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs3.cic_code, cs3_side, context.cs3_price, cs3_trade_volume))

                # 为防止价格连续跌破布林下轨导致重复买入价差，因此在买入价差后需要更新买卖标志，后续只能卖出价差，不能买入价差
                context.buy_flag = False
                context.sell_flag = True


def on_order(context, order):
    pass