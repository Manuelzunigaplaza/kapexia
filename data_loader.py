# data_loader.py — Version 2: lee desde SQLite
import pandas as pd
import sqlite3

RUTA_BD     = "kapexia.db"
FECHA_CORTE = pd.Timestamp("2023-06-26")
COL_LLEGADA = "Fecha Proyectada de Recibo en sitio o Fecha Real Recibido en Sitio"

def calcular_semaforo(dias):
    if pd.isna(dias):   return "SIN FECHA"
    elif dias <= 0:     return "VERDE"
    elif dias <= 7:     return "AMARILLO"
    else:               return "ROJO"

def cargar_dataset() -> pd.DataFrame:
    """Lee desde SQLite — no desde el XLSM."""
    conn = sqlite3.connect(RUTA_BD)
    df   = pd.read_sql("SELECT * FROM expediting", conn)
    conn.close()

    # Convertir fechas
    df[COL_LLEGADA] = pd.to_datetime(df[COL_LLEGADA], errors="coerce")

    # Columnas calculadas
    df["dias_atraso"] = (df[COL_LLEGADA] - FECHA_CORTE).dt.days * -1
    df["semaforo"]    = df["dias_atraso"].apply(calcular_semaforo)

    return df

def calcular_kpis(df: pd.DataFrame) -> dict:
    total    = len(df)
    rojos    = (df["semaforo"] == "ROJO").sum()
    verdes   = (df["semaforo"] == "VERDE").sum()
    sin_fecha = (df["semaforo"] == "SIN FECHA").sum()
    return {
        "total_items": total,
        "items_rojo":  int(rojos),
        "items_verde": int(verdes),
        "sin_fecha":   int(sin_fecha),
        "pct_rojo":    round(rojos / total * 100, 1),
        "pct_verde":   round(verdes / total * 100, 1),
    }

if __name__ == "__main__":
    df   = cargar_dataset()
    kpis = calcular_kpis(df)
    print(f"Filas: {df.shape[0]} · Columnas: {df.shape[1]}")
    print(kpis)