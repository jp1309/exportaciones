"""
ETL: Convierte el archivo Excel de exportaciones (2 sheets) a Parquet optimizado.
Ejecutar una sola vez cuando se actualiza la fuente de datos.

Fuente: "06. Export. por Producto Principal, País y Subpartida.xlsx"
Salida: "exportaciones_ecuador.parquet"
"""
import pandas as pd
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "06. Export. por Producto Principal, País y Subpartida.xlsx")
PARQUET_FILE = os.path.join(BASE_DIR, "exportaciones_ecuador.parquet")

COLUMN_NAMES = [
    "Periodo", "Codigo_PP", "PP", "Pais_Destino",
    "Codigo_Subpartida", "Subpartida", "TM_Peso_Neto", "FOB"
]

MES_MAP = {
    "Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12,
}


def parse_periodo(s):
    """Convierte '2000 / 01 - Ene' -> (2000, 1)"""
    parts = s.split("/")
    anio = int(parts[0].strip())
    mes_part = parts[1].strip()  # '01 - Ene'
    mes_num = int(mes_part.split("-")[0].strip())
    return anio, mes_num


def main():
    print(f"Leyendo sheet 1 de: {EXCEL_FILE}")
    df1 = pd.read_excel(EXCEL_FILE, sheet_name="Columnas", dtype={"Código PP": str, "Código Subpartida": str})
    df1.columns = COLUMN_NAMES
    print(f"  Sheet 1: {len(df1):,} filas")

    print(f"Leyendo sheet 2...")
    df2 = pd.read_excel(EXCEL_FILE, sheet_name="Columnas(1)", header=None,
                        dtype={1: str, 4: str})
    df2.columns = COLUMN_NAMES
    print(f"  Sheet 2: {len(df2):,} filas")

    # Concatenar
    df = pd.concat([df1, df2], ignore_index=True)
    print(f"Total concatenado: {len(df):,} filas")

    # Limpiar strings
    for col in ["PP", "Pais_Destino", "Subpartida", "Periodo"]:
        df[col] = df[col].astype(str).str.strip()

    df["Codigo_PP"] = df["Codigo_PP"].astype(str).str.strip()
    df["Codigo_Subpartida"] = df["Codigo_Subpartida"].astype(str).str.strip()

    # Parsear periodo -> Anio, Mes, Fecha
    parsed = df["Periodo"].apply(parse_periodo)
    df["Anio"] = parsed.apply(lambda x: x[0])
    df["Mes"] = parsed.apply(lambda x: x[1])
    df["Fecha"] = pd.to_datetime(df["Anio"].astype(str) + "-" + df["Mes"].astype(str) + "-01")

    # Asegurar numéricos
    df["FOB"] = pd.to_numeric(df["FOB"], errors="coerce").fillna(0)
    df["TM_Peso_Neto"] = pd.to_numeric(df["TM_Peso_Neto"], errors="coerce").fillna(0)

    # Eliminar filas con código -999 (no definidos) si se desea mantener, dejar
    # Los mantenemos pero marcados

    # Tipos optimizados
    df["Anio"] = df["Anio"].astype("int16")
    df["Mes"] = df["Mes"].astype("int8")
    df["FOB"] = df["FOB"].astype("float32")
    df["TM_Peso_Neto"] = df["TM_Peso_Neto"].astype("float32")

    # Resumen
    print(f"\nRango temporal: {df['Anio'].min()}-{df['Mes'].min():02d} a {df['Anio'].max()}-{df['Mes'].max():02d}")
    print(f"Productos únicos (PP): {df['PP'].nunique()}")
    print(f"Países destino únicos: {df['Pais_Destino'].nunique()}")
    print(f"Subpartidas únicas: {df['Subpartida'].nunique()}")
    print(f"Columnas finales: {list(df.columns)}")
    print(f"Shape: {df.shape}")

    # Guardar
    df.to_parquet(PARQUET_FILE, index=False, engine="pyarrow")
    size_mb = os.path.getsize(PARQUET_FILE) / (1024 * 1024)
    print(f"\nGuardado en: {PARQUET_FILE}")
    print(f"Tamaño: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
