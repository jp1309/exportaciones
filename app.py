"""
Dashboard de Exportaciones de Ecuador
Página de inicio con descripción del proyecto, navegación y resumen ejecutivo.
Datos: Ene 2000 – Dic 2025 | Nivel: Producto × País × Subpartida
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from data_loader import load_data_aggregated, filtros_sidebar, PRODUCT_COLORS, get_product_color, get_country_color, REGION_COLORS

st.set_page_config(
    page_title="Inicio – Exportaciones Ecuador",
    page_icon="🇪🇨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetric"] label {
        color: #495057;
        font-size: 0.85rem;
    }
    .stDivider { margin: 0.5rem 0; }
    .module-card {
        background: #f8f9fa;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 10px;
        height: 100%;
    }
    .module-card h4 {
        margin-top: 0;
        color: #1e3a5f;
    }
    .module-card p {
        color: #4a5568;
        font-size: 0.92rem;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────
st.title("Inicio")
st.markdown(
    "### Dashboard de Exportaciones del Ecuador"
)
st.caption(
    "Datos mensuales: Enero 2000 – Diciembre 2025 | "
    "Valores FOB en millones de USD | "
    "Fuente: Banco Central del Ecuador (BCE)"
)

st.divider()

# ── Descripción del proyecto ──────────────────────────────────────────
st.markdown("""
Este dashboard interactivo permite explorar y analizar las **exportaciones del Ecuador**
durante el periodo **2000–2025**. La herramienta ofrece visualizaciones dinámicas para entender
la estructura, evolución y diversificación del comercio exterior ecuatoriano a nivel de
producto principal, país destino y subpartida arancelaria.

Los datos provienen del **Banco Central del Ecuador (BCE)** y abarcan más de **1 millón de registros**
con detalle mensual de valores FOB, volúmenes en toneladas métricas y clasificación arancelaria.
""")

st.divider()

# ── Módulos de visualización ──────────────────────────────────────────
st.subheader("Módulos de visualización")
st.markdown("Navega a cada módulo desde el menú lateral izquierdo.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="module-card">
        <h4>📈 1. Suma Móvil 12M</h4>
        <p><b>Objetivo:</b> Analizar la tendencia de largo plazo de las exportaciones
        eliminando la estacionalidad mediante el cálculo de la suma móvil de 12 meses.
        Permite comparar la evolución por producto, país y sector.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <h4>💲 3. Precio Implícito</h4>
        <p><b>Objetivo:</b> Calcular y monitorear el precio implícito de exportación
        (FOB/TM) con promedio móvil de 12 meses. Incluye detección de outliers,
        bandas de confianza y comparativa por destino.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="module-card">
        <h4>🌳 2. Treemap Jerárquico</h4>
        <p><b>Objetivo:</b> Visualizar la estructura jerárquica de las exportaciones
        (Sector → Grupo → Producto) mediante treemaps y sunbursts interactivos.
        Permite identificar la composición sectorial y su evolución temporal.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <h4>🔍 4. Drilldown Subpartida</h4>
        <p><b>Objetivo:</b> Explorar el detalle granular a nivel de subpartida arancelaria
        para cada producto. Incluye matrices subpartida×país, evolución temporal
        y análisis por destino de exportación.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Cargar datos y filtros ───────────────────────────────────────────
df = load_data_aggregated()
dff, rango, *_ = filtros_sidebar(df, key_prefix="home", show_region=True)

# ── Resumen ejecutivo ─────────────────────────────────────────────────
st.subheader("Resumen ejecutivo")
st.caption(f"Filtro aplicado: {rango[0]}–{rango[1]}")

# ── KPIs principales ─────────────────────────────────────────────────
fob_total = dff["FOB"].sum()
tm_total = dff["TM_Peso_Neto"].sum()
n_prod = dff["PP"].nunique()
n_pais = dff["Pais_Destino"].nunique()

max_anio = dff["Anio"].max()
fob_ultimo = dff[dff["Anio"] == max_anio]["FOB"].sum()
fob_previo = dff[dff["Anio"] == max_anio - 1]["FOB"].sum()
var_fob = ((fob_ultimo - fob_previo) / fob_previo * 100) if fob_previo > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("FOB Total (millones USD)", f"${fob_total:,.1f}")
c2.metric("Volumen Total (TM)", f"{tm_total:,.0f}")
c3.metric(f"FOB {max_anio} (millones USD)", f"${fob_ultimo:,.1f}", f"{var_fob:+.1f}%")
c4.metric("Productos", f"{n_prod}")
c5.metric("Países destino", f"{n_pais}")

st.divider()

# ── Serie anual FOB + Crecimiento ────────────────────────────────────
st.subheader("Exportaciones anuales FOB")

sa = dff.groupby("Anio").agg(FOB=("FOB", "sum"), TM=("TM_Peso_Neto", "sum")).reset_index()
sa["Crec"] = sa["FOB"].pct_change() * 100
crec_min = sa["Crec"].min()
crec_max = sa["Crec"].max()
pad = (crec_max - crec_min) * 0.1
y2_range = [crec_min - pad, crec_max + pad]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(
    x=sa["Anio"], y=sa["FOB"], name="FOB (millones USD)",
    marker_color="#2563eb", opacity=0.85,
    hovertemplate="<b>%{x}</b><br>FOB: $%{y:,.1f} M<extra></extra>"
), secondary_y=False)
fig.add_trace(go.Scatter(
    x=sa["Anio"], y=sa["Crec"], name="Crecimiento %",
    mode="lines+markers",
    line=dict(color="#dc2626", width=2), marker=dict(size=5),
    hovertemplate="<b>%{x}</b><br>Crec: %{y:.1f}%<extra></extra>"
), secondary_y=True)
fig.update_layout(
    height=380,
    yaxis=dict(title="FOB (millones USD)", tickformat=",.1f"),
    yaxis2=dict(title="Crecimiento (%)", overlaying="y", side="right",
                zeroline=True, zerolinecolor="#555", range=y2_range),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
    margin=dict(t=30, b=30),
    plot_bgcolor="white",
)
fig.update_xaxes(gridcolor="#f0f0f0")
fig.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig, use_container_width=True)

# ── Top productos y países lado a lado ───────────────────────────────
st.subheader("Top 10 productos y destinos")
col_l, col_r = st.columns(2)

with col_l:
    tp = dff.groupby("PP")["FOB"].sum().sort_values(ascending=True).tail(10).reset_index()
    colors_p = [get_product_color(p, i) for i, p in enumerate(tp["PP"])]
    fig_p = go.Figure(go.Bar(
        y=tp["PP"], x=tp["FOB"], orientation="h",
        marker_color=colors_p,
        hovertemplate="<b>%{y}</b><br>$%{x:,.1f} M<extra></extra>"
    ))
    fig_p.update_layout(
        height=450, margin=dict(l=200, t=10, b=30, r=20),
        xaxis_title="FOB (millones USD)", plot_bgcolor="white",
    )
    fig_p.update_xaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig_p, use_container_width=True)

with col_r:
    td = dff.groupby("Pais_Destino")["FOB"].sum().sort_values(ascending=True).tail(10).reset_index()
    colors_d = [get_country_color(p, i) for i, p in enumerate(td["Pais_Destino"])]
    fig_d = go.Figure(go.Bar(
        y=td["Pais_Destino"], x=td["FOB"], orientation="h",
        marker_color=colors_d,
        hovertemplate="<b>%{y}</b><br>$%{x:,.1f} M<extra></extra>"
    ))
    fig_d.update_layout(
        height=450, margin=dict(l=200, t=10, b=30, r=20),
        xaxis_title="FOB (millones USD)", plot_bgcolor="white",
    )
    fig_d.update_xaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig_d, use_container_width=True)

st.divider()

# ── Exportaciones por región ─────────────────────────────────────────
st.subheader("Exportaciones por región geográfica")

col_reg1, col_reg2 = st.columns(2)

with col_reg1:
    reg_data = dff.groupby("Region")["FOB"].sum().sort_values(ascending=False).reset_index()
    fig_reg = go.Figure(go.Pie(
        labels=reg_data["Region"], values=reg_data["FOB"],
        marker_colors=[REGION_COLORS.get(r, "#b3b3b3") for r in reg_data["Region"]],
        hole=0.45, textposition="inside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>$%{value:,.1f} M<br>%{percent}<extra></extra>",
    ))
    fig_reg.update_layout(height=380, margin=dict(t=20, b=20), showlegend=True,
                          legend=dict(orientation="v", font=dict(size=10)))
    st.plotly_chart(fig_reg, use_container_width=True)

with col_reg2:
    reg_evol = dff.groupby(["Anio", "Region"])["FOB"].sum().reset_index()
    regiones_ord = reg_evol.groupby("Region")["FOB"].sum().sort_values(ascending=False).index.tolist()
    fig_reg2 = go.Figure()
    for reg_name in reversed(regiones_ord):
        sub = reg_evol[reg_evol["Region"] == reg_name]
        color = REGION_COLORS.get(reg_name, "#b3b3b3")
        fig_reg2.add_trace(go.Scatter(
            x=sub["Anio"], y=sub["FOB"], name=reg_name,
            mode="lines", stackgroup="one",
            line=dict(width=0.5, color=color), fillcolor=color,
            hovertemplate=f"<b>{reg_name}</b><br>$%{{y:,.1f}} M<extra></extra>",
        ))
    fig_reg2.update_layout(
        height=380, margin=dict(t=20, b=30), plot_bgcolor="white",
        yaxis=dict(title="FOB (millones USD)", tickformat=",.1f", gridcolor="#f0f0f0"),
        legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
    )
    fig_reg2.update_xaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig_reg2, use_container_width=True)

st.divider()

# ── Participación por producto (Top 10) ────────────────────────────────
st.subheader("Participación por producto en el tiempo (Top 10)")

cats = dff.groupby("PP")["FOB"].sum().sort_values(ascending=False).head(10).index.tolist()
total_anual = dff.groupby("Anio")["FOB"].sum().rename("Total_General")
area_top = dff[dff["PP"].isin(cats)].groupby(["Anio", "PP"])["FOB"].sum().reset_index()
area_top = area_top.merge(total_anual, on="Anio")
area_top["Participacion"] = area_top["FOB"] / area_top["Total_General"] * 100

# Calcular "Resto" como diferencia
n_resto = dff["PP"].nunique() - len(cats)
resto_label = f"RESTO ({n_resto} productos)"
resto = area_top.groupby("Anio").agg(FOB_top=("FOB", "sum"), Total_General=("Total_General", "first")).reset_index()
resto["PP"] = resto_label
resto["Participacion"] = (resto["Total_General"] - resto["FOB_top"]) / resto["Total_General"] * 100
resto = resto[["Anio", "PP", "Participacion"]]
area_top = area_top[["Anio", "PP", "Participacion"]]
area_data = pd.concat([area_top, resto], ignore_index=True)

all_cats = cats + [resto_label]

fig_part = go.Figure()
for prod in reversed(all_cats):
    sub = area_data[area_data["PP"] == prod]
    color = "#d1d5db" if prod == resto_label else PRODUCT_COLORS.get(prod, "#d1d5db")
    fig_part.add_trace(go.Scatter(
        x=sub["Anio"], y=sub["Participacion"], name=prod,
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color=color),
        fillcolor=color,
        hovertemplate=f"<b>{prod}</b><br>%{{y:.1f}}%<extra></extra>"
    ))
fig_part.update_layout(height=400, margin=dict(t=30, b=30),
                       legend=dict(orientation="h", y=-0.25),
                       plot_bgcolor="white",
                       yaxis=dict(title="Participación (%)", ticksuffix="%",
                                  dtick=10, range=[0, 100]))
fig_part.update_xaxes(gridcolor="#f0f0f0")
fig_part.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig_part, use_container_width=True)

st.divider()

# ── Diversificación temporal ──────────────────────────────────────────
st.subheader("Diversificación: N° de productos y destinos en el tiempo")

div_data = dff.groupby(["Anio"]).agg(
    N_productos=("PP", "nunique"),
    N_destinos=("Pais_Destino", "nunique")
).reset_index()

fig_div = go.Figure()
fig_div.add_trace(go.Scatter(
    x=div_data["Anio"], y=div_data["N_productos"],
    name="N° Productos", mode="lines+markers",
    line=dict(color="#2563eb", width=2)
))
fig_div.add_trace(go.Scatter(
    x=div_data["Anio"], y=div_data["N_destinos"],
    name="N° Destinos", mode="lines+markers",
    line=dict(color="#f59e0b", width=2), yaxis="y2"
))
fig_div.update_layout(
    height=350, margin=dict(t=10, b=30),
    yaxis=dict(title="N° Productos"),
    yaxis2=dict(title="N° Destinos", overlaying="y", side="right"),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
    plot_bgcolor="white"
)
fig_div.update_xaxes(gridcolor="#f0f0f0")
fig_div.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig_div, use_container_width=True)

st.divider()

# ── Fuentes de datos ──────────────────────────────────────────────────
st.subheader("Fuentes de datos")
st.markdown("""
| Fuente | Descripción | Periodo |
|--------|-------------|---------|
| **Banco Central del Ecuador (BCE)** | Exportaciones por Producto Principal, País de Destino y Subpartida Arancelaria | Ene 2000 – Dic 2025 |

Los datos incluyen valores FOB (Free On Board) en millones de USD, volúmenes en toneladas métricas (TM),
y clasificación arancelaria a 6 dígitos con detalle de subpartida.
""")

st.divider()

# ── Autor ─────────────────────────────────────────────────────────────
st.markdown("""
---
<div style="text-align: center; padding: 20px 0; color: #64748b;">
    <p style="font-size: 1.1rem; margin-bottom: 5px;">
        Desarrollado por <b style="color: #1e3a5f;">Juan Pablo Erráez</b>
    </p>
    <p style="font-size: 0.85rem;">
        Dashboard de análisis de exportaciones del Ecuador | 2025
    </p>
</div>
""", unsafe_allow_html=True)
