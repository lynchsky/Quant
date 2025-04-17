import datetime

from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码仅供参考，可根据需要进行修改）

    行情码          类型       频率    下单平台     是否撮合    数据清洗    全域变量
    210215.CFXO    逐笔成交    0       X-BondT+1    是         原始        cs1
    T2203.CFF      逐笔成交    0       中金所       否         原始        cs2

    策略逻辑

    在极速变化的走势中，国债期货行情往往领先于现券行情一定时间。因此当国债期货在过去N秒内上涨或下跌大于等于M时，可买入或卖出现券并在持有N秒后平仓。
    """

    # 接收参数
    context.lead_seconds = add_parameter(int, 'lead_seconds', '领先秒数')
    context.base_range = add_parameter(float, 'base_range', '涨跌基准幅度')
    context.trade_volume = add_parameter(int, 'trade_volume', '下单量')

    # 添加全局变量
    context.t_dict = {}
    context.strategy_group = 'A'
    context.trade_time = None
    context.trade_side = None


def on_bar(context, bar):
    pass


def on_tick(context, tick):
    # 如果接收到的是国债期货的tick数据，则构建键值对并将其添加到t_dict字典中
    if tick.cic_code == context.cs2.cic_code:
        # 转换国债期货tick对应的行情时间的格式为datetime类型
        transact_time = datetime.datetime.strptime(tick.transact_time, '%Y-%m-%d %H:%M:%S.%f')

        # 以行情时间为键，行情价格为值构建键值对并添加到t_dict字典中
        context.t_dict[transact_time] = tick.price

        # 筛选t_dict字典，使其只保存最新一定秒数（由lead_seconds参数设定）的数据
        context.t_dict = {k: context.t_dict[k] for k in context.t_dict.keys() if k >= (
                transact_time - datetime.timedelta(seconds=context.lead_seconds))}

    # 如果t_dict字典不为空，且接收到的是现券的tick数据，则进行后续操作
    if context.t_dict and (tick.cic_code == context.cs1.cic_code):
        # 计算t_dict字典中数据的价格波动区间，以及价格波动区间的10%分位点和90%分位点
        temp_range = max(context.t_dict.values()) - min(context.t_dict.values())
        max_level = min(context.t_dict.values()) + 0.9 * temp_range
        min_level = min(context.t_dict.values()) + 0.1 * temp_range

        # 如果计算出的价格波动区间达到一定标准（由参数base_range设定），则进行后续操作
        if temp_range >= context.base_range:
            # 国债期货极速上涨（即t_dict字典中最远的价格在10%分位点之下，最近的价格在90%分位点之上）时现券开仓方向为买入
            if (context.t_dict[max(context.t_dict.keys())] >= max_level) and (
                    context.t_dict[min(context.t_dict.keys())] <= min_level):
                side = OrderSide.BUY

            # 国债期货极速下跌（即t_dict字典中最远的价格在90%分位点之上，最近的价格在10%分位点之下）时现券开仓方向为卖出
            elif (context.t_dict[max(context.t_dict.keys())] <= min_level) and (
                    context.t_dict[min(context.t_dict.keys())] >= max_level):
                side = OrderSide.SELL

            # 如果国债期货即未极速上涨也未极速下跌，则不开仓
            else:
                side = OrderSide.NKNOWN

            # 如果记录的发单时间为初始值或者已被重置（说明没有未平仓仓位）且计算出的side不为OrderSide.NKNOWN，则进行开仓操作
            if (context.trade_time is None) and (side != OrderSide.NKNOWN):
                # 发出订单，其中发单价格为当前tick的成交价，发单方向为计算出的side的方向
                order_id = send_order(platform_code=context.cs1.platform,
                                      security_id=context.cs1.symbol,
                                      volume=context.trade_volume,
                                      price=tick.price,
                                      order_type=OrderType.LIMIT,
                                      side=side,
                                      strategy_group=context.strategy_group)

                # 如果发单成功，记录一些状态并打印相应信息
                if order_id != 0:
                    # 记录发单时间
                    context.trade_time = datetime.datetime.strptime(tick.transact_time, '%Y-%m-%d %H:%M:%S.%f')

                    # 记录发单方向
                    context.trade_side = side

                    # 打印发单信息
                    print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                        context.cs1.cic_code, side, tick.price, context.trade_volume))

        # 如果记录的发单时间未被重置（说明有未平仓仓位）且当前时间与记录的发单时间之差已经超过一定秒数（由lead_seconds参数设定），则进行平仓操作
        if (context.trade_time is not None) and (datetime.datetime.strptime(
                tick.transact_time, '%Y-%m-%d %H:%M:%S.%f') >= context.trade_time + datetime.timedelta(
                seconds=context.lead_seconds)):
            # 如果记录的发单方向为买入，则平仓方向为卖出
            if context.trade_side == OrderSide.BUY:
                side = OrderSide.SELL

            # 如果记录的发单方向为卖出，则平仓方向为买入
            else:
                side = OrderSide.BUY

            # 发出订单，其中发单价格为当前tick的成交价，发单方向为根据记录的发单方向映射出的平仓方向
            order_id = send_order(platform_code=context.cs1.platform,
                                  security_id=context.cs1.symbol,
                                  volume=context.trade_volume,
                                  price=tick.price,
                                  order_type=OrderType.LIMIT,
                                  side=side,
                                  strategy_group=context.strategy_group)

            # 如果发单成功，重置一些状态并打印相应信息
            if order_id != 0:
                # 重置发单时间为None值，代表不存在未平仓仓位
                context.trade_time = None

                # 重置发单方向为None值，代表不存在未平仓仓位
                context.trade_side = None

                # 打印发单信息
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, side, tick.price, context.trade_volume))


def on_order(context, order):
    pass