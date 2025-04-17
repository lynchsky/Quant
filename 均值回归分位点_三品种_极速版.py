import numpy as np
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

    计算相同类别（现券或IRS）三个不同品种过去N根K-BAR的价差（短期限 + 长期限 - 2 * 中期限）及价差的75%分位点、50%分位点和25%分位点。
    当实时价差突破75%分位点时卖出价差，卖出价差后当实时价差跌破50%分位点时平仓买入价差；
    当实时价差跌破25%分位点时买入价差，买入价差后当实时价差突破50%分位点时平仓卖出价差。
    """

    # 接收参数
    context.quantile_period = add_parameter(int, 'quantile_period', '分位点计算周期')
    context.cs1_trade_volume = add_parameter(int, 'cs1_trade_volume', 'CS1下单量')
    context.cs2_trade_volume = add_parameter(int, 'cs2_trade_volume', 'CS2下单量')
    context.cs3_trade_volume = add_parameter(int, 'cs3_trade_volume', 'CS3下单量')

    # 添加因子
    context.tick_spread = add_factor(float, 'tick_spread', '实时价差')
    context.bar_spread = add_factor(float, 'bar_spread', 'BAR价差')
    context.percent_75 = add_factor(float, 'percent_75', '75%分位点')
    context.percent_50 = add_factor(float, 'percent_50', '50%分位点')
    context.percent_25 = add_factor(float, 'percent_25', '25%分位点')

    # 添加全局变量
    context.strategy_group = 'A'
    context.cur_percent_75 = None
    context.cur_percent_50 = None
    context.cur_percent_25 = None
    context.cs1_price = None
    context.cs2_price = None
    context.cs3_price = None
    context.flag_75 = False
    context.flag_25 = False


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
    #                                                   count=context.quantile_period)

    # # 对获取到的数据进行填充操作
    # short_middle_bar_spread_data = format_data(short_middle_bar_spread_data['close-close'], method='fill')

    bar_data_1 = get_bar_n(cic_code=context.cs6.cic_code,
                                interval=context.cs6.interval,
                                count=context.quantile_period,
                                fields=['close'])
    bar_data_2 = get_bar_n(cic_code=context.cs5.cic_code,
                            interval=context.cs5.interval,
                            count=context.quantile_period,
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
    #                                                  count=context.quantile_period)

    # # 对获取到的数据进行填充操作
    # long_middle_bar_spread_data = format_data(long_middle_bar_spread_data['close-close'], method='fill')

    bar_data_3 = get_bar_n(cic_code=context.cs4.cic_code,
                                interval=context.cs4.interval,
                                count=context.quantile_period,
                                fields=['close'])
    bar_data_4 = get_bar_n(cic_code=context.cs5.cic_code,
                            interval=context.cs5.interval,
                            count=context.quantile_period,
                            fields=['close'])
    bar_data_3 = pd.Series(bar_data_3['close'])
    bar_data_3.fillna(method='ffill',inplace=True)
    bar_data_3 = np.array(bar_data_3)
    bar_data_4 = pd.Series(bar_data_4['close'])
    bar_data_4.fillna(method='ffill',inplace=True)
    bar_data_4 = np.array(bar_data_4)
    long_middle_bar_spread_data = bar_data_3 - bar_data_4

    # 如果填充后的价差数据的数据量完整且不含NaN值，则进行后续操作
    if (len(short_middle_bar_spread_data) == len(long_middle_bar_spread_data) == context.quantile_period) and (
            sum(np.isnan(short_middle_bar_spread_data)) == 0) and (sum(np.isnan(long_middle_bar_spread_data)) == 0):
        # 计算三品种收盘价的价差数据（短期限 + 长期限 - 2 * 中期限）
        bar_spread_data = short_middle_bar_spread_data + long_middle_bar_spread_data

        # 计算三品种收盘价的价差数据的最大值和最小值
        max_bar_spread = max(bar_spread_data)
        min_bar_spread = min(bar_spread_data)

        # 计算三品种收盘价的价差数据的75%、50%、25%分位点并赋值给全局变量
        context.cur_percent_75 = min_bar_spread + (max_bar_spread - min_bar_spread) * 0.75
        context.cur_percent_50 = min_bar_spread + (max_bar_spread - min_bar_spread) * 0.50
        context.cur_percent_25 = min_bar_spread + (max_bar_spread - min_bar_spread) * 0.25

        # 因子赋值
        context.bar_spread = bar_spread_data[-1]
        context.percent_75 = context.cur_percent_75
        context.percent_50 = context.cur_percent_50
        context.percent_25 = context.cur_percent_25


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
                                count=context.quantile_period,
                                fields=['price'])
    tick_data_2 = get_deal_n(cic_code=context.cs2.cic_code,
                            count=context.quantile_period,
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
                                count=context.quantile_period,
                                fields=['price'])
    tick_data_4 = get_deal_n(cic_code=context.cs2.cic_code,
                            count=context.quantile_period,
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

        # 如果计算出的三品种收盘价的价差数据的50%分位点有值（50%分位点有值，则75%分位点和25%分位点也有值）且保存的三品种TICK的price字段有值，则进行后续操作
        if (context.cur_percent_50 is not None) and (context.cs1_price is not None) and (
                context.cs2_price is not None) and (context.cs3_price is not None):

            # TICK的价差突破BAR价差的75%分位值时，如未在75%分位开仓，则开仓卖出价差
            if (not context.flag_75) and (tick_spread_data[-2] < context.cur_percent_75 < tick_spread_data[-1]):
                # 卖出价差即卖出长期限和短期限品种，买入中期限品种
                cs1_side = cs3_side = OrderSide.SELL
                cs2_side = OrderSide.BUY

                # 发出订单（卖出长期限品种），发单价格为保存的长期限品种TICK的price字段
                cs1_order_id = send_order(platform_code=context.cs1.platform,
                                          security_id=context.cs1.symbol,
                                          volume=context.cs1_trade_volume,
                                          price=context.cs1_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs1_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs1_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, cs1_side, context.cs1_price, context.cs1_trade_volume))

                # 发出订单（买入中期限品种），发单价格为保存的中期限品种TICK的price字段
                cs2_order_id = send_order(platform_code=context.cs2.platform,
                                          security_id=context.cs2.symbol,
                                          volume=context.cs2_trade_volume,
                                          price=context.cs2_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs2_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs2_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs2.cic_code, cs2_side, context.cs2_price, context.cs2_trade_volume))

                # 发出订单（卖出短期限品种），发单价格为保存的短期限品种TICK的price字段
                cs3_order_id = send_order(platform_code=context.cs3.platform,
                                          security_id=context.cs3.symbol,
                                          volume=context.cs3_trade_volume,
                                          price=context.cs3_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs3_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs3_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs3.cic_code, cs3_side, context.cs3_price, context.cs3_trade_volume))

                # 在75%分位卖出价差后，将75%分位的开仓标志置为True
                context.flag_75 = True

            # 如已在75%分位开仓，且TICK的价差跌破BAR价差的50%分位值时，则平仓买入价差
            if context.flag_75 and (tick_spread_data[-2] > context.cur_percent_50 > tick_spread_data[-1]):
                # 买入价差即买入长期限和短期限品种，卖出中期限品种
                cs1_side = cs3_side = OrderSide.BUY
                cs2_side = OrderSide.SELL

                # 发出订单（买入长期限品种），发单价格为保存的长期限品种TICK的price字段
                cs1_order_id = send_order(platform_code=context.cs1.platform,
                                          security_id=context.cs1.symbol,
                                          volume=context.cs1_trade_volume,
                                          price=context.cs1_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs1_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs1_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, cs1_side, context.cs1_price, context.cs1_trade_volume))

                # 发出订单（卖出中期限品种），发单价格为保存的中期限品种TICK的price字段
                cs2_order_id = send_order(platform_code=context.cs2.platform,
                                          security_id=context.cs2.symbol,
                                          volume=context.cs2_trade_volume,
                                          price=context.cs2_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs2_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs2_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs2.cic_code, cs2_side, context.cs2_price, context.cs2_trade_volume))

                # 发出订单（买入短期限品种），发单价格为保存的短期限品种TICK的price字段
                cs3_order_id = send_order(platform_code=context.cs3.platform,
                                          security_id=context.cs3.symbol,
                                          volume=context.cs3_trade_volume,
                                          price=context.cs3_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs3_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs3_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs3.cic_code, cs3_side, context.cs3_price, context.cs3_trade_volume))

                # 75%分位的开仓已在50%分位平仓，将75%分位的开仓标志置为False
                context.flag_75 = False

            # TICK的价差跌破BAR价差的25%分位值时，如未在25%分位开仓，则开仓买入价差
            if (not context.flag_25) and (tick_spread_data[-2] > context.cur_percent_25 > tick_spread_data[-1]):
                # 买入价差即买入长期限和短期限品种，卖出中期限品种
                cs1_side = cs3_side = OrderSide.BUY
                cs2_side = OrderSide.SELL

                # 发出订单（买入长期限品种），发单价格为保存的长期限品种TICK的price字段
                cs1_order_id = send_order(platform_code=context.cs1.platform,
                                          security_id=context.cs1.symbol,
                                          volume=context.cs1_trade_volume,
                                          price=context.cs1_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs1_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs1_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, cs1_side, context.cs1_price, context.cs1_trade_volume))

                # 发出订单（卖出中期限品种），发单价格为保存的中期限品种TICK的price字段
                cs2_order_id = send_order(platform_code=context.cs2.platform,
                                          security_id=context.cs2.symbol,
                                          volume=context.cs2_trade_volume,
                                          price=context.cs2_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs2_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs2_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs2.cic_code, cs2_side, context.cs2_price, context.cs2_trade_volume))

                # 发出订单（买入短期限品种），发单价格为保存的短期限品种TICK的price字段
                cs3_order_id = send_order(platform_code=context.cs3.platform,
                                          security_id=context.cs3.symbol,
                                          volume=context.cs3_trade_volume,
                                          price=context.cs3_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs3_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs3_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs3.cic_code, cs3_side, context.cs3_price, context.cs3_trade_volume))

                # 在25%分位买入价差后，将25%分位的开仓标志置为True
                context.flag_25 = True

            # 如已在25%分位开仓，且TICK的价差突破BAR价差的50%分位值时，则平仓卖出价差
            if context.flag_25 and (tick_spread_data[-2] < context.cur_percent_50 < tick_spread_data[-1]):
                # 卖出价差即卖出长期限和短期限品种，买入中期限品种
                cs1_side = cs3_side = OrderSide.SELL
                cs2_side = OrderSide.BUY

                # 发出订单（卖出长期限品种），发单价格为保存的长期限品种TICK的price字段
                cs1_order_id = send_order(platform_code=context.cs1.platform,
                                          security_id=context.cs1.symbol,
                                          volume=context.cs1_trade_volume,
                                          price=context.cs1_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs1_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs1_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, cs1_side, context.cs1_price, context.cs1_trade_volume))

                # 发出订单（买入中期限品种），发单价格为保存的中期限品种TICK的price字段
                cs2_order_id = send_order(platform_code=context.cs2.platform,
                                          security_id=context.cs2.symbol,
                                          volume=context.cs2_trade_volume,
                                          price=context.cs2_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs2_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs2_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs2.cic_code, cs2_side, context.cs2_price, context.cs2_trade_volume))

                # 发出订单（卖出短期限品种），发单价格为保存的短期限品种TICK的price字段
                cs3_order_id = send_order(platform_code=context.cs3.platform,
                                          security_id=context.cs3.symbol,
                                          volume=context.cs3_trade_volume,
                                          price=context.cs3_price,
                                          order_type=OrderType.LIMIT,
                                          side=cs3_side,
                                          strategy_group=context.strategy_group)

                # 如果发单成功，打印相应信息
                if cs3_order_id != 0:
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs3.cic_code, cs3_side, context.cs3_price, context.cs3_trade_volume))

                # 25%分位的开仓已在50%分位平仓，将25%分位的开仓标志置为False
                context.flag_25 = False


def on_order(context, order):
    pass