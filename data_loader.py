"""
Módulo compartido: carga de datos y preprocesamiento.
Usado por todos los módulos del dashboard.
Fuente: 06. Export. por Producto Principal, País y Subpartida.xlsx
(convertido a Parquet con etl_excel_to_parquet.py)
"""
import streamlit as st
import pandas as pd
import os

SECTOR_MAP = {
    "11": "Productos Primarios Agrícolas",
    "12": "Silvicultura",
    "13": "Pecuarios",
    "14": "Pesca",
    "15": "Minería y Petróleo",
    "21": "Químicos y Farmacéuticos",
    "22": "Alimentos Procesados",
    "23": "Industrializados",
    "31": "Desperdicios de Papel",
    "32": "Desperdicios de Metales",
    "33": "Otros Desperdicios",
    "41": "Animales Vivos (no alimentación)",
    "-9": "No Definido",
}

GRUPO_MAP = {
    "1101": "Cereales", "1102": "Banano y Plátano", "1103": "Cacao",
    "1104": "Café", "1105": "Frutas", "1107": "Especias",
    "1109": "Fibras naturales", "1110": "Fibras vegetales",
    "1111": "Otros agrícolas", "1201": "Balsa", "1203": "Maderas",
    "1301": "Animales vivos", "1302": "Pieles y cueros", "1303": "Otros pecuarios",
    "1401": "Atún y pescado", "1402": "Camarones", "1403": "Langostas",
    "1404": "Otros piscícolas", "1501": "Petróleo crudo",
    "1502": "Oro y plata", "1503": "Concentrados minerales",
    "1504": "Zinc", "1505": "Sal mineral", "1506": "Otros mineros",
    "2101": "Medicinas", "2102": "Farmacéuticos", "2103": "Otros químicos",
    "2201": "Conservas de frutas", "2202": "Azúcar", "2203": "Melazas",
    "2204": "Café industrializado", "2205": "Elaborados de cacao",
    "2206": "Elaborados de banano", "2207": "Elaborados del mar",
    "2208": "Conservas agrícolas", "2209": "Harinas y cereales",
    "2210": "Carne y lácteos", "2211": "Bebidas",
    "2212": "Aceites vegetales", "2213": "Otros alimenticios",
    "2301": "Alimento para animales", "2303": "Leña y carbón",
    "2304": "Maderas procesadas", "2305": "Artículos de madera",
    "2306": "Derivados de petróleo", "2307": "Vehículos y maquinaria",
    "2308": "Aparatos eléctricos", "2309": "Electrodomésticos",
    "2310": "Sombreros paja toquilla", "2311": "Cestería",
    "2312": "Manufacturas de papel", "2313": "Textiles y prendas",
    "2314": "Cuero, plástico, caucho", "2315": "Artesanía",
    "2316": "Otras mercancías",
    "3101": "Desperdicios de papel", "3201": "Chatarra",
    "3301": "Otros desperdicios", "4101": "Animales vivos no alimentación",
}

# Regiones geográficas – patrones de búsqueda (se busca si el nombre contiene la clave)
# Orden importa: se evalúa de arriba hacia abajo, primera coincidencia gana
_REGION_PATTERNS = [
    # América del Norte
    ("ESTADOS UNIDOS", "América del Norte"),
    ("CANAD", "América del Norte"),
    ("MEXIC", "América del Norte"), ("MÉXIC", "América del Norte"),
    # Europa
    ("ALEMANI", "Europa"), ("ESPAÑ", "Europa"), ("FRANCI", "Europa"),
    ("ITALI", "Europa"), ("HOLANDA", "Europa"), ("PAÍSES BAJOS", "Europa"),
    ("REINO UNIDO", "Europa"), ("BÉLGI", "Europa"), ("BELGI", "Europa"), ("BELG", "Europa"),
    ("RUSI", "Europa"), ("SUIZ", "Europa"), ("PORTUG", "Europa"),
    ("SUECI", "Europa"), ("POLONI", "Europa"), ("GRECI", "Europa"),
    ("TURQU", "Europa"), ("UCRANI", "Europa"), ("NORUEG", "Europa"),
    ("DINAMARC", "Europa"), ("FINLANDI", "Europa"), ("IRLAND", "Europa"),
    ("RUMANI", "Europa"), ("AUSTRI", "Europa"), ("CHECA", "Europa"),
    ("BULGARI", "Europa"), ("ESLOVENI", "Europa"), ("LITUANI", "Europa"),
    ("CROACI", "Europa"), ("MONTENEGR", "Europa"), ("ESTONI", "Europa"),
    ("ALBANI", "Europa"), ("SERBI", "Europa"), ("MALT", "Europa"),
    ("LETONI", "Europa"), ("ESLOVAQU", "Europa"), ("HUNGR", "Europa"),
    ("MACEDONI", "Europa"), ("BOSNIA", "Europa"), ("LUXEMBURG", "Europa"),
    ("ISLANDI", "Europa"), ("LIECHTENSTEIN", "Europa"), ("ANDORR", "Europa"),
    ("SAN MARINO", "Europa"), ("MÓNACO", "Europa"), ("MONACO", "Europa"),
    ("GIBRALTAR", "Europa"), ("SANTA SEDE", "Europa"), ("VATICANO", "Europa"),
    ("FERO", "Europa"), ("YUGOESLAVI", "Europa"), ("BELAR", "Europa"),
    ("MOLDOV", "Europa"), ("GEORGI", "Europa"), ("CHIPRE", "Europa"),
    # Asia
    ("CHINA", "Asia"), ("JAPÓN", "Asia"), ("JAPON", "Asia"),
    ("COREA (SUR", "Asia"), ("COREA DEL SUR", "Asia"),
    ("COREA (NORTE", "Asia"),
    ("INDIA", "Asia"), ("INDONESI", "Asia"),
    ("TAILANDI", "Asia"), ("VIETNAM", "Asia"), ("MALASI", "Asia"),
    ("FILIPIN", "Asia"), ("TAIW", "Asia"), ("SINGAPUR", "Asia"),
    ("HONG KONG", "Asia"), ("MACAO", "Asia"),
    ("PAKIST", "Asia"), ("BANGLADESH", "Asia"), ("SRI LANKA", "Asia"),
    ("CAMBOYA", "Asia"), ("MYANMAR", "Asia"), ("BIRMANIA", "Asia"),
    ("BRUNÉI", "Asia"), ("BRUNEI", "Asia"), ("LAOS", "Asia"),
    ("MONGOLI", "Asia"), ("NEPAL", "Asia"), ("BHUT", "Asia"), ("MALDIV", "Asia"),
    ("KAZAJIST", "Asia"), ("KIRGUIST", "Asia"), ("UZBEKIST", "Asia"),
    ("TAYIKIST", "Asia"), ("TURKMENIST", "Asia"), ("AZERBAIY", "Asia"),
    ("ARMENI", "Asia"), ("AFGANIST", "Asia"),
    # Medio Oriente
    ("ARABIA SAUDITA", "Medio Oriente"), ("EMIRATOS", "Medio Oriente"),
    ("ISRAEL", "Medio Oriente"), ("IRÁN", "Medio Oriente"), ("IRAN", "Medio Oriente"),
    ("IRAK", "Medio Oriente"), ("KUWAIT", "Medio Oriente"),
    ("QATAR", "Medio Oriente"), ("OMÁN", "Medio Oriente"), ("OMAN", "Medio Oriente"),
    ("BAHREIN", "Medio Oriente"), ("BAHRÉIN", "Medio Oriente"),
    ("JORDANI", "Medio Oriente"), ("LÍBANO", "Medio Oriente"), ("LIBANO", "Medio Oriente"),
    ("SIRIA", "Medio Oriente"), ("YEMEN", "Medio Oriente"),
    ("PALESTIN", "Medio Oriente"),
    # Oceanía
    ("AUSTRALIA", "Oceanía"), ("NUEVA ZELAND", "Oceanía"),
    ("PAPÚA", "Oceanía"), ("PAPUA", "Oceanía"),
    ("FIJI", "Oceanía"), ("SAMOA", "Oceanía"),
    ("KIRIBATI", "Oceanía"), ("VANUATU", "Oceanía"),
    ("MARSHALL", "Oceanía"), ("SALOMÓN", "Oceanía"), ("SALOM", "Oceanía"),
    ("MICRONESIA", "Oceanía"), ("PALAU", "Oceanía"), ("NAURU", "Oceanía"),
    ("NIUE", "Oceanía"), ("COOK", "Oceanía"), ("TOKELAU", "Oceanía"),
    ("PITCAIRN", "Oceanía"), ("NORFOLK", "Oceanía"),
    ("POLINESIA", "Oceanía"), ("NUEVA CALEDONI", "Oceanía"),
    ("GUAM", "Oceanía"), ("MARIANAS", "Oceanía"),
    ("PACÍFICO", "Oceanía"), ("COCOS", "Oceanía"),
    # África
    ("SUDÁFRICA", "África"), ("SUDAFRICA", "África"),
    ("EGIPTO", "África"), ("NIGERIA", "África"), ("MARRUECOS", "África"),
    ("KENYA", "África"), ("KENIA", "África"), ("GHANA", "África"),
    ("ARGELIA", "África"), ("COSTA DE MARFIL", "África"),
    ("LIBIA", "África"), ("TÚNEZ", "África"), ("TUNEZ", "África"),
    ("SENEGAL", "África"), ("CAMERÚN", "África"), ("CAMERUN", "África"),
    ("CABO VERDE", "África"), ("SIERRA LEONA", "África"),
    ("GUINEA", "África"),  # cubre Guinea, Guinea Ecuatorial, Guinea Bissau
    ("MADAGASCAR", "África"), ("ETIOPÍA", "África"), ("ETIOP", "África"),
    ("MOZAMBIQUE", "África"), ("ANGOLA", "África"), ("TOGO", "África"),
    ("BENÍN", "África"), ("BENIN", "África"),
    ("CONGO", "África"), ("GABÓN", "África"), ("GABON", "África"),
    ("MAURICIO", "África"), ("MAURITANI", "África"),
    ("NAMIBIA", "África"), ("SUDÁN", "África"), ("SUDAN", "África"),
    ("LIBERIA", "África"), ("UGANDA", "África"), ("TANZANÍA", "África"),
    ("TANZAN", "África"), ("RWANDA", "África"), ("BURUNDI", "África"),
    ("BURKINA", "África"), ("MALÍ", "África"), ("MALI", "África"),
    ("NÍGER", "África"), ("NIGER", "África"),
    ("CHAD", "África"), ("GAMBIA", "África"),
    ("DJIBOUTI", "África"), ("COMORAS", "África"),
    ("SANTO TOMÉ", "África"), ("SANTO TOM", "África"),
    ("SEYCHELLES", "África"), ("SWAZILANDIA", "África"),
    ("LESOTHO", "África"), ("BOTSWANA", "África"),
    ("ZAMBIA", "África"), ("ZIMBABWE", "África"), ("MALAWI", "África"),
    ("CENTROAFRICANA", "África"), ("SAHARA", "África"),
    ("MAYOTE", "África"), ("REUNIÓN", "África"), ("REUNION", "África"),
    # América Latina y Caribe (al final para no capturar falsos positivos)
    ("COLOMBIA", "América Latina"), ("PERÚ", "América Latina"), ("PERU", "América Latina"),
    ("CHILE", "América Latina"), ("ARGENTINA", "América Latina"),
    ("BRASIL", "América Latina"), ("VENEZUELA", "América Latina"),
    ("PANAMÁ", "América Latina"), ("PANAMA", "América Latina"),
    ("GUATEMALA", "América Latina"), ("COSTA RICA", "América Latina"),
    ("HONDURAS", "América Latina"), ("EL SALVADOR", "América Latina"),
    ("NICARAGUA", "América Latina"), ("BOLIVIA", "América Latina"),
    ("PARAGUAY", "América Latina"), ("URUGUAY", "América Latina"),
    ("DOMINICANA", "América Latina"), ("DOMINICA", "América Latina"),
    ("CUBA", "América Latina"), ("PUERTO RICO", "América Latina"),
    ("HAIT", "América Latina"), ("JAMAICA", "América Latina"),
    ("TRINIDAD", "América Latina"), ("BAHAMAS", "América Latina"),
    ("BARBADOS", "América Latina"), ("BÁRB", "América Latina"),
    ("SANTA LUCÍA", "América Latina"), ("SANTA LUC", "América Latina"),
    ("SAN VICENTE", "América Latina"), ("GRANADA", "América Latina"),
    ("ANTIGUA Y BARBUDA", "América Latina"), ("SAINT KITTS", "América Latina"),
    ("BELICE", "América Latina"), ("SURINAM", "América Latina"),
    ("GUYANA", "América Latina"), ("GUAYANA", "América Latina"),
    ("GUADALUPE", "América Latina"), ("MARTINICA", "América Latina"),
    ("ARUBA", "América Latina"), ("CURAZAO", "América Latina"), ("CURACAO", "América Latina"),
    ("ANTILLAS", "América Latina"), ("BONAIRE", "América Latina"),
    ("CAIMÁN", "América Latina"), ("CAIMAN", "América Latina"),
    ("BERMUDA", "América Latina"), ("MONTSERRAT", "América Latina"),
    ("ANGUILA", "América Latina"), ("TURCAS Y CAICOS", "América Latina"),
    ("VÍRGENES", "América Latina"), ("VIRGENES", "América Latina"),
    ("SAN MARTÍN", "América Latina"), ("SAN MART", "América Latina"),
    ("SAINT PIERRE", "América Latina"), ("SAN PEDRO", "América Latina"),
    ("ECUADOR", "América Latina"),
    # Zonas especiales
    ("ZONA FRANCA", "Otros"),
    ("AGUAS INTERNACIONALES", "Otros"),
    ("TERRITORIO BRIT", "Otros"),
    ("GEORGIAS DEL SUR", "Otros"),
]


def _asignar_region(pais):
    """Asigna región geográfica por búsqueda de patrones en el nombre del país."""
    pais_upper = pais.upper()
    for patron, region in _REGION_PATTERNS:
        if patron in pais_upper:
            return region
    return "Otros"


# Códigos de productos petroleros
PETROLERO_CODIGOS = {"150101", "230601"}

# Paleta de colores por sector (para treemaps y sunbursts)
SECTOR_COLORS = {
    "Minería y Petróleo":            "#000000",  # Negro (petróleo)
    "Pesca":                         "#0891b2",  # Cyan (mar)
    "Productos Primarios Agrícolas": "#16a34a",  # Verde (campo)
    "Silvicultura":                  "#15803d",  # Verde oscuro (bosque)
    "Pecuarios":                     "#ca8a04",  # Dorado (ganado)
    "Alimentos Procesados":          "#ea580c",  # Naranja (industria alimentaria)
    "Químicos y Farmacéuticos":      "#dc2626",  # Rojo (química)
    "Industrializados":              "#2563eb",  # Azul (industria)
    "Desperdicios de Papel":         "#78716c",  # Gris piedra
    "Desperdicios de Metales":       "#57534e",  # Gris oscuro
    "Otros Desperdicios":            "#a8a29e",  # Gris claro
    "Animales Vivos (no alimentación)": "#a16207",  # Marrón
    "No Definido":                   "#9ca3af",  # Gris azulado
    "Otro":                          "#d1d5db",  # Gris muy claro
}

# Colores fijos por producto (Top 20 por FOB). Petróleo = negro.
# Los productos fuera de esta lista usarán colores automáticos.
PRODUCT_COLORS = {
    "PETRÓLEO CRUDO":                          "#000000",  # Negro
    "DERIVADOS DE PETRÓLEO":                   "#333333",  # Gris oscuro
    "CAMARONES":                               "#e11d48",  # Rosa fuerte
    "BANANO":                                  "#eab308",  # Amarillo
    "ENLATADOS DE PESCADO":                    "#0891b2",  # Cyan
    "CACAO":                                   "#92400e",  # Marrón
    "FLORES NATURALES":                        "#c026d3",  # Fucsia
    "ORO":                                     "#ca8a04",  # Dorado
    "CONCENTRADO DE PLOMO Y COBRE":            "#6d28d9",  # Violeta
    "OTRAS MANUFACTURAS DE METALES":           "#14b8a6",  # Teal
    "OTROS PRODUCTOS MINEROS":                 "#7c3aed",  # Púrpura
    "EXTRACTOS Y ACEITES VEGETALES":           "#65a30d",  # Lima
    "VEHÍCULOS Y SUS PARTES":                  "#dc2626",  # Rojo
    "MANUFACTURAS DE CUERO, PLÁSTICO Y CAUCHO":"#ea580c",  # Naranja
    "PESCADO":                                 "#0284c7",  # Azul cielo
    "JUGOS Y CONSERVAS DE FRUTAS":             "#16a34a",  # Verde
    "OTRAS MADERAS":                           "#78716c",  # Piedra
    "ELABORADOS DE CACAO":                     "#a16207",  # Marrón claro
    "OTRAS MERCANCÍAS":                        "#64748b",  # Gris azulado
    "ELABORADOS DE BANANO":                    "#d97706",  # Ámbar
}

# Paleta de respaldo para productos sin color asignado
_FALLBACK_COLORS = [
    "#2563eb", "#f59e0b", "#10b981", "#8b5cf6", "#f43f5e",
    "#06b6d4", "#84cc16", "#a855f7", "#14b8a6", "#fb923c",
    "#6366f1", "#22c55e", "#e879f9", "#38bdf8", "#facc15",
]


def get_product_color(product_name, index=0):
    """Retorna el color fijo para un producto, o un color de respaldo."""
    return PRODUCT_COLORS.get(product_name, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])


# Colores fijos por país destino (Top 10 por FOB).
COUNTRY_COLORS = {
    "ESTADOS UNIDOS":          "#1e3a8a",  # Azul marino
    "PANAMÁ":                  "#dc2626",  # Rojo
    "CHINA":                   "#facc15",  # Amarillo dorado
    "PERÚ":                    "#059669",  # Verde esmeralda
    "CHILE":                   "#2563eb",  # Azul
    "COLOMBIA":                "#eab308",  # Amarillo
    "RUSIA":                   "#1d4ed8",  # Azul real
    "ESPAÑA":                  "#f59e0b",  # Naranja
    "ITALIA":                  "#16a34a",  # Verde
    "PAÍSES BAJOS (HOLANDA)":  "#ea580c",  # Naranja oscuro
}


def get_country_color(country_name, index=0):
    """Retorna el color fijo para un país, o un color de respaldo."""
    return COUNTRY_COLORS.get(country_name, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])


@st.cache_data
def load_data():
    """Carga el parquet y agrega columnas de jerarquía y región."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "exportaciones_ecuador.parquet")
    df = pd.read_parquet(path)

    # Limpiar strings (por seguridad, ya se hizo en ETL)
    df["PP"] = df["PP"].str.strip()
    df["Pais_Destino"] = df["Pais_Destino"].str.strip()
    df["Codigo_PP"] = df["Codigo_PP"].astype(str).str.strip()

    # Jerarquía de productos
    df["Cod_Sector"] = df["Codigo_PP"].str[:2]
    df["Cod_Grupo"] = df["Codigo_PP"].str[:4]
    df["Sector"] = df["Cod_Sector"].map(SECTOR_MAP).fillna("Otro")
    df["Grupo"] = df["Cod_Grupo"].map(GRUPO_MAP).fillna("Otro")

    # Región geográfica (búsqueda por patrones para cubrir variantes del BCE)
    df["Region"] = df["Pais_Destino"].apply(_asignar_region)

    # Clasificación petrolero / no petrolero
    df["Tipo"] = df["Codigo_PP"].apply(
        lambda x: "Petrolero" if x in PETROLERO_CODIGOS else "No Petrolero"
    )

    # Convertir FOB: dato original en miles USD → millones USD
    df["FOB"] = df["FOB"] / 1000

    return df


@st.cache_data
def load_data_aggregated():
    """Carga datos agregados a nivel producto-país-mes (sin subpartida).
    Mucho más liviano para visualizaciones que no necesitan detalle de subpartida."""
    df = load_data()
    agg = df.groupby(
        ["Fecha", "Anio", "Mes", "Codigo_PP", "PP", "Pais_Destino",
         "Cod_Sector", "Cod_Grupo", "Sector", "Grupo", "Region", "Tipo"],
        observed=True
    ).agg(
        FOB=("FOB", "sum"),
        TM_Peso_Neto=("TM_Peso_Neto", "sum"),
    ).reset_index()
    return agg


def filtros_sidebar(df, key_prefix="", show_region=False):
    """Renderiza filtros en cascada en el sidebar y retorna df filtrado.

    Cascada: Tipo → Año → Sector → Grupo → Producto → Región → País
    Cada filtro reduce las opciones disponibles en los filtros siguientes.
    """
    st.sidebar.title("Filtros")

    # 1. Tipo petrolero / no petrolero
    tipo_options = ["Todo", "Petrolero", "No Petrolero"]
    tipo_sel = st.sidebar.radio(
        "Tipo de exportación",
        tipo_options,
        index=0,
        horizontal=True,
        key=f"{key_prefix}_tipo"
    )

    # Aplicar tipo para calcular opciones disponibles
    df_disp = df.copy()
    if tipo_sel != "Todo":
        df_disp = df_disp[df_disp["Tipo"] == tipo_sel]

    # 2. Rango de años
    anio_min, anio_max = int(df_disp["Anio"].min()), int(df_disp["Anio"].max())
    rango = st.sidebar.slider("Rango de años", anio_min, anio_max,
                               (anio_min, anio_max), key=f"{key_prefix}_anio")
    df_disp = df_disp[(df_disp["Anio"] >= rango[0]) & (df_disp["Anio"] <= rango[1])]

    # 3. Sector (con código al inicio, ordenado por código, -9 al final)
    sector_opts = df_disp[["Cod_Sector", "Sector"]].drop_duplicates()
    sector_opts["Label"] = sector_opts["Cod_Sector"] + " – " + sector_opts["Sector"]
    sector_opts["_sort"] = sector_opts["Cod_Sector"].apply(lambda x: "ZZZ" if x.startswith("-") else x)
    sector_opts = sector_opts.sort_values("_sort")
    sector_labels = st.sidebar.multiselect(
        "Sector (vacío = todos)",
        sector_opts["Label"].tolist(),
        key=f"{key_prefix}_sector"
    )
    if sector_labels:
        sectores_sel = [l.split(" – ", 1)[1] for l in sector_labels]
        df_disp = df_disp[df_disp["Sector"].isin(sectores_sel)]
    else:
        sectores_sel = []

    # 4. Grupo (con código al inicio, ordenado por código, negativos al final)
    grupo_opts = df_disp[["Cod_Grupo", "Grupo"]].drop_duplicates()
    grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
    grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(lambda x: "ZZZ" if x.startswith("-") else x)
    grupo_opts = grupo_opts.sort_values("_sort")
    grupo_labels = st.sidebar.multiselect(
        "Grupo (vacío = todos)",
        grupo_opts["Label"].tolist(),
        key=f"{key_prefix}_grupo"
    )
    if grupo_labels:
        grupos_sel = [l.split(" – ", 1)[1] for l in grupo_labels]
        df_disp = df_disp[df_disp["Grupo"].isin(grupos_sel)]

    # 5. Producto (opciones filtradas por sector/grupo, ordenado alfabéticamente)
    productos = st.sidebar.multiselect(
        "Producto (vacío = todos)",
        sorted(df_disp["PP"].unique()),
        key=f"{key_prefix}_prod"
    )
    if productos:
        df_disp = df_disp[df_disp["PP"].isin(productos)]

    # 6. Región (opciones filtradas por tipo/sector/producto)
    regiones = []
    if show_region and "Region" in df_disp.columns:
        regiones = st.sidebar.multiselect(
            "Región (vacío = todas)",
            sorted(df_disp["Region"].unique()),
            key=f"{key_prefix}_region"
        )
        if regiones:
            df_disp = df_disp[df_disp["Region"].isin(regiones)]

    # 7. País destino (opciones filtradas por región y todo lo anterior)
    paises = st.sidebar.multiselect(
        "País destino (vacío = todos)",
        sorted(df_disp["Pais_Destino"].unique()),
        key=f"{key_prefix}_pais"
    )
    if paises:
        df_disp = df_disp[df_disp["Pais_Destino"].isin(paises)]

    return df_disp, rango, sectores_sel, productos, paises
