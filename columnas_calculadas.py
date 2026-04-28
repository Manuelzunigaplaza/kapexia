# columnas_calculadas.py
import pandas as pd

df = pd.read_excel(
    r"C:\Users\Asus\OneDrive\Escritorio\KAPEX\ECD19004_PRTLGV REFINERÍA DE CARTAGENA.xlsm",
    engine="openpyxl"
)

# Limpiar nombres de columnas
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

# Ver tipo de datos de las columnas de fecha
print("=== TIPOS DE DATOS FECHAS ===")
columnas_fecha = [col for col in df.columns if "fecha" in col.lower() 
                  or "Fecha" in col]
for col in columnas_fecha:
    print(f"{col}: {df[col].dtype}")

# Ver muestra de valores de fecha requerida
print("\n=== MUESTRA FECHA REQUERIDA ===")
print(df["Fecha requerida por el proyecto para llegada del material (dd/mm/aaaa)"].head(10))

from datetime import datetime

# Fecha de hoy como referencia
hoy = pd.Timestamp("2023-06-26")

# Columna 1 — Dias de atraso
# Diferencia entre fecha proyectada de llegada y hoy
col_llegada = "Fecha Proyectada de Recibo en sitio o Fecha Real Recibido en Sitio"
df["dias_atraso"] = (df[col_llegada] - hoy).dt.days * -1

# Columna 2 — Semaforo
def calcular_semaforo(dias):
    if pd.isna(dias):
        return "SIN FECHA"
    elif dias <= 0:
        return "VERDE"
    elif dias <= 7:
        return "AMARILLO"
    else:
        return "ROJO"

df["semaforo"] = df["dias_atraso"].apply(calcular_semaforo)

# Resultado
print("=== SEMAFORO DEL PROYECTO ===")
print(df["semaforo"].value_counts())

print("\n=== MUESTRA CON COLUMNAS CALCULADAS ===")
print(df[["Código de MR", "Descripción del item", 
          "dias_atraso", "semaforo"]].head(10))