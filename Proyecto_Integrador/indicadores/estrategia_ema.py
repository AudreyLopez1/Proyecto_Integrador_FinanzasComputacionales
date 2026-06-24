import pandas as pd
import numpy as np
import ta

def ejecutar(df, fast=8, slow=21):
    """
    Estrategia de cruce de EMAs.
    Compra cuando la EMA rápida cruza por encima de la EMA lenta.
    Vende cuando la EMA rápida cruza por debajo de la EMA lenta.
    """
    ema_fast = ta.trend.ema_indicator(df['close'], window=fast)
    ema_slow = ta.trend.ema_indicator(df['close'], window=slow)
    
    buy_sig = ((ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))).astype(int)
    sell_sig = ((ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))).astype(int)
    
    return buy_sig, sell_sig
