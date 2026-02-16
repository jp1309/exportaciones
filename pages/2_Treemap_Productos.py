"""
Módulo 2: Treemap jerárquico de productos.
Jerarquía: Sector → Grupo → Producto
Incluye sunburst y evolución de composición sectorial.
Coloreado por sector con paleta discreta.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data_aggregated, filtros_sidebar, SECTOR_COLORS

st.set_page_config(page_title="Treemap Jerárquico", page_icon="🌳", layout="wide")

PLOT_BG = "white"
GRID_COLOR = "#f0f0f0"

df = load_data_aggregated()
dff, rango, *_ = filtros_sidebar(df, key_prefix="tree")

st.title("Treemap Jerárquico de Exportaciones")
st.caption("Estructura: Sector → Grupo → Producto | Basado en códigos arancelarios del BCE")

# ── Selector de métrica ──────────────────────────────────────────────
col_m, col_a = st.columns([1, 2])
with col_m:
    metrica = st.radio("Métrica", ["FOB (millones USD)", "Volumen (TM)"], horizontal=True)
val_col = "FOB" if "FOB" in metrica else "TM_Peso_Neto"

with col_a:
    color_by = st.radio("Color por", ["Sector", "Valor absoluto", "Crecimiento % último año"], horizontal=True)

st.divider()

# ── 1. Treemap completo: Sector → Grupo → Producto ──────────────────
st.subheader("1. Treemap: Sector → Grupo → Producto")

tree_data = dff.groupby(["Sector", "Grupo", "PP"]).agg(
    FOB=("FOB", "sum"),
    TM=("TM_Peso_Neto", "sum")
).reset_index()
# Filtrar filas con valores <= 0 para evitar ZeroDivisionError en treemap
val_filter = "FOB" if val_col == "FOB" else "TM"
tree_data = tree_data[tree_data[val_filter] > 0]

if color_by == "Crecimiento % último año":
    max_anio = dff["Anio"].max()
    curr = dff[dff["Anio"] == max_anio].groupby("PP")[val_col].sum()
    prev = dff[dff["Anio"] == max_anio - 1].groupby("PP")[val_col].sum()
    crec = ((curr - prev) / prev * 100).fillna(0).replace([float('inf'), -float('inf')], 0)
    crec_df = crec.reset_index()
    crec_df.columns = ["PP", "Crecimiento"]
    tree_data = tree_data.merge(crec_df, on="PP", how="left")
    tree_data["Crecimiento"] = tree_data["Crecimiento"].fillna(0).clip(-100, 200)

    fig1 = px.treemap(
        tree_data,
        path=["Sector", "Grupo", "PP"],
        values="FOB" if val_col == "FOB" else "TM",
        color="Crecimiento",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        hover_data={"FOB": ":.1f", "TM": ":.0f"},
    )
elif color_by == "Sector":
    # Coloreado discreto por sector
    fig1 = px.treemap(
        tree_data,
        path=["Sector", "Grupo", "PP"],
        values="FOB" if val_col == "FOB" else "TM",
        color="Sector",
        color_discrete_map=SECTOR_COLORS,
        hover_data={"FOB": ":.1f", "TM": ":.0f"},
    )
else:
    color_col = val_col if val_col == "FOB" else "TM"
    fig1 = px.treemap(
        tree_data,
        path=["Sector", "Grupo", "PP"],
        values="FOB" if val_col == "FOB" else "TM",
        color=color_col,
        color_continuous_scale="Blues" if val_col == "FOB" else "Greens",
        hover_data={"FOB": ":.1f", "TM": ":.0f"},
    )

fig1.update_layout(height=650, margin=dict(t=30, b=10, l=10, r=10))
fig1.update_traces(
    hovertemplate="<b>%{label}</b><br>FOB: $%{customdata[0]:,.1f} M<br>TM: %{customdata[1]:,.0f}<extra></extra>"
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── 2. Treemap por sector + Sunburst ──────────────────────────────────
st.subheader("2. Composición por sector")

col1, col2 = st.columns(2)

with col1:
    sector_data = dff.groupby("Sector").agg(
        FOB=("FOB", "sum"), TM=("TM_Peso_Neto", "sum")
    ).reset_index()
    sector_data = sector_data[sector_data[val_filter] > 0]
    fig2 = px.treemap(
        sector_data, path=["Sector"],
        values="FOB" if val_col == "FOB" else "TM",
        color="Sector",
        color_discrete_map=SECTOR_COLORS,
    )
    fig2.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10),
                       showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    sun_data = dff.groupby(["Sector", "Grupo"]).agg(
        FOB=("FOB", "sum")
    ).reset_index()
    sun_data = sun_data[sun_data["FOB"] > 0]
    fig3 = px.sunburst(
        sun_data, path=["Sector", "Grupo"], values="FOB",
        color="Sector",
        color_discrete_map=SECTOR_COLORS,
    )
    fig3.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10),
                       showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── 3. Evolución de la composición sectorial ─────────────────────────
st.subheader("3. Evolución de la composición sectorial (% del total)")

evol = dff.groupby(["Anio", "Sector"])[val_col].sum().reset_index()
total_anual = evol.groupby("Anio")[val_col].sum().rename("Total")
evol = evol.merge(total_anual, on="Anio")
evol["Share"] = evol[val_col] / evol["Total"] * 100

# Ordenar sectores por importancia para mejor visualización
sector_order = dff.groupby("Sector")[val_col].sum().sort_values(ascending=False).index.tolist()

fig4 = go.Figure()
for sec in reversed(sector_order):
    sub = evol[evol["Sector"] == sec]
    color = SECTOR_COLORS.get(sec, "#d1d5db")
    fig4.add_trace(go.Scatter(
        x=sub["Anio"], y=sub["Share"], name=sec,
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color=color),
        fillcolor=color,
        hovertemplate=f"<b>{sec}</b><br>%{{y:.1f}}%<extra></extra>"
    ))
fig4.update_layout(
    height=420, margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
    yaxis=dict(title="Participación (%)", range=[0, 100], dtick=10, ticksuffix="%"),
    plot_bgcolor=PLOT_BG
)
fig4.update_xaxes(gridcolor=GRID_COLOR)
fig4.update_yaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── 4. Treemap por país destino ──────────────────────────────────────
st.subheader("4. Treemap: Sector → Producto → País destino (Top 15 países)")

top15_paises = dff.groupby("Pais_Destino")["FOB"].sum().sort_values(ascending=False).head(15).index
tree_pais = dff[dff["Pais_Destino"].isin(top15_paises)].groupby(
    ["Sector", "PP", "Pais_Destino"]
).agg(FOB=("FOB", "sum")).reset_index()
tree_pais = tree_pais[tree_pais["FOB"] > 0]

fig5 = px.treemap(
    tree_pais, path=["Sector", "PP", "Pais_Destino"], values="FOB",
    color="Sector",
    color_discrete_map=SECTOR_COLORS,
)
fig5.update_layout(height=650, margin=dict(t=30, b=10, l=10, r=10),
                   showlegend=False)
st.plotly_chart(fig5, use_container_width=True)

# ── 5. Tabla detalle ─────────────────────────────────────────────────
st.divider()
st.subheader("5. Detalle por Sector y Grupo")

tabla = dff.groupby(["Sector", "Grupo", "PP"]).agg(
    FOB=("FOB", "sum"),
    TM=("TM_Peso_Neto", "sum"),
    Paises=("Pais_Destino", "nunique")
).sort_values("FOB", ascending=False).reset_index()
tabla["FOB"] = tabla["FOB"].apply(lambda x: f"{x:,.1f}")
tabla["TM"] = tabla["TM"].apply(lambda x: f"{x:,.0f}")
tabla.columns = ["Sector", "Grupo", "Producto", "FOB (millones USD)", "TM", "N° Países"]

st.dataframe(tabla, use_container_width=True, height=500)
