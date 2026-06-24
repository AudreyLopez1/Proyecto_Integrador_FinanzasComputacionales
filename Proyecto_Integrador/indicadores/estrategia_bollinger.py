import pandas as pd
import numpy as np
import ta

def ejecutar(df, window=20, dev=2.0, ma_type='sma'):
    """
    Estrategia de Bandas de Bollinger.
    Compra cuando el precio de cierre es menor que la banda inferior.
    Vende cuando el precio de cierre es mayor que la banda superior.
    Soporta promedio móvil de tipo 'sma' (Simple) o 'ema' (Exponencial).
    """
    if ma_type == 'ema':
        middle = ta.trend.ema_indicator(df['close'], window=window)
        std = df['close'].rolling(window=window).std()
        upper = middle + dev * std
        lower = middle - dev * std
    else:
        bb = ta.volatility.BollingerBands(df['close'], window=window, window_dev=dev)
        upper = bb.bollinger_hband()
        lower = bb.bollinger_lband()
        
    buy_sig = (df['close'] < lower).astype(int)
    sell_sig = (df['close'] > upper).astype(int)
    
    return buy_sig, sell_sig
