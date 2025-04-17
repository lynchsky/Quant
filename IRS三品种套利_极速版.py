from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码仅供参考，可根据需要进行修改）

    行情码                 类型       频率    下单平台          是否撮合    数据清洗    全域变量
    FR007_5YC-CFXO        报价行情    0       X-Swap实时承接    是         原始        cs1
    FR007_1YC-CFXO        报价行情    0       X-Swap实时承接    是         原始        cs2
    FR007_1YC*5YC-CFXO    报价行情    0       X-Swap实时承接    是         原始        cs3

    策略逻辑

    该策略适用于IRS，需同时订阅两个同一标的不同期限的IRS品种以及这两个IRS的期差品种（cs1为长期限IRS，cs2为短期限IRS，cs3为期差IRS）。
    当期差品种的offer_price小于长期限IRS的bid_price与短期限IRS的offer_price之差时，买入期差品种和短期限IRS、卖出长期限IRS；
    当期差品种的bid_price大于长期限IRS的offer_price与短期限IRS的bid_price之差时，卖出期差品种和短期限IRS、买入长期限IRS。
    """

    # 接收参数
    context.cs1_trade_volume = add_parameter(int, 'cs1_trade_volume', 'CS1下单量')
    context.cs2_trade_volume = add_parameter(int, 'cs2_trade_volume', 'CS2下单量')
    context.cs3_trade_volume = add_parameter(int, 'cs3_trade_volume', 'CS3下单量')

    # 添加因子
    context.cs1_bid_cs2_offer = add_factor(float, 'cs1_bid_cs2_offer', '长期限bid减短期限offer')
    context.cs1_offer_cs2_bid = add_factor(float, 'cs1_offer_cs2_bid', '长期限offer减短期限bid')
    context.cs3_bid_price = add_factor(float, 'cs3_bid_price', '期差bid')
    context.cs3_offer_price = add_factor(float, 'cs3_offer_price', '期差offer')

    # 添加全局变量
    context.strategy_group = 'A'
    context.cs1_bid = None
    context.cs1_offer = None
    context.cs2_bid = None
    context.cs2_offer = None
    context.cs3_bid = None
    context.cs3_offer = None


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    # 记录长期限IRS的第一档的bid_price和offer_price
    if len(tick.bid_price)==0 or len(tick.offer_price)==0:
        return
    print(f'tick.bid_price:{tick.bid_price}')
    if tick.cic_code == context.cs1.cic_code:
        context.cs1_bid = tick.bid_price[0]
        context.cs1_offer = tick.offer_price[0]

    # 记录短期限IRS的第一档的bid_price和offer_price
    if tick.cic_code == context.cs2.cic_code:
        context.cs2_bid = tick.bid_price[0]
        context.cs2_offer = tick.offer_price[0]

    # 记录期差IRS的第一档的bid_price和offer_price
    if tick.cic_code == context.cs3.cic_code:
        context.cs3_bid = tick.bid_price[0]
        context.cs3_offer = tick.offer_price[0]

    # 如果记录的长期限IRS、短期限IRS、期差IRS的第一档的bid_price和offer_price均不为None值，再进行后续操作
    if (context.cs1_bid is not None) and (context.cs1_offer is not None) and (context.cs2_bid is not None) and (
            context.cs2_offer is not None) and (context.cs3_bid is not None) and (context.cs3_offer is not None):
        # 计算长期限IRS的第一档的bid_price和短期限IRS的第一档的offer_price的价差
        cs1_bid_cs2_offer = context.cs1_bid - context.cs2_offer
        # 计算长期限IRS的第一档的offer_price和短期限IRS的第一档的bid_price的价差
        cs1_offer_cs2_bid = context.cs1_offer - context.cs2_bid

        # 因子赋值
        context.cs1_bid_cs2_offer = cs1_bid_cs2_offer
        context.cs1_offer_cs2_bid = cs1_offer_cs2_bid
        context.cs3_bid_price = context.cs3_bid
        context.cs3_offer_price = context.cs3_offer

        # 当期差品种的offer_price小于长期限IRS的bid_price与短期限IRS的offer_price之差时，买入期差品种和短期限IRS、卖出长期限IRS
        if context.cs3_offer < cs1_bid_cs2_offer:
            # 发出长期限IRS卖单，发单价格为记录的长期限IRS的第一档的bid_price
            cs1_order_id = send_order(platform_code=context.cs1.platform,
                                      security_id=context.cs1.symbol,
                                      volume=context.cs1_trade_volume,
                                      price=context.cs1_bid,
                                      order_type=OrderType.LIMIT,
                                      side=OrderSide.SELL,
                                      strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if cs1_order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, OrderSide.SELL, context.cs1_bid, context.cs1_trade_volume))

            # 发出短期限IRS买单，发单价格为记录的短期限IRS的第一档的offer_price
            cs2_order_id = send_order(platform_code=context.cs2.platform,
                                      security_id=context.cs2.symbol,
                                      volume=context.cs2_trade_volume,
                                      price=context.cs2_offer,
                                      order_type=OrderType.LIMIT,
                                      side=OrderSide.BUY,
                                      strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if cs2_order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs2.cic_code, OrderSide.BUY, context.cs2_offer, context.cs2_trade_volume))

            # 发出期差IRS买单，发单价格为记录的期差IRS的第一档的offer_price
            cs3_order_id = send_order(platform_code=context.cs3.platform,
                                      security_id=context.cs3.symbol,
                                      volume=context.cs3_trade_volume,
                                      price=context.cs3_offer,
                                      order_type=OrderType.LIMIT,
                                      side=OrderSide.BUY,
                                      strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if cs3_order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs3.cic_code, OrderSide.BUY, context.cs3_offer, context.cs3_trade_volume))

        # 当期差品种的bid_price大于长期限IRS的offer_price与短期限IRS的bid_price之差时，卖出期差品种和短期限IRS、买入长期限IRS
        if context.cs3_bid > cs1_offer_cs2_bid:
            # 发出长期限IRS买单，发单价格为记录的长期限IRS的第一档的offer_price
            cs1_order_id = send_order(platform_code=context.cs1.platform,
                                      security_id=context.cs1.symbol,
                                      volume=context.cs1_trade_volume,
                                      price=context.cs1_offer,
                                      order_type=OrderType.LIMIT,
                                      side=OrderSide.BUY,
                                      strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if cs1_order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, OrderSide.BUY, context.cs1_offer, context.cs1_trade_volume))

            # 发出短期限IRS卖单，发单价格为记录的短期限IRS的第一档的bid_price
            cs2_order_id = send_order(platform_code=context.cs2.platform,
                                      security_id=context.cs2.symbol,
                                      volume=context.cs2_trade_volume,
                                      price=context.cs2_bid,
                                      order_type=OrderType.LIMIT,
                                      side=OrderSide.SELL,
                                      strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if cs2_order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs2.cic_code, OrderSide.SELL, context.cs2_bid, context.cs2_trade_volume))

            # 发出期差IRS卖单，发单价格为记录的期差IRS的第一档的bid_price
            cs3_order_id = send_order(platform_code=context.cs3.platform,
                                      security_id=context.cs3.symbol,
                                      volume=context.cs3_trade_volume,
                                      price=context.cs3_bid,
                                      order_type=OrderType.LIMIT,
                                      side=OrderSide.SELL,
                                      strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if cs3_order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs3.cic_code, OrderSide.SELL, context.cs3_bid, context.cs3_trade_volume))


def on_order(context, order):
    pass