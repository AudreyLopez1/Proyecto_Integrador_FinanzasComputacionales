import pandas as pd
import numpy as np
import ta

def ejecutar(df, window=14, limit_buy=30, limit_sell=70):
    """
    Estrategia RSI.
    Compra cuando el RSI cae por debajo de limit_buy (sobreventa).
    Vende cuando el RSI supera limit_sell (sobrecompra).
    """
    rsi = ta.momentum.rsi(df['close'], window=window)
    
    buy_sig = (rsi < limit_buy).astype(int)
    sell_sig = (rsi > limit_sell).astype(int)
    
    return buy_sig, sell_sig
