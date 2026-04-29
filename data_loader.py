# data_loader.py — Version 5: CSV directo en nube
import pandas as pd
import sqlite3
import os

RUTA_BD      = "kapexia.db"
RUTA_CSV     = "kapexia_demo_dataset.csv"
FECHA_CORTE  = pd.Timestamp("2023-06-26")
COL_LLEGADA  = "Fecha Proyectada de Recibo en sitio o Fecha Real Recibido en Sitio"

def calcular_semaforo(dias):
    if pd.isna(dias):   return "SIN FECHA"
    elif dias <= 0:     return "VERDE"
    elif dias <= 7:     return "AMARILLO"
    else:               return "ROJO"

def cargar_dataset() -> pd.DataFrame:
    try:
        # Intenta leer desde BD — solo funciona si existe Y tiene datos
        if not os.path.exists(RUTA_BD):
            raise FileNotFoundError("Sin BD local")
        conn = sqlite3.connect(f"file:{RUTA_BD}?mode=ro", uri=True)
        df   = pd.read_sql("SELECT * FROM expediting", conn)
        conn.close()
        if len(df) == 0:
            raise ValueError("BD vacia")
        df[COL_LLEGADA]   = pd.to_datetime(df[COL_LLEGADA], errors="coerce")
        df["dias_atraso"] = (df[COL_LLEGADA] - FECHA_CORTE).dt.days * -1
        df["semaforo"]    = df["dias_atraso"].apply(calcular_semaforo)

    except Exception:
        # Fallback: CSV demo para deploy en nube
        df = pd.read_csv(RUTA_CSV)
        df["dias_atraso"] = pd.to_numeric(df["dias_atraso"], errors="coerce")
        if "semaforo" not in df.columns:
            df["semaforo"] = df["dias_atraso"].apply(calcular_semaforo)
        if "mci_score" not in df.columns:
            df["mci_score"] = 0.0

    return df

def calcular_kpis(df: pd.DataFrame) -> dict:
    total     = len(df)
    rojos     = (df["semaforo"] == "ROJO").sum()
    verdes    = (df["semaforo"] == "VERDE").sum()
    sin_fecha = (df["semaforo"] == "SIN FECHA").sum()
    return {
        "total_items": total,
        "items_rojo":  int(rojos),
        "items_verde": int(verdes),
        "sin_fecha":   int(sin_fecha),
        "pct_rojo":    round(float(rojos) / total * 100, 1) if total > 0 else 0,
        "pct_verde":   round(float(verdes) / total * 100, 1) if total > 0 else 0,
    }