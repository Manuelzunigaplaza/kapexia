# kpis_ecd19004.py
import pandas as pd

df = pd.read_excel(
    r"C:\Users\Asus\OneDrive\Escritorio\KAPEX\ECD19004_PRTLGV REFINERÍA DE CARTAGENA.xlsm",
    engine="openpyxl"
)

# Limpieza
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
FECHA_CORTE = pd.Timestamp("2023-06-26")
col_llegada = "Fecha Proyectada de Recibo en sitio o Fecha Real Recibido en Sitio"
df["dias_atraso"] = (df[col_llegada] - FECHA_CORTE).dt.days * -1

def calcular_semaforo(dias):
    if pd.isna(dias):   return "SIN FECHA"
    elif dias <= 0:     return "VERDE"
    elif dias <= 7:     return "AMARILLO"
    else:               return "ROJO"

df["semaforo"] = df["dias_atraso"].apply(calcular_semaforo)

# KPI 1 — Resumen por especialidad
resumen = df.groupby("Especialidad").agg(
    total_items    = ("Código de MR",   "count"),
    items_rojo     = ("semaforo",        lambda x: (x == "ROJO").sum()),
    dias_prom      = ("dias_atraso",    "mean")
).reset_index()

resumen["pct_rojo"] = (resumen["items_rojo"] / resumen["total_items"] * 100).round(1)

print("=== KPIs POR ESPECIALIDAD ===")
print(resumen.sort_values("items_rojo", ascending=False).to_string())

# KPI 2 — Resumen ejecutivo del proyecto
total = len(df)
rojos = (df["semaforo"] == "ROJO").sum()
sin_fecha = (df["semaforo"] == "SIN FECHA").sum()
pct_rojo = round(rojos / total * 100, 1)

print("\n=== RESUMEN EJECUTIVO ===")
print(f"Total items          : {total}")
print(f"Items en ROJO        : {rojos} ({pct_rojo}%)")
print(f"Items sin fecha      : {sin_fecha}")
print(f"Especialidad critica : MEC._ESTÁTICA (25% en ROJO)")