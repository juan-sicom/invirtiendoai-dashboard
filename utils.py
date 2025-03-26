import pandas as pd

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

