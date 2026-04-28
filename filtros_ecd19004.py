import pandas as pd

df = pd.read_excel(
    r"C:\Users\Asus\OneDrive\Escritorio\KAPEX\ECD19004_PRTLGV REFINERÍA DE CARTAGENA.xlsm",
    engine="openpyxl"
)

# Limpiar espacios multiples en nombres de columnas
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

# Tecnica 1 — Columnas clave del dashboard
columnas_clave = [
    "Código de MR",
    "Descripción del item",
    "Especialidad",
    "Estado de Inspección del Ítem",
    "Proveedor",
    "Fecha entrega O.C."
]
df_reducido = df[columnas_clave]
print("=== TABLA REDUCIDA (6 columnas) ===")
print(df_reducido.head(5))

# Tecnica 2 — Items criticos
criticos = df[
    (df["Estado de Inspección del Ítem"] == "Rechazado") |
    (df["Estado de Inspección del Ítem"] == "No Aceptado")
]
print(f"\n=== ITEMS CRITICOS: {len(criticos)} ===")

# Tecnica 3 — Items en riesgo
estados_riesgo = ["Rechazado", "No Aceptado", "En programación"]
en_riesgo = df[df["Estado de Inspección del Ítem"].isin(estados_riesgo)]
print(f"=== ITEMS EN RIESGO: {len(en_riesgo)} ===")

# Tecnica 4 — Especialidades del proyecto
print("\n=== ESPECIALIDADES DEL PROYECTO ===")
print(df["Especialidad"].value_counts())

# Filtro combinado: valvulas EN programacion
valvulas_riesgo = df[
    (df["Especialidad"] == "MEC._VÁLVULAS") &
    (df["Estado de Inspección del Ítem"] == "En programación")
]
print(f"\n=== VÁLVULAS EN PROGRAMACION: {len(valvulas_riesgo)} ===")