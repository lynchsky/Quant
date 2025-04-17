from MyTT import *
from main import global_signal


# 反转类指标实现
# signal为1表示买入，-1表示卖出，0表示持有



def RMI_signal(df):
    df.loc[(REF(df["RMI"], 1) <= 30) & (df["RMI"] > 30), "RMI_signal"] = 1
    df.loc[(REF(df["RMI"], 1) >= 70) & (df["RMI"] < 70), "RMI_signal"] = -1
    df['RMI_signal']=df['RMI_signal'].fillna(method='ffill')
    df['RMI_signal'] = df['RMI_signal'].fillna(0)
    return df



def RMI_df(df, N = 7):
    close = df["close"]
    # 研报上的公式后面仍是REF(close, 1)
    df["RMI"] = SMA(MAX(close - REF(close, 4), 0), N, 1) / SMA(ABS(close - REF(close, 4)), N, 1) * 100
    
    if global_signal:
        df = RMI_signal(df)
    
    return df


def RSI_signal(df):
    df.loc[(REF(df["RSI"], 1) <= 30) & (df["RSI"] > 30), "RSI_signal"] = 1
    df.loc[(REF(df["RSI"], 1) >= 70) & (df["RSI"] < 70), "RSI_signal"] = -1
    df['RSI_signal']=df['RSI_signal'].fillna(method='ffill')
    df['RSI_signal'] = df['RSI_signal'].fillna(0)
    return df

def RSI_df(df, N = 6):
    close = df["close"]

    close_up = IF(close > REF(close, 1), close - REF(close, 1), 0)
    close_down = IF(close < REF(close, 1), REF(close, 1) - close, 0)
    close_up_sma = SMA(close_up, N, 1)
    close_down_sma = SMA(close_down, N, 1)
    df["RSI"] = close_up_sma / (close_up_sma + close_down_sma) * 100

    if global_signal:
        df = RSI_signal(df)

    return df


def ROC_signal(df):
    # roc上穿0.05买入
    df.loc[(REF(df["ROC"], 1) <= 0.05) & (df["ROC"] > 0.05), "ROC_signal"] = 1
    # roc下穿-0.05卖出
    df.loc[(REF(df["ROC"], 1) >= -0.05) & (df["ROC"] < -0.05), "ROC_signal"] = -1
    df['ROC_signal']=df['ROC_signal'].fillna(method='ffill')
    df['ROC_signal'] = df['ROC_signal'].fillna(0)
    return df

def ROC_df(df):
    close = df["close"]
    df["ROC"] = (close - REF(close, 100)) / REF(close, 100)
    if global_signal:
        df = ROC_signal(df)
    return df


def STC_signal(df):
    # STC上穿25买入
    df.loc[(REF(df["STC"], 1) <= 25) & (df["STC"] > 25), "STC_signal"] = 1
    # STC下穿75卖出
    df.loc[(REF(df["STC"], 1) >= 75) & (df["STC"] < 75), "STC_signal"] = -1
    df['STC_signal']=df['STC_signal'].fillna(method='ffill')
    df['STC_signal'] = df['STC_signal'].fillna(0)
    return df

def STC_df(df, N1 = 23, N2 = 50, N = 40):
    close = df["close"]
    macdx = EMA(close, N1) - EMA(close, N2)
    v1 = MIN(macdx, N)
    v2 = MAX(macdx, N) - v1
    fk = IF(v2 > 0, (macdx - v1) / v2 * 100, REF(fk, 1))
    fd = SMA(fk, N, 1)
    v3 = MIN(fd, N)
    v4 = MAX(fd, N) - v3
    sk = IF(v4 > 0, (fd - v3) / v4 * 100, REF(sk, 1))
    df["STC"] = SMA(sk, N, 1)
    if global_signal:
        df = STC_signal(df)
    return df


def RVI_signal(df):
    # RVI上穿30买入
    df.loc[(REF(df["RVI"], 1) <= 30) & (df["RVI"] > 30), "RVI_signal"] = 1
    # RVI下穿70卖出
    df.loc[(REF(df["RVI"], 1) >= 70) & (df["RVI"] < 70), "RVI_signal"] = -1
    df['RVI_signal']=df['RVI_signal'].fillna(method='ffill')
    df['RVI_signal'] = df['RVI_signal'].fillna(0)
    return df

def RVI_df(df, N1 = 10, N2 = 20):
    close = df["close"]
    std = STD(close, N1)
    ustd = SUM(IF(close > REF(close, 1), std, 0), N2)
    dstd = SUM(IF(close < REF(close, 1), std, 0), N2)
    df["RVI"] = ustd / (ustd + dstd) * 100
    if global_signal:
        df = RVI_signal(df)
    return df


def RSIS_signal(df):
    # 阈值可以改变
    df.loc[(REF(df["RSISMA"], 1) <= 30) & (df["RSISMA"] > 30), "RSIS_signal"] = 1
    df.loc[(REF(df["RSISMA"], 1) >= 70) & (df["RSISMA"] < 70), "RSIS_signal"] = -1
    df['RSIS_signal']=df['RSIS_signal'].fillna(method='ffill')
    df['RSIS_signal'] = df['RSIS_signal'].fillna(0)
    return df

def RSIS_df(df, N = 120, M = 20):
    close = df["close"]
    close_diff_pos = IF(close > REF(close, 1), close - REF(close, 1), 0)
    rsi = SMA(close_diff_pos, 1) / SMA(ABS(close - REF(close, 1)), N, 1) * 100
    rsis = (rsi - MIN(rsi, N)) / (MAX(rsi, N) - MIN(rsi, N)) * 100
    df["RSISMA"] = MA(rsis, M)

    if global_signal:
        df = RSIS_signal(df)
    return df