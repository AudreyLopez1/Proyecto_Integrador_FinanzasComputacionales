import pandas as pd
import numpy as np
import ta

def ejecutar(df, macd_fast=12, macd_slow=26, macd_signal=9, 
             stoch_window=14, stoch_k_smooth=7, stoch_d_smooth=7,
             usar_guardia_stoch=False, usar_guardia_macd=False):
    """
    Estrategia combinada de MACD y Estocástico (Estrategias 5, 6, 7 y 8).
    
    Lógica Base (Estrategia 5):
    - Compra si MACD > 0 y Estocástico %K < 80.
    - Venta si MACD < 0 o (MACD > 0 y Estocástico %K > 80).
    
    Refuerzos de Compra:
    - usar_guardia_stoch=True (Estrategia 6): Requiere además que %K > %D (señal de guardia del estocástico).
    - usar_guardia_macd=True (Estrategia 7): Requiere además que MACD > MACD Signal (señal de guardia de MACD).
    - Ambos True (Estrategia 8): Requiere ambos refuerzos.
    """
    # 1. Indicador MACD
    macd_ind = ta.trend.MACD(
        close=df['close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal
    )
    macd_val = macd_ind.macd()
    macd_sig = macd_ind.macd_signal()
    
    # 2. Indicador Estocástico
    stoch_ind = ta.momentum.StochasticOscillator(
        high=df['high'], low=df['low'], close=df['close'], window=stoch_window, smooth_window=stoch_k_smooth
    )
    stoch_k = stoch_ind.stoch()
    stoch_d = stoch_ind.stoch_signal()
    
    # 3. Señales Base
    base_buy = (macd_val > 0) & (stoch_k < 80)
    base_sell = (macd_val < 0) | ((macd_val > 0) & (stoch_k > 80))
    
    # Aplicar refuerzos a la compra
    buy_sig = base_buy.copy()
    if usar_guardia_stoch:
        buy_sig = buy_sig & (stoch_k > stoch_d)
    if usar_guardia_macd:
        buy_sig = buy_sig & (macd_val > macd_sig)
        
    return buy_sig.astype(int), base_sell.astype(int)
