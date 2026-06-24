#liberias
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración Pagina
st.set_page_config(page_title="Proyecto Finanzas")
st.title("Análisis de Activos Financieros")


#opciones
PERIODOS = {"1 mes": "1mo","3 meses": "3mo","6 meses": "6mo","1 año": "1y","2 años": "2y","5 años": "5y"}
INTERVALOS = {"1 día": "1d","1 semana": "1wk","1 mes": "1mo"}
ACTIVOS = ["SPY","QQQ","NVDA","AAPL","MSFT","TSLA","META","AMZN"]
CAPITAL_INI = 10000.0
COMISION    = 0.001

# session state
for key, default in {
    "datos":     {},
    "tickers":   ["SPY"],
    "periodo":   "1 año",
    "intervalo": "1 día",
    "pesos_opt":   None,      # np.array con pesos del portafolio óptimo
    "tickers_port": [],      
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# descarga de datos
@st.cache_data(ttl=60)
def descargar_datos(ticker, periodo, intervalo):
    df = yf.download(ticker, period=periodo, interval=intervalo,
                     auto_adjust=True, progress=False)
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    return df

# sidebar
with st.sidebar:
    st.title("Barra")
    opcion = st.radio("Selecciona módulo", ["Perfil de Riesgo","Inicio","Portafolio Óptimo","Backtest"])
    st.divider()

    tickers = st.multiselect("Selecciona activos", ACTIVOS,
                             default=st.session_state["tickers"])
    periodo   = st.selectbox("Periodo",      list(PERIODOS.keys()),
                             index=list(PERIODOS.keys()).index(st.session_state["periodo"]))
    intervalo = st.selectbox("Periodicidad", list(INTERVALOS.keys()),
                             index=list(INTERVALOS.keys()).index(st.session_state["intervalo"]))

    if st.button("Cargar datos"):
        if not tickers:
            st.warning("")
        else:
            nuevos = {}
            with st.spinner(""):
                for t in tickers:
                    df = descargar_datos(t, PERIODOS[periodo], INTERVALOS[intervalo])
                    if not df.empty:
                        nuevos[t] = df
            st.session_state["datos"]     = nuevos
            st.session_state["tickers"]   = tickers
            st.session_state["periodo"]   = periodo
            st.session_state["intervalo"] = intervalo


# parámetros portafolio 
if opcion == "Portafolio Óptimo":
    with st.sidebar:
        st.divider()
        st.markdown("**Parámetros para el portafolio**")
        num_ports       = st.slider("Número de portafolios", 500, 3000, 1000, step=500)
        ventas_en_corto = st.checkbox("Permitir ventas en corto", value=False)
#----------------------------------------------------------------------
if opcion == "Perfil de Riesgo":

    st.header("Perfilamiento de Riesgo")
    st.markdown("Responde las siguientes preguntas para determinar tu coeficiente de aversión al riesgo")

    preguntas = {
        "¿Cuánto tiempo planeas mantener tu inversión?": {
            "Menos de 1 año": 3,
            "1 a 5 años": 2,
            "Más de 5 años": 1,
        },
        "Si tu portafolio cae 20% en un mes, ¿qué harías?": {
            "Vendo todo inmediatamente": 3,
            "No hago nada y espero": 2,
            "Compro más aprovechando el precio": 1,
        },
        "¿Cuál es tu principal objetivo de inversión?": {
            "Preservar mi capital, no perder nada": 3,
            "Crecer mi capital moderadamente": 2,
            "Que tu dinero crezca sin importar los riesgos": 1,
        },
        "¿Qué porcentaje de tus ahorros destinarías a esta inversión?": {
            "Menos del 10%": 3,
            "Entre 10% y 50%": 2,
            "Más del 50%": 1,
        },
        "¿Cómo describirías tu grado de conocimiento en inversiones?": {
            "Baja": 3,
            "Media": 2,
            "Alta": 1,
        },
        "¿Cómo reaccionas emocionalmente ante pérdidas?": {
            "Me genera mucho estrés, no puedo tolerarlo": 3,
            "Me incomoda pero lo manejo": 2,
            "Lo veo como una oportunidad": 1,},
            }

    respuestas = {}
    for pregunta, opciones in preguntas.items():
        respuestas[pregunta] = st.radio(pregunta, list(opciones.keys()), index=None)

    st.divider()

    if st.button("Calcular mi perfil", type="primary"):
        if None in respuestas.values():
            st.warning("Por favor responde todas las preguntas.")
        else:
            total = sum(preguntas[p][r] for p, r in respuestas.items())

            # Escala 6 pts (agresivo) a 18 pts (conservador)
            # A va de 1 (agresivo) a 10 (conservador)
            A = round(1 + (total - 6) * (9 / 12), 2)

            if total <= 9:
                perfil = "Agresivo",
            elif total <= 13:
                perfil = "Moderado",
            else:
                perfil= "Conservador",

            st.success(f"Perfil: {perfil}")

            st.session_state["coef_A"] = A
            st.session_state["perfil"] = perfil
#---------------------------------------------------------------------------------
# INICIO

elif opcion == "Inicio":
    datos = st.session_state["datos"]

    def calcular_estadisticas(df):
        close = df["close"]
        rendimientos = close.pct_change().dropna()
        precio_actual = close.iloc[-1]
        retorno = ((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100
        return {
            "precio":      precio_actual,
            "rendimiento": retorno,
            "maximo":      close.max(),
            "minimo":      close.min()}

    def grafico_precio(df, ticker):

        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Precio"))
        #bandas de media movil
        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=ema12,
                name="EMA 12",
                line=dict(width=1.5)))

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=ema26,
                name="EMA 26",
                line=dict(width=1.5)))

        fig.update_layout(
            title=f"{ticker}",
            yaxis_title="Precio",
            xaxis_rangeslider_visible=False,
            height=600)

        return fig

    def grafico_comparacion(datos):
        fig = go.Figure()
        for ticker, df in datos.items():
            base100 = (df["close"] / df["close"].iloc[0]) * 100
            fig.add_trace(go.Scatter(x=df.index, y=base100, mode="lines", name=ticker))
        fig.update_layout(title="Comparación de activos (Base 100)",
                          xaxis_title="Fecha", yaxis_title="Índice Base 100")
        return fig

    # pestañas
    tab1, tab2 = st.tabs(["Precios individuales", "Comparación"])

    with tab1:
        for ticker, df in datos.items():
            st.subheader(ticker)
            stats = calcular_estadisticas(df)
            col1, col2 = st.columns(2)
            col1.metric("Precio", f"${stats['precio']:.2f}")
            col2.metric("Rendimiento %", f"{stats['rendimiento']:.2f}%")
            st.write(f"Desde: {df.index.min().date()} | Hasta: {df.index.max().date()}")
            st.plotly_chart(grafico_precio(df, ticker), use_container_width=True)
            tabla = pd.DataFrame({
                "Indicador": ["Máximo", "Mínimo"],
                "Valor": [round(stats["maximo"], 2), round(stats["minimo"], 2)]})
            st.dataframe(tabla, use_container_width=True)
    
            csv = df.to_csv(index=True).encode("utf-8")
            st.download_button(
            label=f"Descargar {ticker} CSV",
            data=csv,
            file_name=f"{ticker}_{PERIODOS[st.session_state['periodo']]}.csv",
            mime="text/csv",
        )

    with tab2:
        st.plotly_chart(grafico_comparacion(datos), use_container_width=True)
        resumen = []
        for ticker, df in datos.items():
            stats = calcular_estadisticas(df)
            resumen.append({
                "Ticker":    ticker,
                "Precio":    round(stats["precio"], 2),
                "Retorno %": round(stats["rendimiento"], 2)})
        st.dataframe(pd.DataFrame(resumen), use_container_width=True)
        
        if datos:
            df_todos = pd.concat(
        {t: df["close"].rename(t) for t, df in datos.items()}, axis=1)
    
            csv_todos = df_todos.to_csv(index=True).encode("utf-8")
            st.download_button(
            label="Descargar precio de cierre todos los activos CSV)",
            data=csv_todos,
            file_name="activos_comparacion.csv",
            mime="text/csv",)   

#--------------------------------------------------------------------------------------------
#portafolio optimo
elif opcion == "Portafolio Óptimo":

    from scipy.optimize import minimize
    datos = st.session_state["datos"]

    if len(datos) < 2:
        st.warning("Selecciona al menos 2 activos y carga los datos.")
        st.stop()

    coef_A = st.session_state.get("coef_A")
    perfil = st.session_state.get("perfil")
    if isinstance(perfil, tuple):
        perfil = perfil[0]

    tiene_perfil = coef_A is not None
    if tiene_perfil:
        st.write(f"Perfil: {perfil} ")

    #Preparar datos
    cierres = pd.concat(
        {t: df["close"].rename(t) for t, df in datos.items()}, axis=1).dropna()

    tickers_port = list(cierres.columns)
    rendimientos = cierres.pct_change().dropna()

    e_ret = rendimientos.mean() * 252
    cov   = rendimientos.cov()  * 252
    std   = rendimientos.std()  * np.sqrt(252)

    # Simulación
    min_omega = -1.0 if ventas_en_corto else 0.0
    n = len(tickers_port)

    np.random.seed(42)
    port_sigmas, port_rends, port_pesos, port_utilidades = [], [], [], []

    for _ in range(num_ports):
        w = np.random.uniform(min_omega, 1.0, n)
        w = w / w.sum()
        r = float(w @ e_ret) * 100
        s = float(np.sqrt(w @ cov.values @ w)) * 100
        port_rends.append(r)
        port_sigmas.append(s)
        port_pesos.append(w)
        u = float(w @ e_ret) - 0.5 * coef_A * float(w @ cov.values @ w) if tiene_perfil else None
        port_utilidades.append(u)

    #Frontera eficiente con Jansen
    def portfolio_returns(weights, mean_returns):
        return np.sum(mean_returns * weights)

    def min_vol_target(mean_ret, cov, target, minOmega, maxOmega):
        n_assets = len(mean_ret)
        x0 = np.ones(n_assets) / n_assets

        def portfolio_std(wt, mean_ret=None, cov=None):
            return np.sqrt(wt.T @ cov @ wt)

        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: x.T @ mean_ret - target},
        ]
        bounds = tuple((minOmega, maxOmega) for _ in range(n_assets))
        return minimize(portfolio_std, x0=x0, args=(mean_ret, cov),
                        method='SLSQP', bounds=bounds, constraints=constraints,
                        options={'tol': 1e-10, 'maxiter': int(1e4)})

    with st.spinner(""):
        ret_range = np.linspace(e_ret.min(), e_ret.max(), 80)
        front = [min_vol_target(e_ret.values, cov.values, r, min_omega, 1.0)
                 for r in ret_range]

    ef_risks, ef_returns, ef_pesos = [], [], []
    for res in front:
        if res.success:
            ef_risks.append(res.fun * 100)
            ef_returns.append(portfolio_returns(res.x, e_ret) * 100)
            ef_pesos.append(res.x)

    #Portafolio con maximo Sharpe
    sharpes_ef = [r / s if s > 0 else -np.inf for r, s in zip(ef_returns, ef_risks)]
    idx_sharpe = int(np.argmax(sharpes_ef))
    w_sharpe   = ef_pesos[idx_sharpe]
    r_sharpe   = ef_returns[idx_sharpe]
    s_sharpe   = ef_risks[idx_sharpe]
    sh_sharpe  = sharpes_ef[idx_sharpe]

    #Portafolio optimo segun perfil
    if tiene_perfil:
        utilidades_ef = [
            (r / 100) - 0.5 * coef_A * (s / 100) ** 2
            for r, s in zip(ef_returns, ef_risks)]
        
        idx_util = int(np.argmax(utilidades_ef))
        w_util   = ef_pesos[idx_util]
        r_util   = ef_returns[idx_util]
        s_util   = ef_risks[idx_util]
        u_util   = utilidades_ef[idx_util]
        sh_util  = r_util / s_util if s_util > 0 else 0

    #grafica
    color_nube = "red" if ventas_en_corto else "#1269dc"
    label_nube = "Con ventas en corto" if ventas_en_corto else "Sin ventas en corto"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=port_sigmas, y=port_rends,
        mode="markers",
        marker=dict(size=4, color=color_nube, opacity=0.35),
        name=f"Portafolios simulados ({label_nube})",
    ))

    fig.add_trace(go.Scatter(
        x=ef_risks, y=ef_returns,
        mode="lines",
        line=dict(color="green", width=3),
        name="Frontera eficiente",
    ))

    fig.add_trace(go.Scatter(
        x=(std * 100).values, y=(e_ret * 100).values,
        mode="markers+text",
        text=tickers_port,
        textposition="top center",
        marker=dict(size=10, color="black"),
        name="Activos individuales",
    ))

    fig.add_trace(go.Scatter(
        x=[s_sharpe], y=[r_sharpe],
        mode="markers+text",
        textposition="middle right",
        marker=dict(size=16, color="orange", symbol="x"),
        name=f"Portafolio óptimo con maximo Sharpe",
    ))

    if tiene_perfil:
        fig.add_trace(go.Scatter(
            x=[s_util], y=[r_util],
            mode="markers+text",
            textposition="middle right",
            marker=dict(size=18, color="purple", symbol="star",
                        line=dict(color="white", width=1)),
            name=f"Portafolio óptimo perfil {perfil}",
        ))

    fig.update_layout(
        title="Frontera Eficiente y Portafolios Optimos",
        xaxis_title="Riesgo — Desviacion estandar anualizada (%)",
        yaxis_title="Retorno esperado anualizado (%)",
        height=580,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
    )
    st.plotly_chart(fig, use_container_width=True)

    #comparacion de portafolios
    st.subheader("Comparacion de portafolios")

    #portafolio con maximo sharpe
    st.markdown(" Maximo Sharpe")
    m1, m2, m3 = st.columns(3)
    m1.metric("Retorno",      f"{r_sharpe:.2f}%")
    m2.metric("Riesgo",       f"{s_sharpe:.2f}%")
    m3.metric("Sharpe Ratio", f"{sh_sharpe:.3f}")

    df_p_sharpe = pd.DataFrame({
            "Activo":    tickers_port,
            "Peso (%)": (w_sharpe * 100).round(2),
        }).sort_values("Peso (%)", ascending=False)
    st.dataframe(df_p_sharpe, use_container_width=True, hide_index=True)

    fig_pie_s = go.Figure(go.Pie(
            labels=tickers_port,
            values=np.abs(w_sharpe),
            hole=0.4,
            textinfo="label+percent",))
    
    fig_pie_s.update_layout(title="Pesos — Maximo Sharpe", height=340, margin=dict(t=40, b=0))
    st.plotly_chart(fig_pie_s, use_container_width=True)

    st.markdown(f"Optimo para perfil: {perfil}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Retorno",      f"{r_util:.2f}%")
    m2.metric("Riesgo",       f"{s_util:.2f}%")
    m3.metric("Sharpe Ratio", f"{sh_util:.3f}")

    d1, d2 = st.columns(2)
    d1.metric("Retorno vs Sharpe max", f"{r_util - r_sharpe:+.2f}%", delta_color="normal")
    d2.metric("Riesgo vs Sharpe max",  f"{s_util - s_sharpe:+.2f}%", delta_color="inverse")

    df_p_util = pd.DataFrame({
                "Activo":    tickers_port,
                "Peso (%)": (w_util * 100).round(2),
            }).sort_values("Peso (%)", ascending=False)
    st.dataframe(df_p_util, use_container_width=True, hide_index=True)

    fig_pie_u = go.Figure(go.Pie(
                labels=tickers_port,
                values=np.abs(w_util),
                hole=0.4,
                textinfo="label+percent",))
    fig_pie_u.update_layout(
                title=f"Pesos {perfil}",
                height=340, margin=dict(t=40, b=0))
    st.plotly_chart(fig_pie_u, use_container_width=True)


#-------------------------------------------------------------------------------------------------------------
# BACKTEST
elif opcion == "Backtest":

    datos = st.session_state["datos"]

    # cargamos las estrategias
    from Proyecto_Integrador.indicadores import estrategia_bollinger as bollinger
    import indicadores.estrategia_ema as ema
    import indicadores.estrategia_logit as logit
    import indicadores.estrategia_macd as macd
    import indicadores.estrategia_macd_stoch as macd_stoch
    import indicadores.estrategia_rnn as rnn
    import indicadores.estrategia_rsi as rsi
    import indicadores.estrategia_stoch_double as stoch_double
    import indicadores.estrategia_stoch_momentum as stoch_momentum
    import indicadores.estrategia_stoch_simple as stoch_simple

    ESTRATEGIAS = {
    "Bollinger Bands": bollinger,
    "EMA Crossover": ema,
    "Regresión Logística": logit,
    "MACD Crossover": macd,
    "MACD + Estocástico": macd_stoch,
    "Red Neuronal (RNN)": rnn,
    "RSI": rsi,
    "Doble Estocástico": stoch_double,
    "Estocástico + Momentum": stoch_momentum,
    "Estocástico Simple": stoch_simple,
    }

    def descubrir_estrategias():
        return ESTRATEGIAS
    #backtest
    def ejecutar_backtest(df_raw, modulo, nombre):
        df = df_raw.copy().reset_index(drop=True)
        try:
            buy_sig, sell_sig = modulo.ejecutar(df)
        except Exception as e:
            return {"error": str(e)}

        buy_sig  = buy_sig.fillna(0).astype(int)
        sell_sig = sell_sig.fillna(0).astype(int)

        capital, posicion = CAPITAL_INI, 0.0
        equity, operaciones = [], []

        for i in range(len(df)):
            precio = df["close"].iloc[i]
            if buy_sig.iloc[i] == 1 and posicion == 0 and precio > 0:
                com      = capital * COMISION
                posicion = (capital - com) / precio
                capital  = 0.0
                operaciones.append({"tipo": "compra", "costo_com": com})
            elif sell_sig.iloc[i] == 1 and posicion > 0 and precio > 0:
                ingresos = posicion * precio
                com      = ingresos * COMISION
                capital  = ingresos - com
                posicion = 0.0
                operaciones.append({"tipo": "venta", "costo_com": com})
            equity.append(capital + posicion * precio)

        if posicion > 0:
            equity[-1] = posicion * df["close"].iloc[-1] * (1 - COMISION)

        eq      = pd.Series(equity, index=df_raw.index[:len(equity)])
        retorno = (eq.iloc[-1] / CAPITAL_INI - 1) * 100
        rets    = eq.pct_change().dropna()
        sharpe  = (rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0.0
        dd      = (eq - eq.cummax()) / eq.cummax() * 100
        costos  = sum(o["costo_com"] for o in operaciones)
        n_ventas = sum(1 for o in operaciones if o["tipo"] == "venta")

        return {
            "nombre": nombre, "equity": eq, "error": None,
            "Retorno Total (%)":  round(retorno, 2),
            "Max Drawdown (%)":   round(dd.min(), 2),
            "Sharpe Ratio":       round(sharpe, 4),
            "Núm. Operaciones":   n_ventas,
            "Costos Totales ($)": round(costos, 2),
        }

    COLORES = ['#1f77b4','#d62728','#2ca02c','#ff7f0e','#9467bd',
               '#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']
    COLS_METRICAS = ["Retorno Total (%)", "Max Drawdown (%)",
                     "Sharpe Ratio", "Núm. Operaciones", "Costos Totales ($)"]
    
    st.header("Backtest de Estrategias")
    tickers_bt = st.multiselect("Activos a analizar", list(datos.keys()),
                                default=list(datos.keys()))

    if st.button("Ejecutar Backtest", type="primary"):

        estrategias = descubrir_estrategias()

        # iterar por cada activo seleccionado
        for ticker_bt in tickers_bt:
            st.subheader(f" {ticker_bt}")
            df_raw = datos[ticker_bt]

            resultados = {}
            prog  = st.progress(0)
            total = len(estrategias)

            for i, (nombre, modulo) in enumerate(estrategias.items()):
                res = ejecutar_backtest(df_raw.copy(), modulo, nombre)
                if res.get("error"):
                    st.warning(f" {nombre}: {res['error']}")
                else:
                    resultados[nombre] = res
                prog.progress((i + 1) / total)
            prog.empty()

            if not resultados:
                st.error(f"Ninguna estrategia pudo ejecutarse para {ticker_bt}.")
                continue

            # resumen
            resumen = pd.DataFrame(
                {n: {c: r[c] for c in COLS_METRICAS} for n, r in resultados.items()}
            ).T

            # ranking
            ranking = pd.DataFrame(index=resumen.index)
            ranking['Rank Retorno']     = resumen['Retorno Total (%)'].rank(ascending=False).astype(int)
            ranking['Rank Drawdown']    = resumen['Max Drawdown (%)'].rank(ascending=False).astype(int)
            ranking['Rank Sharpe']      = resumen['Sharpe Ratio'].rank(ascending=False).astype(int)
            ranking['Rank Operaciones'] = resumen['Núm. Operaciones'].rank(ascending=True).astype(int)
            ranking['Rank Costos']      = resumen['Costos Totales ($)'].rank(ascending=True).astype(int)
            ranking['Score Promedio']   = ranking.mean(axis=1)
            ranking['Ranking General']  = ranking['Score Promedio'].rank(ascending=True).astype(int)
            ranking = ranking.sort_values('Ranking General')
            mejor   = ranking.index[0]

            st.success(f"Mejor estrategia para **{ticker_bt}**: **{mejor}** "
                       f"(Score: {ranking.loc[mejor, 'Score Promedio']:.2f})")

            tab_m, tab_r, tab_radar, tab_eq = st.tabs(
                ["Métricas", "Ranking", "Gráfica", "Gráfica de curvas"])

            with tab_m:
                def color_celda(val, col):
                    if col == "Retorno Total (%)":
                        return "color: green; font-weight:bold" if val > 0 else "color: red; font-weight:bold"
                    if col == "Max Drawdown (%)":
                        return "color: green" if val > -10 else "color: red"
                    if col == "Sharpe Ratio":
                        return "color: green" if val > 0 else "color: red"
                    return ""

                styled = resumen.style.format({
                    "Retorno Total (%)":  "{:.2f}%",
                    "Max Drawdown (%)":   "{:.2f}%",
                    "Sharpe Ratio":       "{:.4f}",
                    "Núm. Operaciones":   "{:.0f}",
                    "Costos Totales ($)": "{:.2f}",
                })
                for col in ["Retorno Total (%)", "Max Drawdown (%)", "Sharpe Ratio"]:
                    styled = styled.map(lambda v, c=col: color_celda(v, c), subset=[col])

                st.dataframe(styled, use_container_width=True)


            with tab_r:
                # highlight mejor fila
                def highlight_mejor(row):
                    return ["background-color: #d4edda; font-weight:bold"
                            if row.name == mejor else "" for _ in row]

                st.dataframe(
                    ranking.style
                        .apply(highlight_mejor, axis=1)
                        .format({"Score Promedio": "{:.2f}"}),
                    use_container_width=True
                )

            with tab_radar:
                eps = 1e-9
                rd  = pd.DataFrame(index=resumen.index)
                rd['Retorno'] = (resumen['Retorno Total (%)'] - resumen['Retorno Total (%)'].min()) / \
                                (resumen['Retorno Total (%)'].max() - resumen['Retorno Total (%)'].min() + eps)
                rd['Drawdown'] = 1 - (abs(resumen['Max Drawdown (%)']) - abs(resumen['Max Drawdown (%)']).min()) / \
                                 (abs(resumen['Max Drawdown (%)']).max() - abs(resumen['Max Drawdown (%)']).min() + eps)
                sp = resumen['Sharpe Ratio'] - resumen['Sharpe Ratio'].min()
                rd['Sharpe'] = sp / (sp.max() + eps)
                rd['Eficiencia Ops'] = 1 - (resumen['Núm. Operaciones'] - resumen['Núm. Operaciones'].min()) / \
                                       (resumen['Núm. Operaciones'].max() - resumen['Núm. Operaciones'].min() + eps)
                rd['Eficiencia Costos'] = 1 - (resumen['Costos Totales ($)'] - resumen['Costos Totales ($)'].min()) / \
                                          (resumen['Costos Totales ($)'].max() - resumen['Costos Totales ($)'].min() + eps)

                cats = ['Retorno','Drawdown','Sharpe','Eficiencia Ops','Eficiencia Costos']
                fig_radar = go.Figure()
                for i, est in enumerate(rd.index):
                    v = rd.loc[est].values.tolist()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=v + [v[0]], theta=cats + [cats[0]],
                        name=est, line=dict(color=COLORES[i % len(COLORES)])))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
                st.plotly_chart(fig_radar, use_container_width=True)

            with tab_eq:
                fig_eq = go.Figure()
                bh = (df_raw["close"] / df_raw["close"].iloc[0]) * CAPITAL_INI
                fig_eq.add_trace(go.Scatter(x=df_raw.index, y=bh, mode="lines",
                                            name="Buy & Hold",
                                            line=dict(dash="dash", color="gray")))
                for i, (nombre, res) in enumerate(resultados.items()):
                    fig_eq.add_trace(go.Scatter(x=res["equity"].index,
                                                y=res["equity"].values,
                                                mode="lines", name=nombre,
                                                line=dict(color=COLORES[i % len(COLORES)])))
                fig_eq.update_layout(title=f" {ticker_bt}",
                                     xaxis_title="Fecha", yaxis_title="Capital ($)",
                                     height=500, hovermode="x unified")
                st.plotly_chart(fig_eq, use_container_width=True)

            st.divider()
