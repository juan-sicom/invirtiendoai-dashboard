import streamlit as st
from streamlit_echarts import st_echarts, JsCode
from utils import calcular_bollinger, interpretar_bollinger, calcular_rsi, interpretar_rsi, mostrar_diagnostico
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(layout="centered")
st.title("📈 Invirtiendo.gpt")

# ========= BLOQUE DE AUTOCOMPLETADO CON CACHÉ =========

@st.cache_data(show_spinner=False, ttl=300)
def buscar_tickers_yahoo(query, limite=10):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            resultados = r.json().get("quotes", [])
            sugerencias = []
            for r in resultados:
                if "symbol" in r and "shortname" in r:
                    simbolo = r["symbol"]
                    nombre = r["shortname"]
                    sugerencias.append(f"{simbolo} - {nombre}")
                elif "symbol" in r:
                    sugerencias.append(r["symbol"])
            return sugerencias[:limite]
        else:
            return []
    except Exception as e:
        st.warning(f"Error buscando tickers: {e}")
        return []

entrada_usuario = st.text_input("Buscar ticker (ej: apple, msft, tesla):")

ticker = None

if entrada_usuario:
    sugerencias = buscar_tickers_yahoo(entrada_usuario)
    if sugerencias:
        seleccion = st.selectbox("Selecciona una opción:", sugerencias, key="ticker_select")
        ticker = seleccion.split(" - ")[0].strip().upper()
    else:
        st.info("Sin coincidencias. Usando entrada manual.")
        ticker = entrada_usuario.strip().upper()
else:
    ticker = "AAPL"

st.caption(f"📌 Ticker seleccionado: `{ticker}`")


# ========== SELECCIÓN DE RANGO ==========
rangos = {
    "1 Día": ("1d", "1m"),
    "5 Días": ("5d", "5m"),
    "1 Mes": ("1mo", "30m"),
    "6 Meses": ("6mo", "1d"),
    "1 Año": ("1y", "1d"),
    "Máx": ("max", "1d"),
}

rango_seleccionado = st.radio("Rango:", list(rangos.keys()), horizontal=True)


# ========== OPCIONES DE INDICADORES ==========
with st.expander("🛠 Indicadores opcionales", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        mostrar_bollinger = st.toggle("📈 Bollinger Bands (20, 2)", value=False)
        st.caption("""
        Muestra bandas de volatilidad alrededor de una media móvil:
        - 🔺 Banda superior → posible **sobrecompra**
        - 🔻 Banda inferior → posible **sobreventa**
        """)

    with col2:
        mostrar_rsi = st.toggle("📊 RSI (14)", value=False)
        st.caption("""
        Oscilador de momentum entre 0–100:
        - 🔺 RSI > 70 → **sobrecompra**
        - 🔻 RSI < 30 → **sobreventa**
        """)

# ========== DESCARGA Y PROCESAMIENTO ==========
if ticker:
    period, interval = rangos[rango_seleccionado]

    with st.spinner(f"📥 Descargando datos de {ticker} ({period}, {interval})..."):
        df = yf.download(ticker, period=period, interval=interval, progress=False)

    if df.empty:
        st.warning("⚠️ No se encontraron datos.")
    else:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        if "Close" not in df.columns:
            st.error("❌ No se encontró columna 'Close'.")
        else:
            df.reset_index(inplace=True)
            df = df.dropna(subset=["Close"])

            if "Datetime" in df.columns:
                df["time"] = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M")
            elif "Date" in df.columns:
                df["time"] = df["Date"].dt.strftime("%Y-%m-%d")
            else:
                df["time"] = df.index.astype(str)

            fechas = df["time"].tolist()
            precios = df["Close"].tolist()
            max_precio = max(precios)

            # Métrica arriba
            ultimo_precio = precios[-1]
            delta_pct = ((ultimo_precio / precios[0]) - 1) * 100
            st.metric("Último precio", f"${ultimo_precio:.2f}", delta=f"{delta_pct:.2f}%")

            # ========== CÁLCULO DE INDICADORES ==========
            series = [
                {
                    "name": "Precio",
                    "type": "line",
                    "data": precios,
                    "smooth": True,
                    "showSymbol": True,
                    "symbolSize": 6,
                    "hoverAnimation": True,
                    "lineStyle": {"width": 2, "color": "#007bff"},
                    "itemStyle": {"color": "#007bff", "borderColor": "#fff", "borderWidth": 2},
                    "areaStyle": {"opacity": 0.08, "color": "#007bff"},
                    "markLine": {
                        "symbol": "none",
                        "label": {
                            "formatter": f"'$ {ultimo_precio:.2f}'",
                            "position": "end",
                            "color": "#007bff"
                        },
                        "lineStyle": {"color": "#007bff", "type": "dashed", "width": 1},
                        "data": [{"yAxis": float(f"{ultimo_precio:.2f}")}]
                    }
                }
            ]

            if mostrar_bollinger:
                sma, upper, lower = calcular_bollinger(df["Close"])
                
                # Interpretación y etiqueta
                ultimo_close = df["Close"].iloc[-1]
                ultima_upper = upper.iloc[-1]
                ultima_lower = lower.iloc[-1]
                interpretacion_bb = interpretar_bollinger(ultimo_close, ultima_upper, ultima_lower)
                st.caption(f"{interpretacion_bb}")
                series.extend([
                    {
                        "name": "SMA 20",
                        "type": "line",
                        "data": sma.round(2).fillna("").tolist(),
                        "lineStyle": {"type": "dashed", "color": "#00bcd4"},
                        "showSymbol": False
                    },
                    {
                        "name": "Upper BB",
                        "type": "line",
                        "data": upper.round(2).fillna("").tolist(),
                        "lineStyle": {"width": 1, "color": "#aaa"},
                        "showSymbol": False
                    },
                    {
                        "name": "Lower BB",
                        "type": "line",
                        "data": lower.round(2).fillna("").tolist(),
                        "lineStyle": {"width": 1, "color": "#aaa"},
                        "showSymbol": False
                    }
                ])

            # ========== CONFIGURAR GRÁFICO PRINCIPAL ==========
            option = {
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "cross",
                        "label": {"backgroundColor": "#007bff"}
                    }
                },
                "xAxis": {
                    "type": "category",
                    "data": fechas,
                    "axisLabel": {"show": False},
                    "axisLine": {"show": False},
                    "axisTick": {"show": False}
                },
                "yAxis": {
                    "type": "value",
                    "scale": True,
                    "axisLine": {"show": False},
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {
                        "formatter": f"function(value) {{ return value === {max_precio:.2f} ? '$' + value.toFixed(2) : ''; }}"
                    }
                },
                "series": series,
                "grid": {"top": 10, "bottom": 10, "left": 0, "right": 0},
                "dataZoom": [{"type": "inside"}],
            }

            st_echarts(option, height="400px")
            

            # ========== GRÁFICO RSI SI SE ACTIVA ==========
            if mostrar_rsi:
                rsi = calcular_rsi(df["Close"])

                rsi_option = {
                    "title": {"text": "RSI (14)", "left": "center"},
                    "xAxis": {
                        "type": "category",
                        "data": fechas,
                        "axisLabel": {"show": False}
                    },
                    "yAxis": {
                        "min": 0,
                        "max": 100,
                        "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
                    },
                    "series": [
                        {
                            "name": "RSI",
                            "type": "line",
                            "data": rsi.round(2).fillna("").tolist(),
                            "lineStyle": {"color": "purple"},
                            "showSymbol": False,
                            "markArea": {
                                "silent": True,
                                "data": [
                                    [{"yAxis": 70}, {"yAxis": 100}],
                                    [{"yAxis": 0, "itemStyle": {"color": "rgba(0,255,0,0.1)"}}, {"yAxis": 30}]
                                ]
                            },
                            "markLine": {
                                "silent": True,
                                "lineStyle": {"type": "dashed", "color": "#bbb"},
                                "data": [{"yAxis": 70}, {"yAxis": 30}]
                            }
                        }
                    ],
                    "grid": {"top": 30, "bottom": 20, "left": 10, "right": 10},
                }

                st_echarts(rsi_option, height="200px")
                
                valor_rsi_actual = rsi.iloc[-1]
                interpretacion = interpretar_rsi(valor_rsi_actual)
                st.caption(f"📊 RSI actual: {valor_rsi_actual:.2f} → {interpretacion}")
                
            mostrar_diagnostico(
                df=df,
                ticker=ticker,
                mostrar_rsi=mostrar_rsi,
                rsi=rsi if mostrar_rsi else None,
                mostrar_bollinger=mostrar_bollinger,
                upper=upper if mostrar_bollinger else None,
                lower=lower if mostrar_bollinger else None,
            )

                
