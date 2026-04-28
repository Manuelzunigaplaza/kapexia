import pandas as pd

df = pd.read_excel(
    r"C:\Users\Asus\OneDrive\Escritorio\KAPEX\ECD19004_PRTLGV REFINERÍA DE CARTAGENA.xlsm",
    engine="openpyxl"
)

print("=== DIMENSIONES ===")
print(f"Filas    : {df.shape[0]}")
print(f"Columnas : {df.shape[1]}")

print("\n=== PRIMERAS 3 FILAS ===")
print(df.head(3))

print(f"\nTotal filas con datos: {df.shape[0]}")
print(f"\nValores nulos por columna:")
print(df.isnull().sum())
print("\n=== ESTADOS DE INSPECCION ===")
print(df["Estado de Inspección del Ítem"].value_counts())

# Filtrar items en programacion
en_programacion = df[df["Estado de Inspección del Ítem"] == "En programación"]
print(f"\nItems en programacion: {len(en_programacion)}")
print(en_programacion[["Código de MR", "Descripción del item", "Especialidad"]].head(10))