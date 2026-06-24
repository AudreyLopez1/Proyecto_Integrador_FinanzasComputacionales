import pandas as pd
import numpy as np
import ta
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def calcular_indicadores_comunes(df):
    """Calcula el conjunto estándar de variables predictoras en el DataFrame."""
    df_feat = df.copy()
    df_feat['RSI'] = ta.momentum.rsi(df_feat['close'], window=14)
    df_feat['Momentum'] = df_feat['close'].diff(14)
    macd_ind = ta.trend.MACD(df_feat['close'])
    df_feat['MACD'] = macd_ind.macd()
    df_feat['Signal'] = macd_ind.macd_signal()
    df_feat['EMA20'] = ta.trend.ema_indicator(df_feat['close'], window=20)
    df_feat['EMA50'] = ta.trend.ema_indicator(df_feat['close'], window=50)
    df_feat['EMA200'] = ta.trend.ema_indicator(df_feat['close'], window=200)
    df_feat['EMA8'] = ta.trend.ema_indicator(df_feat['close'], window=8)
    df_feat['EMA21'] = ta.trend.ema_indicator(df_feat['close'], window=21)
    
    df_feat['VWAP20'] = ta.volume.VolumeWeightedAveragePrice(
        high=df_feat['high'], low=df_feat['low'], close=df_feat['close'], volume=df_feat['volume'], window=20
    ).volume_weighted_average_price()

    bb = ta.volatility.BollingerBands(df_feat['close'], window=20)
    df_feat['BB_upper'] = bb.bollinger_hband()
    df_feat['BB_middle'] = bb.bollinger_mavg()
    df_feat['BB_lower'] = bb.bollinger_lband()

    stoch_14 = ta.momentum.StochasticOscillator(
        high=df_feat['high'], low=df_feat['low'], close=df_feat['close'], window=14, smooth_window=7
    )
    df_feat['Stochastic_%K_14_7_7'] = stoch_14.stoch()
    df_feat['Stochastic_%D_14_7_7'] = stoch_14.stoch_signal()

    stoch_7 = ta.momentum.StochasticOscillator(
        high=df_feat['high'], low=df_feat['low'], close=df_feat['close'], window=7, smooth_window=3
    )
    df_feat['Stochastic_%K_7_3_3'] = stoch_7.stoch()
    df_feat['Stochastic_%D_7_3_3'] = stoch_7.stoch_signal()

    df_feat['Close_val'] = df_feat['close']
    df_feat['Volume_val'] = df_feat['volume']
    
    return df_feat

def ejecutar(df, features_list=None):
    """
    Modelo Logit para predecir la dirección del mercado.
    Alinea y calcula las variables predictoras (lagged t-1), divide en 70/30,
    entrena el modelo y genera señales de compra/venta para el set de prueba.
    """
    if features_list is None:
        features_list = [
            'RSI', 'Momentum', 'MACD', 'Signal', 'EMA20', 'EMA50', 'EMA200', 'VWAP20',
            'BB_upper', 'BB_middle', 'BB_lower',
            'Stochastic_%K_14_7_7', 'Stochastic_%D_14_7_7',
            'Stochastic_%K_7_3_3', 'Stochastic_%D_7_3_3',
            'Close_val', 'Volume_val'
        ]
        
    df_feat = calcular_indicadores_comunes(df)
    
    # Lagging
    lagged_features = []
    for col in features_list:
        df_feat[col + '_lag1'] = df_feat[col].shift(1)
        lagged_features.append(col + '_lag1')
        
    df_feat['Direccion'] = (df_feat['close'] > df_feat['close'].shift(1)).astype(int)
    
    # Dropna
    df_clean = df_feat[['close', 'Direccion'] + lagged_features].dropna()
    
    # Split indices (relative to the original df length to align outputs)
    split_date_idx = int(len(df) * 0.7)
    
    train_idx = df_clean.index[df_clean.index < split_date_idx]
    test_idx = df_clean.index[df_clean.index >= split_date_idx]
    
    X_train = df_clean.loc[train_idx, lagged_features]
    y_train = df_clean.loc[train_idx, 'Direccion']
    X_test = df_clean.loc[test_idx, lagged_features]
    y_test = df_clean.loc[test_idx, 'Direccion']
    
    if len(X_train) == 0 or len(X_test) == 0:
        # Fallback to simple split
        split_idx = int(len(df_clean) * 0.7)
        X_train = df_clean.iloc[:split_idx][lagged_features]
        y_train = df_clean.iloc[:split_idx]['Direccion']
        X_test = df_clean.iloc[split_idx:][lagged_features]
        y_test = df_clean.iloc[split_idx:]['Direccion']
        test_idx = df_clean.iloc[split_idx:].index
        
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_scaled, y_train)
    
    preds = model.predict(X_test_scaled)
    
    # Reconstruct Series aligned with df
    pred_series = pd.Series(0, index=df.index)
    pred_series.loc[test_idx] = preds
    
    buy_sig = ((pred_series == 1) & (pred_series.shift(1) != 1)).astype(int)
    sell_sig = ((pred_series == 0) & (pred_series.shift(1) == 1)).astype(int)
    
    return buy_sig, sell_sig
