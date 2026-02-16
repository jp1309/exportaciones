"""
Módulo 3: Precio Implícito de Exportaciones.

Cálculo: Para cada producto j en cada mes i:
  Precio_Implícito(j,i) = Σ(FOB últimos 12 meses) / Σ(TM últimos 12 meses)

FOB está en millones de USD (convertido en data_loader), por lo que:
  Precio_Implícito = (FOB_12M * 1,000,000) / TM_12M  →  resultado en USD/TM
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data_aggregated

st.set_page_config(page_title="Precio Implícito", page_icon="💲", layout="wide")

PLOT_BG = "white"
GRID_COLOR = "#f0f0f0"

dff = load_data_aggregated()

st.title("Precio Implícito de Exportaciones")
st.caption(
    "Precio implícito = FOB acumulado 12 meses / Toneladas métricas acumuladas 12 meses | "
    "Resultado en USD/TM | Promedio móvil para suavizar estacionalidad"
)

st.info(
    "**Interpretación:** El precio implícito refleja el valor promedio por tonelada métrica "
    "exportada en los últimos 12 meses. Permite identificar tendencias de precios, "
    "comparar productos y detectar cambios estructurales en el comercio exterior.",
    icon="ℹ️"
)

# ── Calcular precio implícito por producto ────────────────────────────
@st.cache_data
def calcular_precio_implicito(data):
    """Calcula precio implícito 12M para cada producto."""
    serie_prod = data.groupby(["Fecha", "PP"]).agg(
        FOB=("FOB", "sum"),
        TM=("TM_Peso_Neto", "sum")
    ).reset_index().sort_values(["PP", "Fecha"])

    resultados = []
    for pp, grupo in serie_prod.groupby("PP"):
        g = grupo.copy().sort_values("Fecha")
        g["FOB_12M"] = g["FOB"].rolling(12, min_periods=12).sum()
        g["TM_12M"] = g["TM"].rolling(12, min_periods=12).sum()
        g["Precio_Implicito"] = np.where(
            g["TM_12M"] > 0,
            g["FOB_12M"] / g["TM_12M"] * 1_000_000,  # Convertir millones USD a USD/TM
            np.nan
        )
        resultados.append(g)

    return pd.concat(resultados, ignore_index=True)


precio_df = calcular_precio_implicito(dff)

# ── Helper: selector cascada Sector → Grupo → Producto ───────────────
def selector_producto(key_suffix):
    """Selector cascada Sector → Grupo → Producto con formato igual al sidebar."""
    datos = dff[["Cod_Sector", "Sector", "Cod_Grupo", "Grupo", "PP"]].drop_duplicates()

    # Sector: con código, ordenado por código, negativos al final
    sector_opts = datos[["Cod_Sector", "Sector"]].drop_duplicates()
    sector_opts["Label"] = sector_opts["Cod_Sector"] + " – " + sector_opts["Sector"]
    sector_opts["_sort"] = sector_opts["Cod_Sector"].apply(lambda x: "ZZZ" if x.startswith("-") else x)
    sector_opts = sector_opts.sort_values("_sort")

    col_s, col_g, col_p = st.columns(3)

    with col_s:
        sector_sel = st.selectbox("Sector", ["Todos"] + sector_opts["Label"].tolist(), key=f"sec_{key_suffix}")

    # Filtrar por sector
    if sector_sel != "Todos":
        sector_nombre = sector_sel.split(" – ", 1)[1]
        datos_fil = datos[datos["Sector"] == sector_nombre]
    else:
        datos_fil = datos

    # Grupo: con código, ordenado por código, negativos al final
    grupo_opts = datos_fil[["Cod_Grupo", "Grupo"]].drop_duplicates()
    grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
    grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(lambda x: "ZZZ" if x.startswith("-") else x)
    grupo_opts = grupo_opts.sort_values("_sort")

    with col_g:
        grupo_sel = st.selectbox("Grupo", ["Todos"] + grupo_opts["Label"].tolist(), key=f"grp_{key_suffix}")

    if grupo_sel != "Todos":
        grupo_nombre = grupo_sel.split(" – ", 1)[1]
        datos_fil = datos_fil[datos_fil["Grupo"] == grupo_nombre]

    prods_fil = sorted(datos_fil["PP"].unique())

    with col_p:
        prod_sel = st.selectbox("Producto", [""] + prods_fil, key=f"prod_{key_suffix}",
                                format_func=lambda x: "Seleccionar producto..." if x == "" else x)

    return prod_sel if prod_sel != "" else None


# ── 1. Detalle de precio implícito por producto ──────────────────────
st.divider()
st.subheader("1. Detalle de precio implícito por producto")

prod_sel = selector_producto("detalle")

if prod_sel is None:
    st.info("Selecciona un producto para ver su precio implícito.", icon="👆")
elif (sub_det := precio_df[precio_df["PP"] == prod_sel].dropna(subset=["Precio_Implicito"]).copy()) is not None and len(sub_det) > 0:
    # Calcular media y desviación estándar móvil
    sub_det["Media"] = sub_det["Precio_Implicito"].rolling(24, min_periods=12).mean()
    sub_det["Std"] = sub_det["Precio_Implicito"].rolling(24, min_periods=12).std()
    sub_det["Upper"] = sub_det["Media"] + 2 * sub_det["Std"]
    sub_det["Lower"] = (sub_det["Media"] - 2 * sub_det["Std"]).clip(lower=0)

    fig1 = go.Figure()

    # Banda de confianza
    fig1.add_trace(go.Scatter(
        x=pd.concat([sub_det["Fecha"], sub_det["Fecha"][::-1]]),
        y=pd.concat([sub_det["Upper"], sub_det["Lower"][::-1]]),
        fill="toself", fillcolor="rgba(37,99,235,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Banda ±2σ", showlegend=True,
        hoverinfo="skip"
    ))

    fig1.add_trace(go.Scatter(
        x=sub_det["Fecha"], y=sub_det["Precio_Implicito"],
        name="Precio implícito",
        line=dict(color="#2563eb", width=2),
        hovertemplate="%{x|%b %Y}: $%{y:,.0f} USD/TM<extra></extra>"
    ))

    fig1.add_trace(go.Scatter(
        x=sub_det["Fecha"], y=sub_det["Media"],
        name="Media móvil 24M",
        line=dict(color="#f59e0b", width=1.5, dash="dot"),
        hovertemplate="%{x|%b %Y}: $%{y:,.0f} USD/TM<extra></extra>"
    ))

    # Detectar outliers (fuera de 2σ)
    outliers = sub_det[
        (sub_det["Precio_Implicito"] > sub_det["Upper"]) |
        (sub_det["Precio_Implicito"] < sub_det["Lower"])
    ]
    if len(outliers) > 0:
        fig1.add_trace(go.Scatter(
            x=outliers["Fecha"], y=outliers["Precio_Implicito"],
            mode="markers", name="Outliers",
            marker=dict(color="#dc2626", size=8, symbol="diamond"),
            hovertemplate="<b>OUTLIER</b><br>%{x|%b %Y}: $%{y:,.0f} USD/TM<extra></extra>"
        ))

    fig1.update_layout(
        height=420, hovermode="x unified", margin=dict(t=20, b=30),
        legend=dict(orientation="h", y=1.08),
        yaxis_title="Precio Implícito (USD/TM)",
        plot_bgcolor=PLOT_BG
    )
    fig1.update_xaxes(gridcolor=GRID_COLOR)
    fig1.update_yaxes(gridcolor=GRID_COLOR, tickformat=",.0f")
    st.plotly_chart(fig1, use_container_width=True)

    # KPIs del producto seleccionado
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    ultimo_precio = sub_det["Precio_Implicito"].iloc[-1]
    precio_hace_12 = sub_det["Precio_Implicito"].iloc[-13] if len(sub_det) >= 13 else np.nan
    var_12m = ((ultimo_precio - precio_hace_12) / precio_hace_12 * 100) if not np.isnan(precio_hace_12) else 0

    col_k1.metric("Precio actual", f"${ultimo_precio:,.0f} USD/TM")
    col_k2.metric("Variación 12M", f"{var_12m:+.1f}%")
    col_k3.metric("Máximo histórico", f"${sub_det['Precio_Implicito'].max():,.0f}")
    col_k4.metric("Mínimo histórico", f"${sub_det['Precio_Implicito'].min():,.0f}")
else:
    st.warning("No hay datos suficientes para calcular precio implícito de este producto.")

st.divider()

# ── 2. Precio implícito por país destino (usa producto del gráfico 1) ─
st.subheader("2. Precio implícito por país destino")
st.caption("Compara el precio implícito del producto seleccionado arriba según el destino de exportación")

if prod_sel is None:
    st.info("Selecciona un producto en el gráfico 1 para ver su precio implícito por destino.", icon="👆")
else:
    prod_pais_data = dff[dff["PP"] == prod_sel]
    top_paises_pp = prod_pais_data.groupby("Pais_Destino")["FOB"].sum().sort_values(ascending=False).head(10).index

    precio_pais = prod_pais_data[prod_pais_data["Pais_Destino"].isin(top_paises_pp)].groupby(
        "Pais_Destino"
    ).agg(FOB=("FOB", "sum"), TM=("TM_Peso_Neto", "sum")).reset_index()
    precio_pais["Precio"] = np.where(
        precio_pais["TM"] > 0,
        precio_pais["FOB"] / precio_pais["TM"] * 1_000_000,
        0
    )
    precio_pais = precio_pais[precio_pais["Precio"] > 0].sort_values("Precio", ascending=True)

    fig2 = go.Figure(go.Bar(
        y=precio_pais["Pais_Destino"], x=precio_pais["Precio"], orientation="h",
        marker_color="#8b5cf6",
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f} USD/TM<extra></extra>"
    ))
    fig2.update_layout(
        height=400, margin=dict(l=200, t=10, b=30, r=20),
        xaxis_title=f"Precio Implícito de {prod_sel} (USD/TM)",
        plot_bgcolor=PLOT_BG
    )
    fig2.update_xaxes(gridcolor=GRID_COLOR)
    fig2.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig2, use_container_width=True)
