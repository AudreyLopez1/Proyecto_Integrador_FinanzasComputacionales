import pandas as pd
import numpy as np
import ta

def ejecutar(df, fast=12, slow=26, signal=9):
    """
    Estrategia de cruce MACD.
    Compra cuando la línea MACD cruza por encima de la línea de señal (Signal).
    Vende cuando la línea MACD cruza por debajo de la línea de señal.
    """
    macd_ind = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
    macd_line = macd_ind.macd()
    signal_line = macd_ind.macd_signal()
    
    buy_sig = ((macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))).astype(int)
    sell_sig = ((macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))).astype(int)
    
    return buy_sig, sell_sig
