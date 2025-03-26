import streamlit as st
from streamlit_echarts import st_echarts, JsCode
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(layout="centered")
st.title("📈 Precio Limpio con Tooltip Inteligente")

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

rangos = {
    "1 Día": ("1d", "1m"),
    "5 Días": ("5d", "5m"),
    "1 Mes": ("1mo", "1d"),
    "6 Meses": ("6mo", "1d"),
    "1 Año": ("1y", "1d"),
    "Máx": ("max", "1d"),
}

rango_seleccionado = st.radio("Rango:", list(rangos.keys()), horizontal=True)

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

            # ⚙️ Configuración ECharts
            option = {
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "cross",
                        "label": {
                            "backgroundColor": "#007bff"
                        }
                    }
                },
                "xAxis": {
                    "type": "category",
                    "data": fechas,
                    "axisLabel": {"show": False},
                    "axisLine": {"show": False},
                    "axisTick": {"show": False},
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
                "series": [
                    {
                        "name": "Precio",
                        "type": "line",
                        "data": precios,
                        "smooth": True,
                        "showSymbol": True,
                        "symbolSize": 6,
                        "hoverAnimation": True,
                        "lineStyle": {
                            "width": 2,
                            "color": "#007bff"
                        },
                        "itemStyle": {
                            "color": "#007bff",
                            "borderColor": "#fff",
                            "borderWidth": 2
                        },
                        "areaStyle": {
                            "opacity": 0.08,
                            "color": "#007bff"
                        },
                        "markLine": {
                            "symbol": "none",
                            "label": {
                                "formatter": f"'$ {ultimo_precio:.2f}'",
                                "position": "end",
                                "color": "#007bff"
                            },
                            "lineStyle": {
                                "color": "#007bff",
                                "type": "dashed",
                                "width": 1
                            },
                            "data": [{"yAxis": float(f"{ultimo_precio:.2f}")}]
                        }
                    }
                ],
                "grid": {"top": 10, "bottom": 10, "left": 0, "right": 0},
                "dataZoom": [{"type": "inside"}],
            }


            st_echarts(option, height="400px")
