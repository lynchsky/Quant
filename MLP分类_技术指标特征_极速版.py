import pandas as pd
import talib
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from ComstarApi import *


def init(context):
    """
    行情设置格式（行情码和BAR级别仅供参考，可根据需要进行修改）

    行情码          类型     频率    下单平台     是否撮合    数据清洗    全域变量
    210215.CFXO    K-Bar    1min    X-BondT+1    是         原始        cs1

    策略逻辑

    运用MLP模型预测下一根K线是阳线还是阴线，如果预测结果是阳线，则在下一根K线开盘时买入，如果预测结果是阴线，则在下一根K线开盘时卖出。
    该策略训练模型时使用的特征除了K-Bar的原始信息外还包括SAR指标以及收盘价的RSI指标。

    撮合模型

    自定义撮合模型 -> 下一行情撮合 -> 开盘价
    """

    # 接收参数
    context.af_step = add_parameter(float, 'af_step', '加速因子步长')  # SAR指标该参数默认值一般为0.02
    context.max_af = add_parameter(float, 'max_af', '加速因子最大值')  # SAR指标该参数默认值一般为0.2
    context.rsi_period = add_parameter(int, 'rsi_period', 'RSI计算周期')
    context.test_size = add_parameter(float, 'test_size', '测试集划分比例')
    context.trade_volume = add_parameter(int, 'trade_volume', '目标持仓量')

    # 添加因子
    context.predict_result = add_factor(int, 'predict_result', '机器学习预测结果')  # 1为阳线、0为阴线（阴线包括十字星线）

    # 添加全局变量
    context.strategy_group = 'A'
    context.bar_number = 500

    context.preprocess_model = None  # 保存训练好的预处理模型
    context.model = None  # 保存训练好的机器学习模型


def on_bar(context, bar):
    # 策略刚启动还没有机器学习模型时需要先训练预处理模型和机器学习模型
    if context.model is None:
        # 获取数据
        bar_data = get_bar_n(cic_code=context.cs1.cic_code,
                             interval=context.cs1.interval,
                             count=context.bar_number,
                             fields=['open', 'high', 'low', 'close', 'time',
                                     'open_yield', 'high_yield', 'low_yield', 'close_yield'])
        # 填充数据
        # bar_data = {k: format_data(bar_data[k], method='fill') if k != 'time' else bar_data[k] for k in bar_data}
        bar_data = {k: np.array(bar_data[k]) if k != 'time' else bar_data[k] for k in bar_data}

        # 将填充后的数据转换为DataFrame并设置time列为索引且按照索引升序排序
        bar_data = pd.DataFrame(bar_data).set_index('time').sort_index(ascending=True)

        # 添加SAR指标特征
        bar_data['SAR'] = talib.SAR(bar_data['high'].values,
                                    bar_data['low'].values,
                                    acceleration=context.af_step,
                                    maximum=context.max_af)

        # 添加RSI指标特征
        bar_data['RSI'] = talib.RSI(bar_data['close'].values,
                                    timeperiod=context.rsi_period)

        # 去除含有NaN元素的行
        bar_data = bar_data.dropna(how='any')

        # 构造标签，收盘价大于开盘价的标签设置为1，否则设置为0
        bar_data['up_or_down'] = 0
        mask = bar_data['open'] < bar_data['close']
        bar_data.loc[mask, 'up_or_down'] = 1

        # 为预测下一根K线是阳线还是阴线，需将标签向下平移一个周期并进行填充
        bar_data['up_or_down'] = bar_data['up_or_down'].shift(periods=1).bfill()

        # 选择特征和标签
        feature = bar_data[['open', 'high', 'low', 'close', 'open_yield', 'high_yield', 'low_yield', 'close_yield',
                            'SAR', 'RSI']].values
        label = bar_data['up_or_down'].values

        # 划分训练集和测试集
        feature_train, feature_test, label_train, label_test = train_test_split(feature, label,
                                                                                test_size=context.test_size)

        # 初始化预处理模型
        preprocess_model = StandardScaler()

        # 训练预处理模型
        preprocess_model.fit(feature_train)

        # 运用训练好的预处理模型预处理训练集和测试集
        feature_train_std = preprocess_model.transform(feature_train)
        feature_test_std = preprocess_model.transform(feature_test)

        # 初始化机器学习模型
        mlp = MLPClassifier()

        # 训练机器学习模型
        mlp.fit(feature_train_std, label_train)

        # 运用训练好的机器学习模型对测试集进行预测
        label_test_predict = mlp.predict(feature_test_std)

        # 计算并打印机器学习模型的auc指标
        print(roc_auc_score(label_test, label_test_predict))

        # 保存训练好的预处理模型和机器学习模型
        context.preprocess_model = preprocess_model
        context.model = mlp

    # 如果机器学习模型已经训练完毕，则根据训练好的预处理模型和机器学习模型进行预测并进行发单操作
    else:
        # 获取数据
        bar_data = get_bar_n(cic_code=context.cs1.cic_code,
                             interval=context.cs1.interval,
                             count=max(context.rsi_period, 1) + 1,
                             fields=['high', 'low', 'close'])

        # 填充数据
        # bar_data = {k: format_data(bar_data[k], method='fill') for k in bar_data}
        bar_data = {k: np.array(bar_data[k]) for k in bar_data}

        # 计算SAR指标特征
        sar = talib.SAR(bar_data['high'],
                        bar_data['low'],
                        acceleration=context.af_step,
                        maximum=context.max_af)

        # 计算RSI指标特征
        rsi = talib.RSI(bar_data['close'],
                        timeperiod=context.rsi_period)

        # 构造特征
        feature = [[bar.open, bar.high, bar.low, bar.close, bar.open_yield, bar.high_yield, bar.low_yield,
                    bar.close_yield, sar[-1], rsi[-1]]]

        # 运用预处理模型对构造的特征进行预处理
        feature_std = context.preprocess_model.transform(feature)

        # 运用机器学习模型进行预测
        predict_result = context.model.predict(feature_std)

        # 因子赋值
        context.predict_result = predict_result[0]

        # 获取当前仓位信息
        position = get_position(security_id=context.cs1.symbol,
                                strategy_group=context.strategy_group)

        # 计算持仓量
        hold_volume = position.hold_volume * position.side.value

        # 如果预测下一根K线为阳线且当前未持有多头仓位，则发出买入信号
        if predict_result[0] == 1 and hold_volume <= 0:
            # 发单前撤销所有未成交单
            cancel_all_orders()

            # 计算应发单量
            volume = abs(hold_volume) + context.trade_volume

            # 发出买单
            order_id = send_order(platform_code=context.cs1.platform,
                                  security_id=context.cs1.symbol,
                                  volume=volume,
                                  price=bar.close,
                                  order_type=OrderType.LIMIT,
                                  side=OrderSide.BUY,
                                  strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, OrderSide.BUY, bar.close, volume))

        # 如果预测下一根K线为阴线（阴线包括十字星线）且当前未持有空头头寸，则发出卖出信号
        elif predict_result[0] == 0 and hold_volume >= 0:
            # 发单前撤销所有未成交单
            cancel_all_orders()

            # 计算应发单量
            volume = hold_volume + context.trade_volume

            # 发出卖单
            order_id = send_order(platform_code=context.cs1.platform,
                                  security_id=context.cs1.symbol,
                                  volume=volume,
                                  price=bar.close,
                                  order_type=OrderType.LIMIT,
                                  side=OrderSide.SELL,
                                  strategy_group=context.strategy_group)

            # 如果发单成功，打印相应信息
            if order_id != 0:
                print('{0}发单成功，发单方向为：{1}，发单价格为：{2}，发单量为：{3}'.format(
                    context.cs1.cic_code, OrderSide.SELL, bar.close, volume))


def on_tick(context, tick):
    pass


def on_order(context, order):
    pass