# motor_mci.py
# Motor de criticidad MCI de KAPEXIA

import pandas as pd
import sqlite3

RUTA_BD     = "kapexia.db"
FECHA_CORTE = pd.Timestamp("2023-06-26")
COL_LLEGADA = "Fecha Proyectada de Recibo en sitio o Fecha Real Recibido en Sitio"

# Pesos por especialidad — basados en impacto en construccion
PESO_ESPECIALIDAD = {
    "MEC._ACCESORIOS": 1.0,
    "MEC._VÁLVULAS":   1.5,  # mayor impacto operacional
    "MEC._TUBERÍA":    1.2,
    "INST._Y_CONTROL": 1.8,  # instrumentacion es critica
    "MEC._ESTÁTICA":   1.3,
    "MEC._ROTATIVA":   2.0,  # equipos rotativos — maxima criticidad
    "ELÉCTRICA":       1.4,
    "SEG._Y_SCI":      1.6,  # seguridad — muy critico
    "CABLES":          1.1,
    "REPUESTOS":       0.8,
    "UN._PAQUETE":     1.2,
}

# Factor por estado de inspeccion
FACTOR_INSPECCION = {
    "Liberado":               0.5,  # ya liberado — menos urgente
    "No requiere inspección": 0.3,
    "En programación":        1.5,  # pendiente — urgente
    "Parcial liberado":       1.2,
    "No Aceptado":            2.0,  # rechazado — critico
    "Rechazado":              2.5,  # maxima urgencia
}

def calcular_mci(row):
    """Calcula el MCI score para un item."""
    dias = row.get("dias_atraso", 0)
    if pd.isna(dias) or dias <= 0:
        return 0.0

    peso_esp  = PESO_ESPECIALIDAD.get(row.get("Especialidad", ""), 1.0)
    factor_ins = FACTOR_INSPECCION.get(
        row.get("Estado de Inspección del Ítem", ""), 1.0)

    return round(dias * peso_esp * factor_ins, 1)

def agregar_mci(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columna MCI al dataframe."""
    df["mci_score"] = df.apply(calcular_mci, axis=1)
    return df

if __name__ == "__main__":
    # Cargar desde BD
    conn = sqlite3.connect(RUTA_BD)
    df   = pd.read_sql("SELECT * FROM expediting", conn)
    conn.close()

    # Convertir fechas y calcular atraso
    df[COL_LLEGADA] = pd.to_datetime(df[COL_LLEGADA], errors="coerce")
    df["dias_atraso"] = (df[COL_LLEGADA] - FECHA_CORTE).dt.days * -1

    # Calcular MCI
    df = agregar_mci(df)

    # Top 10 items mas criticos
    top10 = df[df["mci_score"] > 0].nlargest(10, "mci_score")

    print("=== TOP 10 ITEMS MAS CRITICOS (MCI) ===")
    print(top10[["Código de MR", "Descripción del item",
                  "Especialidad", "dias_atraso", "mci_score"]].to_string())