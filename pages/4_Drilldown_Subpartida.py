"""
Módulo 4: Drilldown interactivo a nivel de Subpartida arancelaria.

Jerarquía de selección: Sector → Grupo → Producto
Al seleccionar un producto, se muestran:
  1. Composición por subpartida (Top 15 por FOB) — bar horizontal
  2. Evolución temporal de las principales subpartidas — líneas por año
  3. Detalle de una subpartida específica:
     - KPIs: FOB total, TM, precio implícito, N° destinos
     - Evolución anual (barras) + Top 10 países destino (barras)

Datos: load_data() — parquet completo con subpartidas (~1.09M filas)
FOB en millones USD | TM en toneladas métricas
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data, filtros_sidebar

st.set_page_config(page_title="Drilldown Subpartida", page_icon="🔍", layout="wide")

PLOT_BG = "white"
GRID_COLOR = "#f0f0f0"

# Usar datos completos (con subpartida)
df = load_data()
dff, rango, *_ = filtros_sidebar(df, key_prefix="drill")

st.title("Drilldown por Subpartida Arancelaria")
st.caption("Explora el detalle a nivel de subpartida arancelaria para cada producto y destino")

# ── Selector cascada Sector → Grupo → Producto ──────────────────────
datos = dff[["Cod_Sector", "Sector", "Cod_Grupo", "Grupo", "PP"]].drop_duplicates()

# Sector: con código, ordenado por código, negativos al final
sector_opts = datos[["Cod_Sector", "Sector"]].drop_duplicates()
sector_opts["Label"] = sector_opts["Cod_Sector"] + " – " + sector_opts["Sector"]
sector_opts["_sort"] = sector_opts["Cod_Sector"].apply(lambda x: "ZZZ" if x.startswith("-") else x)
sector_opts = sector_opts.sort_values("_sort")

col_s, col_g, col_p = st.columns(3)

with col_s:
    sector_sel = st.selectbox("Sector", ["Todos"] + sector_opts["Label"].tolist(), key="drill_sec")

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
    grupo_sel = st.selectbox("Grupo", ["Todos"] + grupo_opts["Label"].tolist(), key="drill_grp")

if grupo_sel != "Todos":
    grupo_nombre = grupo_sel.split(" – ", 1)[1]
    datos_fil = datos_fil[datos_fil["Grupo"] == grupo_nombre]

prods_fil = sorted(datos_fil["PP"].unique())

with col_p:
    prod_sel = st.selectbox("Producto", [""] + prods_fil, key="drill_sel_prod",
                            format_func=lambda x: "Seleccionar producto..." if x == "" else x)

if not prod_sel:
    st.info("Selecciona un producto para explorar sus subpartidas.", icon="👆")
    st.stop()

prod_data = dff[dff["PP"] == prod_sel]

st.markdown(f"**{prod_sel}** — {prod_data['Codigo_Subpartida'].nunique()} subpartidas | "
            f"{prod_data['Pais_Destino'].nunique()} destinos | "
            f"FOB total: ${prod_data['FOB'].sum():,.1f} millones USD")

st.divider()

# ── 1. Composición por subpartida ────────────────────────────────────
st.subheader("1. Composición por subpartida (Top 15)")

top_sub = prod_data.groupby(["Codigo_Subpartida", "Subpartida"]).agg(
    FOB=("FOB", "sum"),
    TM=("TM_Peso_Neto", "sum"),
    Paises=("Pais_Destino", "nunique")
).sort_values("FOB", ascending=False).head(15).reset_index()

fig1 = go.Figure(go.Bar(
    y=top_sub["Subpartida"].str[:50], x=top_sub["FOB"],
    orientation="h", marker_color="#2563eb",
    customdata=top_sub[["Codigo_Subpartida", "TM", "Paises"]],
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Código: %{customdata[0]}<br>"
        "FOB: $%{x:,.0f} M<br>"
        "TM: %{customdata[1]:,.0f}<br>"
        "Países: %{customdata[2]}<extra></extra>"
    )
))
fig1.update_layout(
    height=500, margin=dict(l=300, t=10, b=30, r=20),
    xaxis_title="FOB (millones USD)",
    yaxis=dict(autorange="reversed"),
    plot_bgcolor=PLOT_BG
)
fig1.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig1, width="stretch")

st.divider()

# ── 2. Evolución temporal por subpartida ──────────────────────────────
st.subheader("2. Evolución temporal de las principales subpartidas")

n_sub_evol = st.slider("Subpartidas a mostrar", 3, 8, 5, key="n_sub_evol")
top_sub_names = top_sub["Subpartida"].head(n_sub_evol).tolist()

sub_evol = prod_data[prod_data["Subpartida"].isin(top_sub_names)].groupby(
    ["Anio", "Subpartida"]
)["FOB"].sum().reset_index()

fig2 = px.line(sub_evol, x="Anio", y="FOB", color="Subpartida",
               labels={"FOB": "FOB (millones USD)", "Anio": "Año"},
               color_discrete_sequence=px.colors.qualitative.Bold)
fig2.update_layout(
    height=420, margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=-0.2, font=dict(size=9)),
    plot_bgcolor=PLOT_BG
)
fig2.update_xaxes(gridcolor=GRID_COLOR)
fig2.update_yaxes(gridcolor=GRID_COLOR, tickformat=",.1f")
st.plotly_chart(fig2, width="stretch")

st.divider()

# ── 3. Drilldown a subpartida específica ──────────────────────────────
st.subheader("3. Detalle de una subpartida")

subpartidas_disp = prod_data.groupby("Subpartida")["FOB"].sum().sort_values(ascending=False)
sub_sel = st.selectbox(
    "Seleccionar subpartida",
    subpartidas_disp.index.tolist(),
    key="drill_sub_sel"
)

sub_data = prod_data[prod_data["Subpartida"] == sub_sel]

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("FOB Total (millones USD)", f"${sub_data['FOB'].sum():,.1f}")
col_k2.metric("Volumen Total (TM)", f"{sub_data['TM_Peso_Neto'].sum():,.0f}")
precio_sub = sub_data["FOB"].sum() / sub_data["TM_Peso_Neto"].sum() * 1_000_000 if sub_data["TM_Peso_Neto"].sum() > 0 else 0
col_k3.metric("Precio Implícito", f"${precio_sub:,.0f} USD/TM")
col_k4.metric("N° Destinos", f"{sub_data['Pais_Destino'].nunique()}")

# Evolución temporal
col_a, col_b = st.columns(2)

with col_a:
    sub_evol2 = sub_data.groupby("Anio").agg(
        FOB=("FOB", "sum"), TM=("TM_Peso_Neto", "sum")
    ).reset_index()
    fig4a = go.Figure()
    fig4a.add_trace(go.Bar(
        x=sub_evol2["Anio"], y=sub_evol2["FOB"],
        marker_color="#2563eb",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f} M<extra></extra>"
    ))
    fig4a.update_layout(
        height=350, margin=dict(t=10, b=30),
        yaxis_title="FOB (millones USD)",
        xaxis_title="Año",
        plot_bgcolor=PLOT_BG
    )
    fig4a.update_xaxes(gridcolor=GRID_COLOR)
    fig4a.update_yaxes(gridcolor=GRID_COLOR, tickformat=",.1f")
    st.plotly_chart(fig4a, width="stretch")

with col_b:
    sub_pais = sub_data.groupby("Pais_Destino")["FOB"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig4b = go.Figure(go.Bar(
        y=sub_pais["Pais_Destino"], x=sub_pais["FOB"],
        orientation="h", marker_color="#f59e0b",
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f} M<extra></extra>"
    ))
    fig4b.update_layout(
        height=350, margin=dict(l=180, t=10, b=30, r=20),
        xaxis_title="FOB (millones USD)",
        plot_bgcolor=PLOT_BG
    )
    fig4b.update_xaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig4b, width="stretch")

