from MyTT import *
from main import global_signal


# 趋势类指标实现
# signal为1表示买入，-1表示卖出，0表示持有


def BBI_signal(df):
    # 收盘价上穿BBI买入
    df.loc[(REF(df["close"], 1) < REF(df["BBI"], 1)) & (df["close"] > df["BBI"]), "BBI_signal"] = 1
    # 收盘价下穿BBI卖出
    df.loc[(REF(df["close"], 1) > REF(df["BBI"], 1)) & (df["close"] < df["BBI"]), "BBI_signal"] = -1
    # print(df["BBI_signal"].eq(1).sum())
    # print(df["BBI_signal"].eq(0).sum())
    # print(df["BBI_signal"].eq(-1).sum())
    df['BBI_signal']=df['BBI_signal'].fillna(method='ffill')
    # print(df["BBI_signal"].eq(1).sum())
    # print(df["BBI_signal"].eq(0).sum())
    # print(df["BBI_signal"].eq(-1).sum())
    df['BBI_signal'] = df['BBI_signal'].fillna(0)
    return df

def BBI_df(df):
    close = df["close"]
    df["BBI"] = (MA(close, 3) + MA(close, 9) + MA(close, 12) + MA(close, 15)) / 4
    if global_signal:
        df = BBI_signal(df)
    return df


def VIDYA_signal(df):
    # 收盘价上穿VIDYA买入
    df.loc[(REF(df["close"], 1) <= REF(df["VIDYA"], 1)) & (df["close"] > df["VIDYA"]), "VIDYA_signal"] = 1
    # 收盘价下穿VIDYA卖出
    df.loc[(REF(df["close"], 1) >= REF(df["VIDYA"], 1)) & (df["close"] < df["VIDYA"]), "VIDYA_signal"] = -1
    df['VIDYA_signal']=df['VIDYA_signal'].fillna(method='ffill')
    df['VIDYA_signal'] = df['VIDYA_signal'].fillna(0)
    return df

def VIDYA_df(df, N = 10):
    close = df["close"]
    v1 = ABS(close - REF(close, N)) / SUM(ABS(close - REF(close, 1)), N)
    df["VIDYA"] = v1 * close + (1 - v1) * REF(close, 1)

    if global_signal:
        df = VIDYA_signal(df)
    return df


def RSIH_signal(df):
    # RSIH上穿0买入
    df.loc[(REF(df["RSIH"], 1) <= 0) & (df["RSIH"] > 0), "RSIH_signal"] = 1
    # RSIH下穿0卖出
    df.loc[(REF(df["RSIH"], 1) >= 0) & (df["RSIH"] < 0), "RSIH_signal"] = -1
    df['RSIH_signal']=df['RSIH_signal'].fillna(method='ffill')
    df['RSIH_signal'] = df['RSIH_signal'].fillna(0)
    return df


def RSIH_df(df, N1 = 15, N2 = 70):
    close = df["close"]
    close_diff_pos = IF(close > REF(close, 1), close - REF(close, 1), 0)
    rsi = SMA(close_diff_pos, N1, 1) / SMA(ABS(close - REF(close, 1)), N1, 1) * 100
    rsi_sig = EMA(rsi, N2)
    df["RSIH"] = rsi - rsi_sig
    if global_signal:
        df = RSIH_signal(df)
    return df


def WMA_signal(df):
    # 收盘价上穿WMA买入
    df.loc[(REF(df["close"], 1) <= REF(df["WMA"], 1)) & (df["close"] > df["WMA"]), "WMA_signal"] = 1
    # 收盘价下穿WMA卖出
    df.loc[(REF(df["close"], 1) >= REF(df["WMA"], 1)) & (df["close"] < df["WMA"]), "WMA_signal"] = -1
    df['WMA_signal']=df['WMA_signal'].fillna(method='ffill')
    df['WMA_signal'] = df['WMA_signal'].fillna(0)
    return df

def WMA_df(df, N = 20):
    close = df["close"]
    df["WMA"] = WMA(close, N)
    if global_signal:
        df = WMA_signal(df)
    return df


def T3_signal(df):
    # 收盘价上穿T3买入
    df.loc[(REF(df["close"], 1) <= REF(df["T3"], 1)) & (df["close"] > df["T3"]), "T3_signal"] = 1
    # 收盘价下穿T3卖出
    df.loc[(REF(df["close"], 1) >= REF(df["T3"], 1)) & (df["close"] < df["T3"]), "T3_signal"] = -1
    df['T3_signal']=df['T3_signal'].fillna(method='ffill')
    df['T3_signal'] = df['T3_signal'].fillna(0)
    return df


def T3_df(df, N = 20, VA = 0.5):
    close = df["close"]
    t1 = EMA(close, N) * (1 + VA) - EMA(EMA(close, N), N) * VA
    t2 = EMA(t1, N) * (1 + VA) - EMA(EMA(t1, N), N) * VA
    df["T3"] = EMA(t2, N) * (1 + VA) - EMA(EMA(t2, N), N) * VA
    if global_signal:
        df = T3_signal(df)
    return df

def DEMA_signal(df):
    """
    DEMA signal
    """
    df.loc[(REF(df["close"], 1) <= REF(df["DEMA"], 1)) & (df["close"] > df["DEMA"]), "DEMA_signal"] = 1
    df.loc[(REF(df["close"], 1) >= REF(df["DEMA"], 1)) & (df["close"] < df["DEMA"]), "DEMA_signal"] = -1
    df['DEMA_signal']=df['DEMA_signal'].fillna(method='ffill')
    df['DEMA_signal'] = df['DEMA_signal'].fillna(0)
    return df

def DEMA_df(df, N = 60):
    """
    Double Exponential Moving Average
    """
    close = df["close"]
    ema_n = EMA(close, N)
    df["DEMA"] = 2 * ema_n - EMA(ema_n, N)
    
    if global_signal:
        df = DEMA_signal(df)
    
    return df

def KAMA_signal(df):
    """
    KAMA signal
    """
    df.loc[(REF(df["close"], 1) <= REF(df["KAMA"], 1)) & (df["close"] > df["KAMA"]), "KAMA_signal"] = 1
    df.loc[(REF(df["close"], 1) >= REF(df["KAMA"], 1)) & (df["close"] < df["KAMA"]), "KAMA_signal"] = -1
    df['KAMA_signal']=df['KAMA_signal'].fillna(method='ffill')
    df['KAMA_signal'] = df['KAMA_signal'].fillna(0)
    return df

def KAMA_df(df, N = 10, M1 = 2, M2 = 30):
    """
    KAMA
    """
    close = df["close"]
    direction = close - REF(close, N)
    volatility = SUM(ABS(close - REF(close, 1)), N)
    er = direction / volatility
    fast = 2 / (M1 + 1)
    slow = 2 / (M2 + 1)
    smooth = er * (fast - slow) + slow
    cof = smooth ** 2
    df["KAMA"] = close * cof + REF(df["KAMA"], 1) * (1 - cof)
    
    if global_signal:
        df = KAMA_signal(df)
    
    return df


def MADisplayced_signal(df):
    """
    MADisplayced signal
    """
    df.loc[(REF(df["close"], 1) <= REF(df["MADisplayced"], 1)) & (df["close"] > df["MADisplayced"]), "MADisplayced_signal"] = 1
    df.loc[(REF(df["close"], 1) >= REF(df["MADisplayced"], 1)) & (df["close"] < df["MADisplayced"]), "MADisplayced_signal"] = -1
    df['MADisplayced_signal']=df['MADisplayced_signal'].fillna(method='ffill')
    df['MADisplayced_signal'] = df['MADisplayced_signal'].fillna(0)
    return df


def MADisplayced_df(df, N = 20, M = 10):
    
    close = df["close"]
    ma_close = MA(close, N)
    df["MADisplayced"] = REF(ma_close, M)

    if global_signal:
        df = MADisplayced_signal(df)
    return df

def PO_signal(df):
    """
    PO signal
    """
    df.loc[(REF(df["PO"], 1) <= 0) & (df["PO"] > 0), "PO_signal"] = 1
    df.loc[(REF(df["PO"], 1) >= 0) & (df["PO"] < 0), "PO_signal"] = -1
    df['PO_signal']=df['PO_signal'].fillna(method='ffill')
    df['PO_signal'] = df['PO_signal'].fillna(0)
    return df


def PO_df(df):
    
    close = df["close"]
    df["PO"] = (EMA(close, 9) - EMA(close, 26)) / EMA(close, 26) * 100

    if global_signal:
        df = PO_signal(df)
    return df


def TMA_signal(df):
    """
    TMA signal
    """
    df.loc[(REF(df["close"], 1) <= REF(df["TMA"], 1)) & (df["close"] > df["TMA"]), "TMA_signal"] = 1
    df.loc[(REF(df["close"], 1) >= REF(df["TMA"], 1)) & (df["close"] < df["TMA"]), "TMA_signal"] = -1
    df['TMA_signal']=df['TMA_signal'].fillna(method='ffill')
    df['TMA_signal'] = df['TMA_signal'].fillna(0)
    return df

def TMA_df(df, N = 20):
    """
    Triangular Moving Average
    """
    close = df["close"]
    df["TMA"] = MA(MA(close, N), N)
    if global_signal:
        df = TMA_signal(df)
    return df
    
def MTM_signal(df):
    """
    MTM signal
    """
    df.loc[(REF(df["MTM"], 1) <= 0) & (df["MTM"] > 0), "MTM_signal"] = 1
    df.loc[(REF(df["MTM"], 1) >= 0) & (df["MTM"] < 0), "MTM_signal"] = -1
    df['MTM_signal']=df['MTM_signal'].fillna(method='ffill')
    df['MTM_signal'] = df['MTM_signal'].fillna(0)
    return df

def MTM_df(df, N = 60):
    """
    MTM
    """
    close = df["close"]
    df["MTM"] = close - REF(close, N)
    if global_signal:
        df = MTM_signal(df)
    return df

def CMO_signal(df):
    """
    CMO signal
    """
    df.loc[(REF(df["CMO"], 1) <= 30) & (df["CMO"] > 30), "CMO_signal"] = 1
    df.loc[(REF(df["CMO"], 1) >= -30) & (df["CMO"] < -30), "CMO_signal"] = -1
    df['CMO_signal']=df['CMO_signal'].fillna(method='ffill')
    df['CMO_signal'] = df['CMO_signal'].fillna(0)
    return df

def CMO_df(df, N = 20):
    """
    Chande Momentum Oscillator
    """
    close = df["close"]
    su = SUM(MAX(close - REF(close, 1), 0), N)
    sd = SUM(MAX(REF(close, 1) - close, 0), N)
    df["CMO"] = (su - sd) / (su + sd) * 100
    if global_signal:
        df = CMO_signal(df)
    return df    

def PPO_signal(df):
    """
    PPO signal
    """
    df.loc[(REF(df["PPO"], 1) <= REF(df["PPO_sig"], 1)) & (df["PPO"] > df["PPO_sig"]), "PPO_signal"] = 1
    df.loc[(REF(df["PPO"], 1) >= REF(df["PPO_sig"], 1)) & (df["PPO"] < df["PPO_sig"]), "PPO_signal"] = -1
    df['PPO_signal']=df['PPO_signal'].fillna(method='ffill')
    df['PPO_signal'] = df['PPO_signal'].fillna(0)
    return df

def PPO_df(df, N1 = 12, N2 = 26, M = 9):
    """
    Percentage Price Oscillator
    """
    close = df["close"]
    df["PPO"] = (EMA(close, N1) - EMA(close, N2)) / EMA(close, N2)
    df["PPO_sig"] = EMA(df["PPO"], M)
    if global_signal:
        df = PPO_signal(df)
    return df


def TRIX_signal(df):
    df.loc[(REF(df["TRIX"], 1) <= 0) & (df["TRIX"] > 0), "TRIX_signal"] = 1
    df.loc[(REF(df["TRIX"], 1) >= 0) & (df["TRIX"] < 0), "TRIX_signal"] = -1
    df['TRIX_signal']=df['TRIX_signal'].fillna(method='ffill')
    df['TRIX_signal'] = df['TRIX_signal'].fillna(0)
    return df


def TRIX_df(df, N):
    """
    TRIX
    """
    close = df["close"]
    triple_ema = EMA(EMA(EMA(close, N), N), N)
    df["TRIX"] = (triple_ema - REF(triple_ema, 1)) / REF(triple_ema, 1)
    if global_signal:
        df = TRIX_signal(df)
    return df


def DZRSI_single(df):
    """
    DZRSI signal
    """
    df.loc[(REF(df["RSI_MA"], 1) <= REF(df["RSI_UPPER"], 1)) & (df["RSI_MA"] > df["RSI_UPPER"]), "DZRSI_signal"] = 1
    df.loc[(REF(df["RSI_MA"], 1) >= REF(df["RSI_LOWER"], 1)) & (df["RSI_MA"] < df["RSI_LOWER"]), "DZRSI_signal"] = -1
    df['DZRSI_signal']=df['DZRSI_signal'].fillna(method='ffill')
    df['DZRSI_signal'] = df['DZRSI_signal'].fillna(0)
    return df

def DZRSI_df(df, N = 40, M = 3, param = 1):
    """
    DZRSI
    """
    close = df["close"]
    rsi = RSI(close, N)
    df["RSI_MIDDLE"] = MA(rsi, N)
    df["RSI_UPPER"] = df["RSI_MIDDLE"] + STD(rsi, N) * param
    df["RSI_LOWER"] = df["RSI_MIDDLE"] - STD(rsi, N) * param
    df["RSI_MA"] = MA(rsi, M)
    
    if global_signal:
        df = DZRSI_single(df)

    return df



def EXPMA_signal(df):
    """
    EXPMA signal
    """
    df.loc[(REF(df["EMA1"], 1) <= REF(df["EMA2"], 1)) & (df["EMA1"] > df["EMA2"]), "EXPMA_signal"] = 1
    df.loc[(REF(df["EMA1"], 1) >= REF(df["EMA2"], 1)) & (df["EMA1"] < df["EMA2"]), "EXPMA_signal"] = -1
    df['EXPMA_signal']=df['EXPMA_signal'].fillna(method='ffill')
    df['EXPMA_signal'] = df['EXPMA_signal'].fillna(0)
    return df


def EXPMA_df(df, N1 = 12, N2 = 50):
    """
    EXPMA
    """
    close = df["close"]
    df["EMA1"] = EMA(close, N1)
    df["EMA2"] = EMA(close, N2)

    if global_signal:
        df = EXPMA_signal(df)
    return df


def SROC_signal(df):
    """
    SROC signal
    """
    df.loc[(REF(df["SROC"], 1) <= 0.05) & (df["SROC"] > 0.05), "SROC_signal"] = 1
    df.loc[(REF(df["SROC"], 1) >= 0.05) & (df["SROC"] < 0.05), "SROC_signal"] = -1
    df['SROC_signal']=df['SROC_signal'].fillna(method='ffill')
    df['SROC_signal'] = df['SROC_signal'].fillna(0)
    return df

def SROC_df(df, N = 13, M = 21):
    """
    SROC
    """
    close = df["close"]
    emap = EMA(close, N)
    df["SROC"] = (emap - REF(emap, M)) / REF(emap, M)

    if global_signal:
        df = SROC_signal(df)
    return df


def TSI_signal(df):
    """
    TSI signal
    """
    df.loc[(REF(df["TSI"], 1) <= 10) & (df["TSI"] > 10), "TSI_signal"] = 1
    df.loc[(REF(df["TSI"], 1) >= -10) & (df["TSI"] < -10), "TSI_signal"] = -1
    df['TSI_signal']=df['TSI_signal'].fillna(method='ffill')
    df['TSI_signal'] = df['TSI_signal'].fillna(0)
    return df

def TSI_df(df, N1 = 25, N2 = 13):
    close = df["close"]
    df["TSI"] = EMA(EMA(close - REF(close, 1), N1), N2) / EMA(EMA(ABS(close - REF(close, 1)), N1), N2) * 100

    if global_signal:
        df = TSI_signal(df)

    return df


def MICD_signal(df):
    df.loc[(REF(df["MICD"], 1) <= 0) & (df["MICD"] > 0), "MICD_signal"] = 1
    df.loc[(REF(df["MICD"], 1) >= 0) & (df["MICD"] < 0), "MICD_signal"] = -1
    df['MICD_signal']=df['MICD_signal'].fillna(method='ffill')
    df['MICD_signal'] = df['MICD_signal'].fillna(0)
    return df


def MICD_df(df, N = 20, N1 = 10, N2 = 20, M = 10):
    close = df["close"]
    mi = close - REF(close, N)
    mtmma = SMA(mi, N, 1)
    dif = MA(REF(mtmma, 1), N1) - MA(REF(mtmma, 1), N2)
    df["MICD"] = SMA(dif, M, 1)

    if global_signal:
        df = MICD_signal(df)
    return df


def OSC_single(df):
    df.loc[(REF(df["OSC"], 1) <= REF(df["OSCMA"], 1)) & (df["OSC"] > df["OSCMA"]), "OSC_signal"] = 1
    df.loc[(REF(df["OSC"], 1) >= REF(df["OSCMA"], 1)) & (df["OSC"] < df["OSCMA"]), "OSC_signal"] = -1
    df['OSC_signal']=df['OSC_signal'].fillna(method='ffill')
    df['OSC_signal'] = df['OSC_signal'].fillna(0)
    return df

def OSC_df(df, N = 40, M = 20):
    close = df["close"]
    df["OSC"] = close - MA(close, N)
    df["OSCMA"] = MA(df["OSC"], M)

    if global_signal:
        df = OSC_single(df)
    return df




def DO_single(df):
    df.loc[(REF(df["DO"], 1) <= 0) & (df["DO"] > 0), "DO_signal"] = 1
    df.loc[(REF(df["DO"], 1) >= 0) & (df["DO"] < 0), "DO_signal"] = -1
    df['DO_signal']=df['DO_signal'].fillna(method='ffill')
    df['DO_signal'] = df['DO_signal'].fillna(0)
    return df

# 研报未给出N和M的默认值
def DO_df(df, N, M):
    close = df["close"]
    rsi = RSI(close, N)
    df["DO"] = EMA(EMA(rsi, N), M)

    if global_signal:
        df = DO_single(df)
    return df







def MACD_signal(df):
    # MACD上穿0买入
    df.loc[(REF(df["MACD"], 1) <= 0) & (df["MACD"] > 0), "MACD_signal"] = 1
    # MACD下穿0卖出
    df.loc[(REF(df["MACD"], 1) >= 0) & (df["MACD"] < 0), "MACD_signal"] = -1
    df['MACD_signal']=df['MACD_signal'].fillna(method='ffill')
    df['MACD_signal'] = df['MACD_signal'].fillna(0)
    # 另一种信号构造方式是MACD和其移动平均的差值，上穿0买入，下穿0卖出
    return df

def MACD_df(df, N1 = 20, N2 = 40, N3 = 5):
    close = df["close"]
    df["DIF"] = EMA(close, N1) - EMA(close, N2)
    df["DEA"] = EMA(df["DIF"], N3)
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2

    if global_signal:
        df = MACD_signal(df)

    return df

def TDI_signal(df):
    # RSI_PriceLine同时上穿RSI_SingleLine和RSI_MarketLine
    df.loc[(REF(df["RSI_PriceLine"], 1) <= REF(df["RSI_SingleLine"], 1)) & (df["RSI_PriceLine"] > df["RSI_SingleLine"]) & (REF(df["RSI_PriceLine"], 1) <= REF(df["RSI_MarketLine"], 1)) & (df["RSI_PriceLine"] > df["RSI_MarketLine"]), "TDI_signal"] = 1
    # RSI_PriceLine同时下穿RSI_SingleLine和RSI_MarketLine
    df.loc[(REF(df["RSI_PriceLine"], 1) >= REF(df["RSI_SingleLine"], 1)) & (df["RSI_PriceLine"] < df["RSI_SingleLine"]) & (REF(df["RSI_PriceLine"], 1) >= REF(df["RSI_MarketLine"], 1)) & (df["RSI_PriceLine"] < df["RSI_MarketLine"]), "TDI_signal"] = -1
    df['TDI_signal']=df['TDI_signal'].fillna(method='ffill')
    df['TDI_signal'] = df['TDI_signal'].fillna(0)
    return df

# 研报未给出N1这个参数
def TDI_df(df, N1, N2, N3, N4):
    close = df["close"]
    rsi = RSI(close, N1)
    df["RSI_PriceLine"] = EMA(rsi, N2)
    df["RSI_SingleLine"] = EMA(rsi, N3)
    df["RSI_MarketLine"] = EMA(rsi, N4)

    if global_signal:
        df = TDI_signal(df)
    return df

def COPP_signal(df):
    df.loc[(REF(df["COPP"], 1) <= 0) & (df["COPP"] > 0), "COPP_signal"] = 1
    df.loc[(REF(df["COPP"], 1) >= 0) & (df["COPP"] < 0), "COPP_signal"] = -1
    df['COPP_signal']=df['COPP_signal'].fillna(method='ffill')
    df['COPP_signal'] = df['COPP_signal'].fillna(0)
    return df


# 研报未给默认参数
def COPP_df(df, N1, N2, M):
    close = df["close"]
    rc = ((close - REF(close, N1)) / REF(close, N1) + (close - REF(close, N2)) / REF(close, N2)) * 100
    df["COPP"] = WMA(rc, M)

    if global_signal:
        df = COPP_signal(df)
    return df


def DMA_signal(df):
    # DMA上穿AMA买入
    df.loc[(REF(df["DMA"], 1) <= REF(df["AMA"], 1)) & (df["DMA"] > df["AMA"]), "DMA_signal"] = 1
    # DMA下穿AMA卖出
    df.loc[(REF(df["DMA"], 1) >= REF(df["AMA"], 1)) & (df["DMA"] < df["AMA"]), "DMA_signal"] = -1
    df['DMA_signal']=df['DMA_signal'].fillna(method='ffill')
    df['DMA_signal'] = df['DMA_signal'].fillna(0)
    return df

def DMA_df(df, N1, N2):
    close = df["close"]
    df["DMA"] = MA(close, N1) - MA(close, N2)
    df["AMA"] = MA(df["DMA"], N1)

    if global_signal:
        df = DMA_signal(df)
    return df

def PSY_signal(df):
    # PSY上穿60买入
    df.loc[(REF(df["PSY"], 1) <= 60) & (df["PSY"] > 60), "PSY_signal"] = 1
    # PSY下穿40卖出
    df.loc[(REF(df["PSY"], 1) >= 40) & (df["PSY"] < 40), "PSY_signal"] = -1
    df['PSY_signal']=df['PSY_signal'].fillna(method='ffill')
    df['PSY_signal'] = df['PSY_signal'].fillna(0)
    return df


def PSY_df(df, N = 12):
    close = df["close"]
    df["PSY"] = SUM(IF(close > REF(close, 1), 1, 0), N) / N * 100

    if global_signal:
        df = PSY_signal(df)

    return df


def DPO_signal(df):
    # DPO上穿0买入
    df.loc[(REF(df["DPO"], 1) <= 0) & (df["DPO"] > 0), "DPO_signal"] = 1
    # DPO下穿0卖出
    df.loc[(REF(df["DPO"], 1) >= 0) & (df["DPO"] < 0), "DPO_signal"] = -1
    df['DPO_signal']=df['DPO_signal'].fillna(method='ffill')
    df['DPO_signal'] = df['DPO_signal'].fillna(0)
    return df

def DPO_df(df, N = 20):
    close = df["close"]
    df["DPO"] = close - REF(MA(close, N), N / 2 + 1)

    if global_signal:
        df = DPO_signal(df)

    return df


def BIAS_signal(df):
    # BIAS6大于5且BIAS12大于7且BIAS24大于11买入
    df.loc[(df["BIAS6"] > 5) & (df["BIAS12"] > 7) & (df["BIAS24"] > 11), "BIAS_signal"] = 1
    # BIAS6小于-5且BIAS12小于-7且BIAS24小于-11卖出
    df.loc[(df["BIAS6"] < -5) & (df["BIAS12"] < -7) & (df["BIAS24"] < -11), "BIAS_signal"] = -1
    df['BIAS_signal']=df['BIAS_signal'].fillna(method='ffill')
    df['BIAS_signal'] = df['BIAS_signal'].fillna(0)
    return df

def BIAS_df(df, N1 = 6, N2 = 12, N3 = 24):
    close = df["close"]
    df["BIAS6"] = (close - MA(close, N1)) / MA(close, N1) * 100
    df["BIAS12"] = (close - MA(close, N2)) / MA(close, N2) * 100
    df["BIAS24"] = (close - MA(close, N3)) / MA(close, N3) * 100
    if global_signal:
        df = BIAS_signal(df)
    return df


def HULLMA_signal(df):
    # HULLMA1上传HULLMA2买入
    df.loc[(REF(df["HULLMA1"], 1) <= REF(df["HULLMA2"], 1)) & (df["HULLMA1"] > df["HULLMA2"]), "HULLMA_signal"] = 1
    # HULLMA1下穿HULLMA2卖出
    df.loc[(REF(df["HULLMA1"], 1) >= REF(df["HULLMA2"], 1)) & (df["HULLMA1"] < df["HULLMA2"]), "HULLMA_signal"] = -1
    df['HULLMA_signal']=df['HULLMA_signal'].fillna(method='ffill')
    df['HULLMA_signal'] = df['HULLMA_signal'].fillna(0)
    return df

def HULLMA_df(df, N1 = 20, N2 = 80):
    close = df["close"]

    # 短期HULLMA
    x1 = 2 * EMA(close, int(N1 / 2)) - EMA(close, N1)
    df["HULLMA1"] = EMA(x1, int(pow(N1, 0.5)))
    # 长期HULLMA
    x2 = 2 * EMA(close, int(N2 / 2)) - EMA(close, N2)
    df["HULLMA2"] = EMA(x2, int(pow(N2, 0.5)))
    if global_signal:
        df = HULLMA_signal(df)
    return df


def KST_signal(df):
    # KST上穿0买入
    df.loc[(REF(df["KST"], 1) <= 0) & (df["KST"] > 0), "KST_signal"] = 1
    # KST下穿0卖出
    df.loc[(REF(df["KST"], 1) >= 0) & (df["KST"] < 0), "KST_signal"] = -1
    df['KST_signal']=df['KST_signal'].fillna(method='ffill')
    df['KST_signal'] = df['KST_signal'].fillna(0)
    return df


def KST_df(df):
    close = df["close"]
    roc1 = close - REF(close, 10)
    roc2 = close - REF(close, 15)
    roc3 = close - REF(close, 20)
    roc4 = close - REF(close, 30)
    df["KST"] = MA(MA(roc1, 10) * 1 + MA(roc2, 10) * 2 + MA(roc3, 10) * 3 + MA(roc4, 10) * 4, 9)
    if global_signal:
        df = KST_signal(df)
    return df



def ENV_signal(df):
    # 上穿上轨买入
    df.loc[(REF(df["close"], 1) <= REF(df["UPPER"], 1)) & (df["close"] > df["UPPER"]), "ENV_signal"] = 1
    # 下穿下轨卖出
    df.loc[(REF(df["close"], 1) >= REF(df["LOWER"], 1)) & (df["close"] < df["LOWER"]), "ENV_signal"] = -1
    df['ENV_signal']=df['ENV_signal'].fillna(method='ffill')
    df['ENV_signal'] = df['ENV_signal'].fillna(0)
    return df


def ENV_df(df, N = 25, param = 0.05):
    close = df["close"]
    df["UPPER"] = MA(close, N) * (1 + param)
    df["LOWER"] = MA(close, N) * (1 - param)
    if global_signal:
        df = ENV_signal(df)
    return df

def PMO_signal(df):
    #  PMO上穿PMO_signal买入
    df.loc[(REF(df["PMO"], 1) <= REF(df["PMO_signal"], 1)) & (df["PMO"] > df["PMO_signal"]), "PMO_signal"] = 1
    # PMO下穿PMO_signal卖出
    df.loc[(REF(df["PMO"], 1) >= REF(df["PMO_signal"], 1)) & (df["PMO"] < df["PMO_signal"]), "PMO_signal"] = -1
    df['PMO_signal']=df['PMO_signal'].fillna(method='ffill')
    df['PMO_signal'] = df['PMO_signal'].fillna(0)
    return df


def PMO_df(df, N1 = 10, N2 = 40, N3 = 20):
    close = df["close"]
    roc = (close - REF(close, N1)) / REF(close, N1) * 100
    roc_ma = DMA(roc, 2 / N1)
    roc_ma10 = roc_ma * 10
    df["PMO"] = DMA(roc_ma10, 2 / N2)
    df["PMO_signal"] = DMA(df["PMO"], 2 / (N3 + 1))

    if global_signal:
        df = PMO_signal(df)

    return df

def POS_signal(df):
    # POS上穿80买入
    df.loc[(REF(df["POS"], 1) <= 80) & (df["POS"] > 80), "POS_signal"] = 1
    # POS下穿20卖出
    df.loc[(REF(df["POS"], 1) >= 20) & (df["POS"] < 20), "POS_signal"] = -1
    df['POS_signal']=df['POS_signal'].fillna(method='ffill')
    df['POS_signal'] = df['POS_signal'].fillna(0)
    return df


def POS_df(df, N = 100):
    close = df["close"]
    price = (close - REF(close, N)) / REF(close, N)
    df["POS"] = (price - MIN(price, N)) / (MAX(price, N) - MIN(price, N)) * 100
    if global_signal:
        df = POS_signal(df)
    return df


def TEMA_signal(df):
    # 快线上穿慢线买入
    df.loc[(REF(df["TEMAN1"], 1) <= REF(df["TEMAN2"], 1)) & (df["TEMAN1"] > df["TEMAN2"]), "TEMA_signal"] = 1
    # 快线下穿慢线卖出
    df.loc[(REF(df["TEMAN1"], 1) >= REF(df["TEMAN2"], 1)) & (df["TEMAN1"] < df["TEMAN2"]), "TEMA_signal"] = -1
    df['TEMA_signal']=df['TEMA_signal'].fillna(method='ffill')
    df['TEMA_signal'] = df['TEMA_signal'].fillna(0)
    return df


def TEMA_df(df, N1 = 20, N2 = 40):
    close = df["close"]
    # 快线TEMA
    df["TEMAN1"] = 3 * EMA(close, N1) - 3 * EMA(EMA(close, N1), N1) + EMA(EMA(EMA(close, N1), N1), N1)
    # 慢线TEMA
    df["TEMAN2"] = 3 * EMA(close, N2) - 3 * EMA(EMA(close, N2), N2) + EMA(EMA(EMA(close, N2), N2), N2)
    
    
    if global_signal:
        df = TEMA_signal(df)
    return df

def RCCD_signal(df):
    # RCCD上穿0买入
    df.loc[(REF(df["RCCD"], 1) <= 0) & (df["RCCD"] > 0), "RCCD_signal"] = 1
    # RCCD下穿0卖出
    df.loc[(REF(df["RCCD"], 1) >= 0) & (df["RCCD"] < 0), "RCCD_signal"] = -1
    df['RCCD_signal']=df['RCCD_signal'].fillna(method='ffill')
    df['RCCD_signal'] = df['RCCD_signal'].fillna(0)
    return df

def RCCD_df(df, M = 40, N1 = 20, N2 = 40):
    close = df["close"]
    rc = close / REF(close, M)
    arc1 = SMA(REF(rc, 1), M, 1)
    dif = MA(REF(arc1, 1), N1) - MA(REF(arc1, 1), N2)
    df["RCCD"] = SMA(dif, M, 1)
    if global_signal:
        df = RCCD_signal(df)
    return df

def DBCD_signal(df):
    # 上穿0.05买入
    df.loc[(REF(df["DBCD"], 1) <= 0.05) & (df["DBCD"] > 0.05), "DBCD_signal"] = 1
    # 下穿-0.05卖出
    df.loc[(REF(df["DBCD"], 1) >= -0.05) & (df["DBCD"] < -0.05), "DBCD_signal"] = -1
    df['DBCD_signal']=df['DBCD_signal'].fillna(method='ffill')
    df['DBCD_signal'] = df['DBCD_signal'].fillna(0)
    return df

def DBCD_df(df, N = 5, M = 16, T = 17):
    close = df["close"]
    bias = (close - MA(close, N)) / MA(close, N) * 100
    bias_dif = bias - REF(bias, M)
    df["DBCD"] = SMA(bias_dif, T, 1)
    if global_signal:
        df = DBCD_signal(df)
    return df





def TII_signal(df):
    # TII上穿TII_signal买入
    df.loc[(REF(df["TII"], 1) <= REF(df["TII_signal"], 1)) & (df["TII"] > df["TII_signal"]), "TII_signal"] = 1
    # TII下穿TII_signal卖出
    df.loc[(REF(df["TII"], 1) >= REF(df["TII_signal"], 1)) & (df["TII"] < df["TII_signal"]), "TII_signal"] = -1
    df['TII_signal']=df['TII_signal'].fillna(method='ffill')
    df['TII_signal'] = df['TII_signal'].fillna(0)
    return df

def TII_df(df, N1 = 40, N2 = 9):
    close = df["close"]
    M = int(N1 / 2) + 1
    close_ma = MA(close, N1)
    dev = close - close_ma
    dev_pos = IF(dev > 0, dev, 0)
    dev_neg = IF(dev < 0, -1 * dev, 0)
    sum_pos = SUM(dev_pos, M)
    sum_neg = SUM(dev_neg, M)
    df["TII"] = sum_pos / (sum_pos + sum_neg) * 100
    df["TII_signal"] = EMA(df["TII"], N2)
    if global_signal:
        df = TII_signal(df)
    return df




def MA_signal(df):
    # 短期均线上穿长期均线买入
    df.loc[(REF(df["MA5"], 1) <= REF(df["MA20"], 1)) & (df["MA5"] > df["MA20"]), "MA_signal"] = 1
    # 短期均线下穿长期均线卖出
    df.loc[(REF(df["MA5"], 1) >= REF(df["MA20"], 1)) & (df["MA5"] < df["MA20"]), "MA_signal"] = -1
    df['MA_signal']=df['MA_signal'].fillna(method='ffill')
    df['MA_signal'] = df['MA_signal'].fillna(0)
    return df

def MA_df(df, N1 = 5, N2 = 20):
    close = df["close"]
    df["MA5"] = MA(close, N1)
    df["MA20"] = MA(close, N2)
    if global_signal:
        df = MA_signal(df)
    return df


def ZLMACD_signal(df):
    # ZLMACD上穿0买入
    df.loc[(REF(df["ZLMACD"], 1) <= 0) & (df["ZLMACD"] > 0), "ZLMACD_signal"] = 1
    # ZLMACD下穿0卖出
    df.loc[(REF(df["ZLMACD"], 1) >= 0) & (df["ZLMACD"] < 0), "ZLMACD_signal"] = -1
    df['ZLMACD_signal']=df['ZLMACD_signal'].fillna(method='ffill')
    df['ZLMACD_signal'] = df['ZLMACD_signal'].fillna(0)
    return df


def ZLMACD_df(df, N1 = 20, N2 = 100):
    close = df["close"]
    df["ZLMACD"] = (2 * EMA(close, N1) - EMA(EMA(close, N1), N1)) - (2 * EMA(close, N2) - EMA(EMA(close, N2), N2)) 
    if global_signal:
        df = ZLMACD_signal(df)

    return df



