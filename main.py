# ----By ky

# ----talib库和pandas_ta库，只提供部分指标实现

# import talib
# a = talib.get_functions()
# print(a)

# import pandas as pd
# import pandas_ta as ta
# df = pd.DataFrame()
# print(df.ta.indicators())
# ----





# ---- 全局变量
global_signal = True    # 是否生成交易信号
# ----






import pandas as pd
import matplotlib.pyplot as plt

from trend_indicator import *
from reversal_indicator import *

# for test，只需要修改indicator为对应的指标名即可
if __name__ == "__main__":
    df = pd.read_csv(r"C:\Users\keke\Desktop\量化\代码\中债指数数据\7-10年.csv")      # 读取数据，收盘价的列名为close
    
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df.set_index('date', inplace=True)

    df.index = df.index.strftime('%Y-%m-%d')

    df = df["2010-01-04":"2024-02-01"]


    indicator = "RSIH"


    indicator_df = indicator + "_df"  # 指标函数名，指标名+_df为指标的df实现，不加df则可能调用MyTT.py中的指标函数，为series实现
    indicator_singal = indicator + "_signal"


    if indicator_df in globals():
        df = globals()[indicator_df](df)
    else:
        print("指标不存在")
        exit(0)


    print(df)
    # df[["close", indicator]].plot()   #注意有些指标如TEMA需要修改indicator



    print("买入天数:", df[indicator_singal].eq(1).sum())
    print("卖出天数:", df[indicator_singal].eq(-1).sum())
    print("持有天数:", df[indicator_singal].eq(0).sum())

    # # 标记买入和卖出点
    # buy_points = df[df[indicator_singal] == 1]
    # sell_points = df[df[indicator_singal] == -1]
    # plt.scatter(buy_points.index, buy_points['close'], color='red', marker='^', s=30, label='Buy')
    # plt.scatter(sell_points.index, sell_points['close'], color='green', marker='v', s=30, label='Sell')


    # plt.legend()
    # plt.show()










