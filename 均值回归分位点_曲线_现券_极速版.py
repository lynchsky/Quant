import numpy as np
import pandas as pd
from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码和BAR级别仅供参考，可根据需要进行修改）

    行情码           类型       频率    下单平台     是否撮合    数据清洗    全域变量
    220203.CFXO     K-Bar      1min    X-BondT+1    是         原始        cs1
    220201.CFXO     K-Bar      1min    X-BondT+1    是         原始        cs2
    YCCDB5Y.CFXM    逐笔成交    0       CFETS        否         原始        cs3
    YCCDB1Y.CFXM    逐笔成交    0       CFETS        否         原始        cs4

    策略逻辑

    计算现券两个不同品种对应曲线过去N个值的价差及价差的75%分位点、50%分位点和25%分位点。
    当现券BAR的价差突破75%分位点时卖出价差，卖出价差后当现券BAR的价差跌破50%分位点时平仓买入价差；
    当现券BAR的价差跌破25%分位点时买入价差，买入价差后当现券BAR的价差突破50%分位点时平仓卖出价差。
    """

    # 接收参数
    context.quantile_period = add_parameter(int, 'quantile_period', '分位点计算周期')
    context.cs1_trade_volume = add_parameter(int, 'cs1_trade_volume', 'CS1下单量')
    context.cs2_trade_volume = add_parameter(int, 'cs2_trade_volume', 'CS2下单量')

    # 添加因子
    context.bar_spread = add_factor(float, 'bar_spread', 'BAR价差')
    context.curve_spread = add_factor(float, 'curve_spread', '曲线价差')
    context.percent_75 = add_factor(float, 'percent_75', '75%分位点')
    context.percent_50 = add_factor(float, 'percent_50', '50%分位点')
    context.percent_25 = add_factor(float, 'percent_25', '25%分位点')

    # 添加全局变量
    context.strategy_group = 'A'
    context.cs1_close = None
    context.cs2_close = None
    context.flag_75 = False
    context.flag_25 = False


def on_bar(context, bar):
    # 如果接收到的是品种一的BAR数据，记录BAR的收盘价
    if bar.cic_code == context.cs1.cic_code:
        context.cs1_close = bar.close

    # 如果接收到的是品种二的BAR数据，记录BAR的收盘价
    if bar.cic_code == context.cs2.cic_code:
        context.cs2_close = bar.close

    # 获取品种一与品种二的收盘价收益率的价差数据
    # bar_spread_data = get_diff_history_n(first_cic_code=context.cs1.cic_code,
    #                                      first_category='deal',
    #                                      first_interval=context.cs1.interval,
    #                                      first_field='close_yield',
    #                                      second_cic_code=context.cs2.cic_code,
    #                                      second_category='deal',
    #                                      second_interval=context.cs2.interval,
    #                                      second_field='close_yield',
    #                                      count=2)

    # # 对获取到的数据进行填充操作
    # bar_spread_data = format_data(bar_spread_data['close_yield-close_yield'], method='fill')

    bar_data_1 = get_bar_n(cic_code=context.cs1.cic_code,
                                interval=context.cs1.interval,
                                count=context.quantile_period,
                                fields=['close_yield'])
    bar_data_2 = get_bar_n(cic_code=context.cs2.cic_code,
                            interval=context.cs2.interval,
                            count=context.quantile_period,
                            fields=['close_yield'])
    bar_data_1 = pd.Series(bar_data_1['close_yield'])
    bar_data_1.fillna(method='ffill',inplace=True)
    bar_data_1 = np.array(bar_data_1)
    bar_data_2 = pd.Series(bar_data_2['close_yield'])
    bar_data_2.fillna(method='ffill',inplace=True)
    bar_data_2 = np.array(bar_data_2)
    bar_spread_data = bar_data_1 - bar_data_2

    # 如果填充后的价差数据的数据量不为0条且最后一条不为NaN值，则进行因子赋值
    if (len(bar_spread_data) >= 1) and (not np.isnan(bar_spread_data[-1])):
        # 因子赋值
        context.bar_spread = bar_spread_data[-1]

    # 如果填充后的价差数据的数据量完整且不含NaN值，则进行后续操作
    if (len(bar_spread_data) == 2) and (sum(np.isnan(bar_spread_data)) == 0):
        # 获取曲线一的last_yield数据
        cs3_curve_data = get_market_data_n(cic_code=context.cs3.cic_code,
                                           count=context.quantile_period,
                                           fields=['last_yield'])

        # 对获取到的数据进行填充操作
        cs3_curve_data = format_data(cs3_curve_data['last_yield'], method='fill')

        # 获取曲线二的last_yield数据
        cs4_curve_data = get_market_data_n(cic_code=context.cs4.cic_code,
                                           count=context.quantile_period,
                                           fields=['last_yield'])

        # 对获取到的数据进行填充操作
        cs4_curve_data = format_data(cs4_curve_data['last_yield'], method='fill')

        # 如果获取到曲线数据的数据量完整且不含NaN值，则进行后续操作
        if (len(cs3_curve_data) == len(cs4_curve_data) == context.quantile_period) and (
                sum(np.isnan(cs3_curve_data)) == 0) and (sum(np.isnan(cs4_curve_data)) == 0):
            # 计算曲线的价差数据
            curve_spread_data = cs3_curve_data - cs4_curve_data

            # 计算曲线的价差数据的最大值和最小值
            max_curve_spread = max(curve_spread_data)
            min_curve_spread = min(curve_spread_data)

            # 计算曲线的价差数据的75%、50%、25%分位点并赋值给全局变量
            cur_percent_75 = min_curve_spread + (max_curve_spread - min_curve_spread) * 0.75
            cur_percent_50 = min_curve_spread + (max_curve_spread - min_curve_spread) * 0.50
            cur_percent_25 = min_curve_spread + (max_curve_spread - min_curve_spread) * 0.25

            # 因子赋值
            context.curve_spread = curve_spread_data[-1]
            context.percent_75 = cur_percent_75
            context.percent_50 = cur_percent_50
            context.percent_25 = cur_percent_25

            # 如果保存的品种一和品种二的收盘价有值，则进行后续操作
            if (context.cs1_close is not None) and (context.cs2_close is not None):

                # 现券BAR的价差突破曲线价差的75%分位值时，如未在75%分位开仓，则开仓卖出价差
                if (not context.flag_75) and (bar_spread_data[-2] < cur_percent_75 < bar_spread_data[-1]):
                    # 卖出价差即买入品种一，卖出品种二（由于现券是用收益率计算的价差且是用价格发单，因此发单方向与价差买卖方向相反）
                    cs1_side = OrderSide.BUY
                    cs2_side = OrderSide.SELL

                    # 发出订单（买入品种一），发单价格为保存的品种一BAR的收盘价
                    cs1_order_id = send_order(platform_code=context.cs1.platform,
                                              security_id=context.cs1.symbol,
                                              volume=context.cs1_trade_volume,
                                              price=context.cs1_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs1_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs1_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs1.cic_code, cs1_side, context.cs1_close, context.cs1_trade_volume))

                    # 发出订单（卖出品种二），发单价格为保存的品种二BAR的收盘价
                    cs2_order_id = send_order(platform_code=context.cs2.platform,
                                              security_id=context.cs2.symbol,
                                              volume=context.cs2_trade_volume,
                                              price=context.cs2_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs2_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs2_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs2.cic_code, cs2_side, context.cs2_close, context.cs2_trade_volume))

                    # 在75%分位卖出价差后，将75%分位的开仓标志置为True
                    context.flag_75 = True

                # 如已在75%分位开仓，且现券BAR的价差跌破曲线价差的50%分位值时，则平仓买入价差
                if context.flag_75 and (bar_spread_data[-2] > cur_percent_50 > bar_spread_data[-1]):
                    # 买入价差即卖出品种一，买入品种二（由于现券是用收益率计算的价差且是用价格发单，因此发单方向与价差买卖方向相反）
                    cs1_side = OrderSide.SELL
                    cs2_side = OrderSide.BUY

                    # 发出订单（卖出品种一），发单价格为保存的品种一BAR的收盘价
                    cs1_order_id = send_order(platform_code=context.cs1.platform,
                                              security_id=context.cs1.symbol,
                                              volume=context.cs1_trade_volume,
                                              price=context.cs1_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs1_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs1_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs1.cic_code, cs1_side, context.cs1_close, context.cs1_trade_volume))

                    # 发出订单（买入品种二），发单价格为保存的品种二BAR的收盘价
                    cs2_order_id = send_order(platform_code=context.cs2.platform,
                                              security_id=context.cs2.symbol,
                                              volume=context.cs2_trade_volume,
                                              price=context.cs2_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs2_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs2_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs2.cic_code, cs2_side, context.cs2_close, context.cs2_trade_volume))

                    # 75%分位的开仓已在50%分位平仓，将75%分位的开仓标志置为False
                    context.flag_75 = False

                # 现券BAR的价差跌破曲线价差的25%分位值时，如未在25%分位开仓，则开仓买入价差
                if (not context.flag_25) and (bar_spread_data[-2] > cur_percent_25 > bar_spread_data[-1]):
                    # 买入价差即卖出品种一，买入品种二（由于现券是用收益率计算的价差且是用价格发单，因此发单方向与价差买卖方向相反）
                    cs1_side = OrderSide.SELL
                    cs2_side = OrderSide.BUY

                    # 发出订单（卖出品种一），发单价格为保存的品种一BAR的收盘价
                    cs1_order_id = send_order(platform_code=context.cs1.platform,
                                              security_id=context.cs1.symbol,
                                              volume=context.cs1_trade_volume,
                                              price=context.cs1_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs1_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs1_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs1.cic_code, cs1_side, context.cs1_close, context.cs1_trade_volume))

                    # 发出订单（买入品种二），发单价格为保存的品种二BAR的收盘价
                    cs2_order_id = send_order(platform_code=context.cs2.platform,
                                              security_id=context.cs2.symbol,
                                              volume=context.cs2_trade_volume,
                                              price=context.cs2_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs2_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs2_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs2.cic_code, cs2_side, context.cs2_close, context.cs2_trade_volume))

                    # 在25%分位买入价差后，将25%分位的开仓标志置为True
                    context.flag_25 = True

                # 如已在25%分位开仓，且现券BAR的价差突破曲线价差的50%分位值时，则平仓卖出价差
                if context.flag_25 and (bar_spread_data[-2] < cur_percent_50 < bar_spread_data[-1]):
                    # 卖出价差即买入品种一，卖出品种二（由于现券是用收益率计算的价差且是用价格发单，因此发单方向与价差买卖方向相反）
                    cs1_side = OrderSide.BUY
                    cs2_side = OrderSide.SELL

                    # 发出订单（买入品种一），发单价格为保存的品种一BAR的收盘价
                    cs1_order_id = send_order(platform_code=context.cs1.platform,
                                              security_id=context.cs1.symbol,
                                              volume=context.cs1_trade_volume,
                                              price=context.cs1_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs1_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs1_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs1.cic_code, cs1_side, context.cs1_close, context.cs1_trade_volume))

                    # 发出订单（卖出品种二），发单价格为保存的品种二BAR的收盘价
                    cs2_order_id = send_order(platform_code=context.cs2.platform,
                                              security_id=context.cs2.symbol,
                                              volume=context.cs2_trade_volume,
                                              price=context.cs2_close,
                                              order_type=OrderType.LIMIT,
                                              side=cs2_side,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs2_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs2.cic_code, cs2_side, context.cs2_close, context.cs2_trade_volume))

                    # 25%分位的开仓已在50%分位平仓，将25%分位的开仓标志置为False
                    context.flag_25 = False


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass