"""
Módulo 1: Suma móvil 12 meses de exportaciones FOB y Volumen.
Suaviza estacionalidad y permite identificar tendencias de largo plazo.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data_aggregated, filtros_sidebar, get_product_color, get_country_color

st.set_page_config(page_title="Suma Móvil 12M", page_icon="📈", layout="wide")

df = load_data_aggregated()
dff, rango, sectores, productos, paises = filtros_sidebar(df, key_prefix="movil", show_region=True)

st.title("Suma Móvil 12 Meses")
st.caption("Suma acumulada de 12 meses para suavizar estacionalidad y visualizar tendencia")

PLOT_BG = "white"
GRID_COLOR = "#f0f0f0"

# ── 1. Suma móvil 12M total ─────────────────────────────────────────
st.subheader("1. Suma móvil 12M – Total exportaciones")

serie = dff.groupby("Fecha").agg(
    FOB=("FOB", "sum"),
    TM=("TM_Peso_Neto", "sum")
).sort_index().reset_index()

serie["FOB_12M"] = serie["FOB"].rolling(12, min_periods=12).sum()
serie["TM_12M"] = serie["TM"].rolling(12, min_periods=12).sum()

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["FOB_12M"], name="FOB suma móvil 12M",
    line=dict(color="#2563eb", width=2.5),
    fill="tozeroy", fillcolor="rgba(37,99,235,0.06)",
    hovertemplate="%{x|%b %Y}: $%{y:,.1f} M<extra></extra>",
), secondary_y=False)
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["TM_12M"], name="Volumen suma móvil 12M (TM)",
    line=dict(color="#f59e0b", width=2, dash="dot"),
    hovertemplate="%{x|%b %Y}: %{y:,.0f} TM<extra></extra>",
), secondary_y=True)

fig1.update_layout(
    height=420, hovermode="x unified", margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=1.1), plot_bgcolor=PLOT_BG
)
fig1.update_yaxes(title_text="FOB (millones USD)", secondary_y=False,
                  gridcolor=GRID_COLOR, tickformat=",.1f")
fig1.update_yaxes(title_text="Volumen suma móvil 12M (TM)", secondary_y=True,
                  gridcolor=GRID_COLOR, tickformat=",.0f")
fig1.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig1, width="stretch")

st.divider()

# ── 2. Suma móvil por producto (top N seleccionable) ────────────────
st.subheader("2. Suma móvil 12M por producto")

n_prod = st.slider("Número de productos a mostrar", 3, 10, 5, key="n_movil_prod")

if productos:
    sel_prods = productos[:n_prod]
else:
    sel_prods = dff.groupby("PP")["FOB"].sum().sort_values(ascending=False).head(n_prod).index.tolist()

prod_serie = dff[dff["PP"].isin(sel_prods)].groupby(["Fecha", "PP"]).agg(
    FOB=("FOB", "sum")
).reset_index().sort_values(["PP", "Fecha"])

fig2 = go.Figure()
for i, prod in enumerate(sel_prods):
    sub = prod_serie[prod_serie["PP"] == prod].copy()
    sub["FOB_12M"] = sub["FOB"].rolling(12, min_periods=12).sum()
    fig2.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["FOB_12M"], name=prod,
        line=dict(color=get_product_color(prod, i), width=2),
        hovertemplate=f"<b>{prod}</b><br>%{{x|%b %Y}}: $%{{y:,.1f}} M<extra></extra>"
    ))

fig2.update_layout(
    height=420, hovermode="x unified", margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
    yaxis=dict(title="FOB suma móvil 12M (millones USD)", tickformat=",.1f", gridcolor=GRID_COLOR),
    plot_bgcolor=PLOT_BG
)
fig2.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig2, width="stretch")

st.divider()

# ── 3. Suma móvil por país destino (top N) ──────────────────────────
st.subheader("3. Suma móvil 12M por país destino")

n_pais = st.slider("Número de países a mostrar", 3, 10, 5, key="n_movil_pais")

if paises:
    sel_paises = paises[:n_pais]
else:
    sel_paises = dff.groupby("Pais_Destino")["FOB"].sum().sort_values(ascending=False).head(n_pais).index.tolist()

pais_serie = dff[dff["Pais_Destino"].isin(sel_paises)].groupby(["Fecha", "Pais_Destino"]).agg(
    FOB=("FOB", "sum")
).reset_index().sort_values(["Pais_Destino", "Fecha"])

fig3 = go.Figure()
for i, pais in enumerate(sel_paises):
    sub = pais_serie[pais_serie["Pais_Destino"] == pais].copy()
    sub["FOB_12M"] = sub["FOB"].rolling(12, min_periods=12).sum()
    fig3.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["FOB_12M"], name=pais,
        line=dict(color=get_country_color(pais, i), width=2),
        hovertemplate=f"<b>{pais}</b><br>%{{x|%b %Y}}: $%{{y:,.1f}} M<extra></extra>"
    ))

fig3.update_layout(
    height=420, hovermode="x unified", margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
    yaxis=dict(title="FOB suma móvil 12M (millones USD)", tickformat=",.1f", gridcolor=GRID_COLOR),
    plot_bgcolor=PLOT_BG
)
fig3.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig3, width="stretch")

