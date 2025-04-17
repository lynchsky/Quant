from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码和BAR级别仅供参考，可根据需要进行修改）

    行情码           类型       频率     下单平台           是否撮合    数据清洗    全域变量
    200215.CFXO     逐笔成交    0        X-BondT+1         是          原始        cs1
    200016.CFXO     逐笔成交    0        X-BondT+1         是          原始        cs2

    策略逻辑

    国债流动性差于国开债，所以较多作为配置盘，国开债多是交易盘。
    牛市的时候，国开债收益率下降的幅度会比国债大，适合买国开债卖国债；熊市的时候，国开债收益率上升的幅度会比国债大，适合卖国开债买国债。

    隐含税率 = (国开债收益率 - 国债收益率) / 国开债收益率    (国开债和国债的差异叫隐含税率)
    临界点 = 自定义参数，例如15%

    当隐含税率下穿临界点时，买入国开债，卖出国债；当隐含税率上穿临界点时，卖出国开债，买入国债。
    """
    # 接收参数
    context.critical_point = add_parameter(float, 'critical_point', '临界点')
    context.trade_volume_develop_bond = add_parameter(int, 'trade_volume_develop_bond', '下单量_国开债')
    context.trade_volume_bond = add_parameter(int, 'trade_volume_bond', '下单量_国债')

    # 添加因子
    context.implied_tax_rate = add_factor(float, 'implied_tax_rate', '隐含税率')

    # 添加全局变量
    context.strategy_group = 'A'
    context.yield_develop_bond = None
    context.yield_bond = None
    context.price_develop_bond = None
    context.price_bond = None
    context.pre_implied_tax_rate = None
    context.first_open = True


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    # 如果接收到的是国开债的TICK数据，记录TICK的tick_yield和price值
    if tick.cic_code == context.cs1.cic_code:
        if tick.tick_yield is not None:
            context.yield_develop_bond = tick.tick_yield
            context.price_develop_bond = tick.price

    # 如果接收到的是国债的TICK数据，记录TICK的tick_yield和price值
    if tick.cic_code == context.cs2.cic_code:
        if tick.tick_yield is not None:
            context.yield_bond = tick.tick_yield
            context.price_bond = tick.price

    # 如果保存的国开债和国债的tick_yield有值，则进行后续操作
    if (context.yield_develop_bond is not None) and (context.yield_bond is not None):
        # 计算隐含税率（为避免除数为0时计算报错，需对除数进行非0判断）
        if abs(context.yield_develop_bond) > 0.00000001:
            # 隐含税率公式为：隐含税率 = (国开债收益率 - 国债收益率) / 国开债收益率
            implied_tax_rate = (context.yield_develop_bond - context.yield_bond) / context.yield_develop_bond

            # 因子赋值
            context.implied_tax_rate = implied_tax_rate

            # 如果保存的pre_implied_tax_rate有值，则进行后续操作
            if context.pre_implied_tax_rate is not None:
                # 如果隐含税率跌破临界点，则买入国开债，卖出国债
                if context.pre_implied_tax_rate > context.critical_point > implied_tax_rate:
                    # 如果是首次开仓，下单量为参数设置的初始下单量
                    if context.first_open:
                        trade_volume_develop_bond = context.trade_volume_develop_bond
                        trade_volume_bond = context.trade_volume_bond

                        # 首次开仓之后，将首次开仓标志置为False
                        context.first_open = False
                    # 如果非首次开仓，下单量为参数设置的初始下单量的2倍（该策略为在市策略，2倍的下单量为平仓和反向开仓的下单量之和）
                    else:
                        trade_volume_develop_bond = context.trade_volume_develop_bond * 2
                        trade_volume_bond = context.trade_volume_bond * 2

                    # 发出订单（买入国开债），发单价格为保存的国开债TICK的price字段
                    cs1_order_id = send_order(platform_code=context.cs1.platform,
                                              security_id=context.cs1.symbol,
                                              volume=trade_volume_develop_bond,
                                              price=context.price_develop_bond,
                                              order_type=OrderType.LIMIT,
                                              side=OrderSide.BUY,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs1_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs1.cic_code, OrderSide.BUY, context.price_develop_bond, trade_volume_develop_bond))

                    # 发出订单（卖出国债），发单价格为保存的国债TICK的price字段
                    cs2_order_id = send_order(platform_code=context.cs2.platform,
                                              security_id=context.cs2.symbol,
                                              volume=trade_volume_bond,
                                              price=context.price_bond,
                                              order_type=OrderType.LIMIT,
                                              side=OrderSide.SELL,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs2_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs2.cic_code, OrderSide.SELL, context.price_bond, trade_volume_bond))

                # 如果隐含税率突破临界点，则卖出国开债，买入国债
                if context.pre_implied_tax_rate < context.critical_point < implied_tax_rate:
                    # 如果是首次开仓，下单量为参数设置的初始下单量
                    if context.first_open:
                        trade_volume_develop_bond = context.trade_volume_develop_bond
                        trade_volume_bond = context.trade_volume_bond

                        # 首次开仓之后，将首次开仓标志置为False
                        context.first_open = False
                    # 如果非首次开仓，下单量为参数设置的初始下单量的2倍（该策略为在市策略，2倍的下单量为平仓和反向开仓的下单量之和）
                    else:
                        trade_volume_develop_bond = context.trade_volume_develop_bond * 2
                        trade_volume_bond = context.trade_volume_bond * 2

                    # 发出订单（卖出国开债），发单价格为保存的国开债TICK的price字段
                    cs1_order_id = send_order(platform_code=context.cs1.platform,
                                              security_id=context.cs1.symbol,
                                              volume=trade_volume_develop_bond,
                                              price=context.price_develop_bond,
                                              order_type=OrderType.LIMIT,
                                              side=OrderSide.SELL,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs1_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs1.cic_code, OrderSide.SELL, context.price_develop_bond, trade_volume_develop_bond))

                    # 发出订单（买入国债），发单价格为保存的国债TICK的price字段
                    cs2_order_id = send_order(platform_code=context.cs2.platform,
                                              security_id=context.cs2.symbol,
                                              volume=trade_volume_bond,
                                              price=context.price_bond,
                                              order_type=OrderType.LIMIT,
                                              side=OrderSide.BUY,
                                              strategy_group=context.strategy_group)

                    # 如果发单成功，打印相应信息
                    if cs2_order_id != 0:
                        print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                            context.cs2.cic_code, OrderSide.BUY, context.price_bond, trade_volume_bond))

            # 保存pre_implied_tax_rate的值，供后续使用
            context.pre_implied_tax_rate = implied_tax_rate


def on_order(context, order):
    pass