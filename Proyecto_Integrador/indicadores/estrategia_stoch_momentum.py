import pandas as pd
import numpy as np
import ta

def ejecutar(df, stoch_window=14, stoch_smooth=3, stoch_limit_buy=20, stoch_limit_sell=80, momentum_window=14):
    """
    Estrategia combinada del Oscilador Estocástico y Momentum.
    Compra cuando el oscilador estocástico (%K) está por debajo del límite de sobreventa (default 20) y el Momentum es positivo.
    Vende cuando el oscilador estocástico (%K) está por encima del límite de sobrecompra (default 80) y el Momentum es negativo.
    """
    stoch = ta.momentum.StochasticOscillator(
        high=df['high'], low=df['low'], close=df['close'], window=stoch_window, smooth_window=stoch_smooth
    )
    stoch_k = stoch.stoch()
    momentum = df['close'].diff(momentum_window)
    
    buy_sig = ((stoch_k < stoch_limit_buy) & (momentum > 0)).astype(int)
    sell_sig = ((stoch_k > stoch_limit_sell) & (momentum < 0)).astype(int)
    
    return buy_sig, sell_sig
