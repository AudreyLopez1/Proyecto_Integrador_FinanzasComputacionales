import pandas as pd
import numpy as np
import ta

def ejecutar(df, w1=14, k1=7, d1=7, w2=7, k2=3, d2=3, usar_guardia=False):
    """
    Estrategia de Doble Estocástico.
    Compara las dos configuraciones (w1, k1, d1) y (w2, k2, d2).
    Si usar_guardia es True, requiere que el %K cruce o sea superior a su promedio móvil (%D) para compra,
    y que %K sea inferior a %D para venta.
    """
    # Configuración 1
    stoch1 = ta.momentum.StochasticOscillator(
        high=df['high'], low=df['low'], close=df['close'], window=w1, smooth_window=k1
    )
    stoch_k1 = stoch1.stoch()
    # Para el %D real en la configuración (w1, k1, d1), el d1 es el suavizado adicional de %K.
    # En ta.momentum.StochasticOscillator, stoch_signal() es el promedio de stoch() con periodo smooth_window.
    # Así que stoch_k es stoch() y stoch_d es stoch_signal().
    stoch_d1 = stoch1.stoch_signal()
    
    # Configuración 2
    stoch2 = ta.momentum.StochasticOscillator(
        high=df['high'], low=df['low'], close=df['close'], window=w2, smooth_window=k2
    )
    stoch_k2 = stoch2.stoch()
    stoch_d2 = stoch2.stoch_signal()
    
    if usar_guardia:
        buy_sig = ((stoch_k1 < 20) & (stoch_k2 < 20) & (stoch_k1 > stoch_d1) & (stoch_k2 > stoch_d2)).astype(int)
        sell_sig = ((stoch_k1 > 80) & (stoch_k2 > 80) & (stoch_k1 < stoch_d1) & (stoch_k2 < stoch_d2)).astype(int)
    else:
        buy_sig = ((stoch_k1 < 20) & (stoch_k2 < 20)).astype(int)
        sell_sig = ((stoch_k1 > 80) & (stoch_k2 > 80)).astype(int)
        
    return buy_sig, sell_sig
