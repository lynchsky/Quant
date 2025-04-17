import numpy as np
import talib

from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码和BAR级别仅供参考，可根据需要进行修改）

    行情码          类型     频率    下单平台     是否撮合    数据清洗    全域变量
    210215.CFXO    K-Bar    1min    X-BondT+1    是         原始        cs1
    T2203.CFF      K-Bar    1min    中金所       否         原始        cs2

    策略逻辑

    由于国债期货行情较现券行情密集，可在国债期货对应的MACD金叉时买入现券，在国债期货对应的MACD死叉时卖出现券。
    """

    # 接收参数
    context.short_period = add_parameter(int, 'short_period', 'MACD快线周期')
    context.long_period = add_parameter(int, 'long_period', 'MACD慢线周期')
    context.macd_period = add_parameter(int, 'macd_period', 'MACD平滑周期')
    context.trade_volume = add_parameter(int, 'trade_volume', '下单量')

    # 添加因子
    context.DIFF = add_factor(float, 'DIFF', 'DIFF指标')
    context.DEA = add_factor(float, 'DEA', 'DEA指标')
    context.MACD = add_factor(float, 'MACD', 'MACD指标')

    # 添加全局变量
    context.strategy_group = 'A'
    context.should_have_volume = 0
    context.pre_diff = None
    context.pre_dea = None


def on_bar(context, bar):
    # 如果接收到的是国债期货的Bar数据，则获取历史数据、计算技术指标并根据技术指标计算现券的目标持仓量
    if bar.cic_code == context.cs2.cic_code:
        # 获取国债期货收盘价的历史数据
        bar_data = get_bar_n(cic_code=context.cs2.cic_code,
                             interval=context.cs2.interval,
                             count=(context.long_period + context.macd_period - 1),
                             fields=['close'])

        # 对获取到的数据进行填充操作
        # bar_data = format_data(bar_data['close'], method='fill')
        bar_data = np.array(bar_data['close'])

        # 如果填充后的数据量完整且填充后的数据不含NaN值，则进行后续操作
        if (len(bar_data) == (context.long_period + context.macd_period - 1)) and (sum(np.isnan(bar_data)) == 0):
            # 调用talib计算MACD指标
            diff, dea, macd = talib.MACD(bar_data,
                                         fastperiod=context.short_period,
                                         slowperiod=context.long_period,
                                         signalperiod=context.macd_period)

            # 因子赋值
            context.DIFF = diff[-1]
            context.DEA = dea[-1]
            context.MACD = macd[-1]

            # 如果保存的pre_diff和pre_dea均不为None值，则进行后续操作
            if (context.pre_diff is not None) and (context.pre_dea is not None):
                # MACD金叉时，目标持仓应为多单
                if (context.pre_diff < context.pre_dea) and (diff[-1] > dea[-1]):
                    context.should_have_volume = context.trade_volume

                # MACD死叉时，目标持仓应为空单
                elif (context.pre_diff > context.pre_dea) and (diff[-1] < dea[-1]):
                    context.should_have_volume = -context.trade_volume

            # 保存pre_diff和pre_dea的值，供后续使用
            context.pre_diff = diff[-1]
            context.pre_dea = dea[-1]

    # 如果当前接收到的是现券的Bar数据，则进行后续操作
    else:
        # 获取当前仓位信息
        position = get_position(security_id=context.cs1.symbol, strategy_group=context.strategy_group)

        # 计算当前持仓（有正负，其中正负代表持仓方向）
        current_have_volume = position.hold_volume * position.side.value

        # 计算为达到目标仓位的应发单量（有正负，其中正负代表发单方向）
        should_trade_volume = context.should_have_volume - current_have_volume

        # 如果计算出的应发单量不为0，则进行后续操作
        if should_trade_volume != 0:
            # 发单前撤销所有未成交单
            cancel_all_orders()

            # 如果计算出的应发单量大于0，则发单方向为多单
            if should_trade_volume > 0:
                side = OrderSide.BUY

            # 如果计算出的应发单量小于0，则发单方向为空单
            else:
                side = OrderSide.SELL

            # 计算发单量（无正负，即真实发单量）
            volume = abs(should_trade_volume)

            # 发出订单，其中发单价格为当前bar的收盘价，发单方向和发单量为计算出的side和volume值
            order_id = send_order(platform_code=context.cs1.platform,
                                  security_id=context.cs1.symbol,
                                  volume=volume,
                                  price=bar.close,
                                  order_type=OrderType.LIMIT,
                                  side=side,
                                  strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, side, bar.close, volume))


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass