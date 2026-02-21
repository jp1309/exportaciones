# Dashboard de Exportaciones del Ecuador

Dashboard interactivo para explorar y analizar las exportaciones del Ecuador durante el periodo **2000–2025**, desarrollado con **Streamlit** y **Plotly**.

Los datos provienen del **Banco Central del Ecuador (BCE)** y abarcan mas de **1 millon de registros** con detalle mensual de valores FOB, volumenes en toneladas metricas y clasificacion arancelaria a nivel de subpartida.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![Plotly](https://img.shields.io/badge/Plotly-5.0+-purple)

---

## Estructura del proyecto

```
exportaciones/
├── app.py                          # Pagina principal (Inicio)
├── data_loader.py                  # Modulo central: carga de datos, filtros, colores
├── etl_excel_to_parquet.py         # ETL: convierte Excel del BCE a Parquet
├── exportaciones_ecuador.parquet   # Datos procesados (~1.09M filas, 11.9 MB)
├── requirements.txt                # Dependencias del proyecto
├── README.md
└── pages/
    ├── 1_Suma_Movil_12M.py         # Modulo 1: Suma movil 12 meses
    ├── 2_Treemap_Productos.py      # Modulo 2: Treemap jerarquico
    ├── 3_Precio_Implicito.py       # Modulo 3: Precio implicito
    └── 4_Drilldown_Subpartida.py   # Modulo 4: Drilldown por subpartida
```

## Modulos

### Inicio (`app.py`)
Pagina principal con resumen ejecutivo del comercio exterior ecuatoriano:
- KPIs principales (FOB total, volumen, variacion interanual, productos, destinos)
- Serie anual de exportaciones FOB con tasa de crecimiento
- Top 10 productos y paises destino
- Distribucion por region geografica (pie chart + area apilada)
- Diversificacion temporal (N° de productos y destinos activos)
- Participacion por producto (Top 10 + Resto, stacked area al 100%)

### 1. Suma Movil 12M
Analiza la tendencia de largo plazo eliminando estacionalidad:
- Suma movil 12M total (FOB + Volumen en doble eje)
- Suma movil por producto (Top N seleccionable, colores fijos)
- Suma movil por pais destino (Top N seleccionable, colores fijos)

### 2. Treemap Jerarquico
Visualiza la estructura de exportaciones por jerarquia arancelaria:
- Treemap completo: Sector → Grupo → Producto (coloreado por sector o valor absoluto)
- Evolucion de la composicion sectorial (% del total, stacked area)
- Treemap por pais destino (Top 15)

### 3. Precio Implicito
Calcula el precio promedio de exportacion (FOB/TM) con suavizado 12M:
- Selector en cascada: Sector → Grupo → Producto
- Selector de rango de anos en sidebar
- Serie temporal con banda de confianza (±2 sigma) y deteccion de outliers
- KPIs: precio actual, variacion 12M, maximo y minimo historico

### 4. Drilldown Subpartida
Explora el detalle granular a nivel de subpartida arancelaria:
- Selector en cascada: Sector → Grupo → Producto
- Composicion por subpartida (Top 15 por FOB, barras horizontales)
- Evolucion temporal de las principales subpartidas (lineas por ano)
- Detalle de una subpartida especifica: KPIs, evolucion anual y top 10 paises destino

## Datos

| Campo | Detalle |
|-------|---------|
| **Fuente** | Banco Central del Ecuador (BCE) |
| **Periodo** | Enero 2000 – Diciembre 2025 |
| **Granularidad** | Mensual, por Producto Principal × Pais Destino × Subpartida |
| **Registros** | ~1,090,000 filas |
| **Variables** | FOB (millones USD), Volumen (TM), Codigo arancelario |

### Jerarquia arancelaria
El codigo de producto (`Codigo_PP`, 6 digitos) define la jerarquia:
- **Sector** (2 primeros digitos): 13 sectores economicos
- **Grupo** (4 primeros digitos): ~50 grupos de productos
- **Producto Principal** (6 digitos): ~70 productos

### Pipeline de datos
```
Excel BCE (2 sheets, 55 MB)
    ↓  etl_excel_to_parquet.py
Parquet (11.9 MB)
    ↓  data_loader.py
    ├── load_data()            → 1.09M filas (con subpartida, para Drilldown)
    └── load_data_aggregated() → 330K filas (sin subpartida, para resto de modulos)
```

## Instalacion

### Requisitos
- Python 3.10 o superior

### Pasos

1. Clonar el repositorio:
```bash
git clone https://github.com/jp1309/exportaciones.git
cd exportaciones
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar el dashboard:
```bash
streamlit run app.py
```

El dashboard se abrira en `http://localhost:8501`.

### Regenerar datos (opcional)
Si se cuenta con el archivo Excel original del BCE:
```bash
python etl_excel_to_parquet.py
```

## Configuracion de colores

El dashboard usa paletas de colores fijas para mantener consistencia visual:

- **~70 productos principales**: colores fijos (petroleo = negro, camarones = rosa, banano = amarillo, etc.)
- **10 paises destino**: colores fijos (EE.UU. = azul marino, Panama = rojo, China = amarillo dorado, etc.)
- **13 sectores**: colores tematicos (Mineria y Petroleo = negro, Pesca = cyan, Agricolas = verde, etc.)

Los colores se definen en `data_loader.py` en los diccionarios `PRODUCT_COLORS`, `COUNTRY_COLORS` y `SECTOR_COLORS`.

## Filtros

### Filtros globales (sidebar)
Disponibles en Inicio, Suma Movil, Treemap y Drilldown:
- Tipo de exportacion (Petrolero / No Petrolero / Todo)
- Rango de anos
- Sector (con codigo numerico)
- Grupo (con codigo numerico)
- Producto
- Region geografica
- Pais destino

### Selectores internos
En Precio Implicito y Drilldown, selectores en cascada Sector → Grupo → Producto dentro de la pagina.

## Tecnologias

- **[Streamlit](https://streamlit.io/)** — Framework para dashboards interactivos
- **[Plotly](https://plotly.com/python/)** — Graficos interactivos (go.Scatter, go.Bar, px.treemap, px.line)
- **[Pandas](https://pandas.pydata.org/)** — Manipulacion y analisis de datos
- **[PyArrow](https://arrow.apache.org/docs/python/)** — Lectura de archivos Parquet

---

Desarrollado por **Juan Pablo Erraez** | 2025
