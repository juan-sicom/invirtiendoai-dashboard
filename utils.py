import pandas as pd
import streamlit as st
import yfinance as yf

def calcular_bollinger(close_series, window=20, num_std=2):
    sma = close_series.rolling(window).mean()
    std = close_series.rolling(window).std()
    upper = sma + (num_std * std)
    lower = sma - (num_std * std)
    return sma, upper, lower


def interpretar_bollinger(precio_actual, banda_superior, banda_inferior):
    if pd.isna(precio_actual) or pd.isna(banda_superior) or pd.isna(banda_inferior):
        return "Sin datos"

    if precio_actual > banda_superior:
        return "📈 Precio fuera de la banda superior → 🔴 Posible sobrecompra"
    elif precio_actual < banda_inferior:
        return "📉 Precio fuera de la banda inferior → 🟢 Posible sobreventa"
    else:
        return "📊 Precio dentro de las bandas → 🟡 Zona neutra"


def calcular_rsi(close, window=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def interpretar_rsi(valor):
    if pd.isna(valor):
        return "Sin datos"
    if valor > 70:
        return "🔴 Sobrecompra"
    elif valor < 30:
        return "🟢 Sobreventa"
    else:
        return "🟡 Zona neutra"
    
    
def mostrar_diagnostico(df, ticker, mostrar_rsi=False, rsi=None, mostrar_bollinger=False, upper=None, lower=None):
    st.markdown("---")
    st.subheader("📋 Diagnóstico técnico y datos del activo")

    ultimo_close = df["Close"].iloc[-1]
    open_price = df["Open"].iloc[0]
    min_price = df["Close"].min()
    max_price = df["Close"].max()

    try:
        info = yf.Ticker(ticker).info
        market_cap = info.get("marketCap", None)
    except:
        market_cap = None

    st.markdown(f"**Apertura:** ${open_price:.2f}")
    st.markdown(f"**Cierre reciente:** ${ultimo_close:.2f}")
    st.markdown(f"**Máximo del período:** ${max_price:.2f}")
    st.markdown(f"**Mínimo del período:** ${min_price:.2f}")
    if market_cap:
        st.markdown(f"**Capitalización bursátil:** ${market_cap:,.0f}")
    else:
        st.markdown(f"**Capitalización:** No disponible")

