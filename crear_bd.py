# crear_bd.py
# Migra el dataset ECD19004 a SQLite — una sola vez

import pandas as pd
import sqlite3
from data_loader import cargar_dataset

print("Cargando dataset...")
df = cargar_dataset()

print("Conectando a SQLite...")
conn = sqlite3.connect("kapexia.db")

print("Migrando datos...")
df.to_sql("expediting", conn, if_exists="replace", index=False)

# Verificar
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM expediting")
total = cursor.fetchone()[0]

conn.close()
print(f"Base de datos creada: kapexia.db")
print(f"Tabla 'expediting': {total} registros migrados")