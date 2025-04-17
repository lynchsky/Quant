import numpy as np

from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码仅供参考，可根据需要进行修改）

    行情码          类型       频率    下单平台     是否撮合    数据清洗    全域变量
    210215.CFXO    逐笔成交    0       X-BondT+1    是         原始        cs1
    T2203.CFF      逐笔成交    0       中金所       否         原始        cs2

    策略逻辑

    根据国债期货近期的区间突破情况，发出现券方向信号。如果急涨或者高位维持，持多头现券；如果急跌或者低位维持，持空头现券。

    注：撮合模型应选择 自定义撮合模型 -> 下一行情撮合 -> 收盘价。
    """

    # 接收参数
    context.monitor_minutes = add_parameter(int, 'monitor_minutes', '监控分钟数')
    context.trade_volume = add_parameter(int, 'trade_volume', '下单量')

    # 添加因子
    context.future_price = add_factor(float, 'future_price', '国债期货价格')
    context.future_up_threshold = add_factor(float, 'future_up_threshold', '国债期货上临界点')
    context.future_down_threshold = add_factor(float, 'future_down_threshold', '国债期货下临界点')

    # 添加全局变量
    context.strategy_group = 'A'
    context.should_have_volume = 0


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    # 如果接收到的是国债期货的tick数据，则获取监控时间段的历史数据，计算上下临界点，并根据最新价与上下临界点的关系计算目标持仓量
    if tick.cic_code == context.cs2.cic_code:
        # 获取监控时间段内国债期货成交价的历史数据
        tick_data = get_deal_n(cic_code=context.cs2.cic_code,
                               count=20,
                               fields=['price'])

        # 对获取到的数据进行填充操作
        # tick_data = format_data(tick_data['price'], method='fill')
        tick_data = np.array(tick_data['price'])

        # 如果填充后的数据长度大于0且填充后的数据不含NaN值，则进行后续操作
        if (len(tick_data) > 0) and (sum(np.isnan(tick_data)) == 0):
            # 计算监控时间段内国债期货的最高成交价和最低成交价
            max_price = max(tick_data)
            min_price = min(tick_data)

            # 计算上下临界点（最高价之下20%为上临界点，最低价之上20%为下临界点）
            future_up_threshold = max_price - 0.2 * (max_price - min_price)
            future_down_threshold = min_price + 0.2 * (max_price - min_price)

            # 因子赋值
            context.future_price = tick.price
            context.future_up_threshold = future_up_threshold
            context.future_down_threshold = future_down_threshold

            # 如果国债期货最新价在上临界点之上，目标持仓为多单
            if tick.price > future_up_threshold:
                context.should_have_volume = context.trade_volume

            # 如果国债期货最新价在下临界点之下，目标持仓为空单
            elif tick.price < future_down_threshold:
                context.should_have_volume = -context.trade_volume

            # 如果国债期货最新价在上下临界点之间，目标仓位为不持仓
            else:
                context.should_have_volume = 0

    # 如果接收到的是现券的tick数据，则进行后续操作
    if tick.cic_code == context.cs1.cic_code:
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

            # 发出订单，其中发单价格为当前tick的成交价，发单量为计算出的发单量volume，发单方向为根据应发单量得出的side
            order_id = send_order(platform_code=context.cs1.platform,
                                  security_id=context.cs1.symbol,
                                  volume=volume,
                                  price=tick.price,
                                  order_type=OrderType.LIMIT,
                                  side=side,
                                  strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, side, tick.price, volume))


def on_order(context, order):
    pass