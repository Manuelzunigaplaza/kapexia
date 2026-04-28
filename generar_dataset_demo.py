# generar_dataset_demo.py
# Genera el dataset oficial de demo de KAPEXIA
# Estructura identica al ECD19004 — datos ficticios

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Semilla para reproducibilidad — siempre genera los mismos datos
np.random.seed(42)
random.seed(42)

# ── Parámetros del proyecto demo ──────────────────────────
N_ITEMS = 200
FECHA_INICIO   = datetime(2023, 1, 1)
FECHA_CORTE    = datetime(2023, 6, 26)

# ── Catálogos basados en ECD19004 real ────────────────────
especialidades = {
    "MEC._ACCESORIOS": 0.40,
    "MEC._VÁLVULAS":   0.20,
    "MEC._TUBERÍA":    0.15,
    "INST._Y_CONTROL": 0.12,
    "MEC._ESTÁTICA":   0.05,
    "ELÉCTRICA":       0.04,
    "MEC._ROTATIVA":   0.02,
    "SEG._Y_SCI":      0.02,
}

sistemas = [
    "CRUDE UNIT", "VACUUM UNIT", "UTILITIES",
    "OFFSITES", "TANKAGE", "FLARE SYSTEM"
]

estados_inspeccion = [
    "Liberado", "No requiere inspección",
    "En programación", "Parcial liberado",
    "No Aceptado", "Rechazado"
]

estados_aprovisionamiento = [
    "RECIBIDO EN SITIO", "EN TRÁNSITO",
    "EN FABRICACIÓN", "OC EMITIDA",
    "EN PROCESO DE COMPRA"
]

proveedores = [
    "PROVEEDOR ALPHA S.A.", "BETA INDUSTRIAL LTDA.",
    "GAMMA SUPPLIES INC.", "DELTA EQUIPOS S.A.S.",
    "EPSILON VALVES CO.", "ZETA FITTINGS CORP."
]

# ── Generador de MR codes ──────────────────────────────────
def generar_mr(especialidad, i):
    codigos = {
        "MEC._ACCESORIOS": "PI13",
        "MEC._VÁLVULAS":   "PI14",
        "MEC._TUBERÍA":    "PI15",
        "INST._Y_CONTROL": "IN01",
        "MEC._ESTÁTICA":   "ME01",
        "ELÉCTRICA":       "EL01",
        "MEC._ROTATIVA":   "RO01",
        "SEG._Y_SCI":      "SC01",
    }
    codigo = codigos.get(especialidad, "GE01")
    return f"{i:03d}-MR-{codigo}-{random.randint(100,999):04d}"

# ── Generar filas ──────────────────────────────────────────
rows = []
especialidad_list = random.choices(
    list(especialidades.keys()),
    weights=list(especialidades.values()),
    k=N_ITEMS
)

for i, esp in enumerate(especialidad_list):
    fecha_req = FECHA_INICIO + timedelta(days=random.randint(30, 540))
    fecha_proy = fecha_req + timedelta(days=random.randint(-240, 30))
    dias_atraso = (fecha_proy - FECHA_CORTE).days

    semaforo = random.choices(["VERDE", "ROJO", "AMARILLO"], weights=[65, 25, 10], k=1)[0]

    rows.append({
        "HUB":                    "Downstream",
        "GERENCIA":               "Caribe",
        "Nombre Proyecto":        "KAPEXIA DEMO — Refinería Modelo",
        "Máscara PEP del proyecto": f"RC-EPC-{random.randint(100,999)}",
        "Especialidad":           esp,
        "Código de MR":           generar_mr(esp, i),
        "Ítem MR":                random.randint(1, 50),
        "Descripción del item":   f"ITEM DEMO {i+1} — {esp}",
        "Área de instalación 1 (Sistema)": random.choice(sistemas),
        "Estado del Proceso de Aprovisionamiento": random.choice(estados_aprovisionamiento),
        "Proveedor":              random.choice(proveedores),
        "Fecha requerida":        fecha_req.strftime("%Y-%m-%d"),
        "Fecha proyectada llegada": fecha_proy.strftime("%Y-%m-%d"),
        "Estado de Inspección del Ítem": random.choice(estados_inspeccion),
        "dias_atraso":            dias_atraso,
        "semaforo":               semaforo,
    })

df_demo = pd.DataFrame(rows)

# ── Exportar ───────────────────────────────────────────────
df_demo.to_csv("kapexia_demo_dataset.csv", index=False)

print("=== DATASET DEMO GENERADO ===")
print(f"Items generados : {len(df_demo)}")
print(f"\nEspecialidades:")
print(df_demo["Especialidad"].value_counts())
print(f"\nSemáforo:")
print(df_demo["semaforo"].value_counts())
print(f"\nArchivo guardado: kapexia_demo_dataset.csv")