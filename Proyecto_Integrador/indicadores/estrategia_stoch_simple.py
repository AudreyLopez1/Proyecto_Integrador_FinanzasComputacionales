import pandas as pd
import numpy as np
import ta

def ejecutar(df, window=14, k_smooth=7, d_smooth=7, usar_guardia=False):
    """
    Estrategia de Estocástico Simple.
    Calcula el estocástico para la configuración especificada.
    Si usar_guardia es True, requiere que %K > %D para compra, y %K < %D para venta.
    """
    stoch = ta.momentum.StochasticOscillator(
        high=df['high'], low=df['low'], close=df['close'], window=window, smooth_window=k_smooth
    )
    stoch_k = stoch.stoch()
    stoch_d = stoch.stoch_signal()
    
    if usar_guardia:
        buy_sig = ((stoch_k < 20) & (stoch_k > stoch_d)).astype(int)
        sell_sig = ((stoch_k > 80) & (stoch_k < stoch_d)).astype(int)
    else:
        buy_sig = (stoch_k < 20).astype(int)
        sell_sig = (stoch_k > 80).astype(int)
        
    return buy_sig, sell_sig
