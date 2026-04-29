# motor_mci.py — VERSION FINAL
# Basado en valores reales del ECD19004 y procedimientos GAB-P-035 / GAB-P-032
import pandas as pd

# ── Pesos por especialidad ─────────────────────────────────────────────────
PESO_ESPECIALIDAD = {
    "MEC._ACCESORIOS": 1.0,
    "MEC._VÁLVULAS":   1.5,
    "MEC._TUBERÍA":    1.2,
    "INST._Y_CONTROL": 1.8,
    "MEC._ESTÁTICA":   1.3,
    "MEC._ROTATIVA":   2.0,
    "ELÉCTRICA":       1.4,
    "SEG._Y_SCI":      1.6,
    "CABLES":          1.1,
    "REPUESTOS":       0.8,
    "UN._PAQUETE":     1.2,
}

# ── Factor NLR — basado en GAB-P-035 ──────────────────────────────────────
# "El material NO puede despacharse sin Nota de Liberación"
FACTOR_NLR = {
    "Liberado":               0.5,
    "No requiere inspección": 0.4,
    "En programación":        3.0,  # BLOQUEANTE — sin NLR
    "Parcial liberado":       2.0,
    "No Aceptado":            4.0,
    "Rechazado":              5.0,
}

# ── Factor Estado ODB — valores reales ECD19004 ────────────────────────────
FACTOR_ESTADO_ODB = {
    "CERRADA":                   0.2,
    "VIGENTE":                   1.0,
    "RECIBIDA PEND. CARGUE SAP": 1.5,  # Gap físico vs SAP
    "VENCIDA":                   3.0,  # CRÍTICO
    "CANCELADA":                 0.1,
}

# ── Factor Proceso — valores reales ECD19004 ───────────────────────────────
FACTOR_PROCESO = {
    "Recibido":                      0.2,
    "En fabricación":                1.5,
    "En planeación abastecimiento":  2.0,
    "En planeación pre-contractual": 2.5,
    "Cancelado":                     0.0,
}

# ── Factor INCOTERM — importados tienen mayor riesgo logístico ─────────────
FACTOR_INCOTERM = {
    "DDP ZF REFINERIA DE CARTAGENA": 1.0,
    "DDP":                           1.0,
    "EXW. HOUSTON, TX – US.":        1.8,
    "EXW OXY MIAMI":                 1.8,
    "FCA HOU,TX GEODIS":             1.6,
    "FCA HOUSTON":                   1.6,
    "EXW":                           1.7,
    "FCA":                           1.5,
    "FCA ONTARIO - CANADA":          1.7,
    "FCA HOU-TX":                    1.6,
    "HOU,TX GEODIS":                 1.6,
}

def calcular_mci(row) -> float:
    """
    MCI = dias_atraso × peso_esp × factor_nlr × factor_proceso × factor_incoterm
    Basado en procedimientos reales GAB-P-035 y GAB-P-032 de Ecopetrol.
    """
    dias    = row.get("dias_atraso", 0)
    proceso = str(row.get("Estado del Proceso de Aprovisionamiento", ""))

    if pd.isna(dias) or dias <= 0:
        return 0.0
    if proceso == "Cancelado":
        return 0.0

    peso_esp       = PESO_ESPECIALIDAD.get(str(row.get("Especialidad", "")), 1.0)
    factor_nlr     = FACTOR_NLR.get(str(row.get("Estado de Inspección del Ítem", "")), 1.0)
    factor_proceso = FACTOR_PROCESO.get(proceso, 1.0)
    factor_odb     = FACTOR_ESTADO_ODB.get(str(row.get("ESTADO DE LA ODB", "")), 1.0)
    factor_inc     = FACTOR_INCOTERM.get(
        str(row.get("Términos de Entrega INCOTERMS / CIUDAD", "")), 1.0)

    return round(dias * peso_esp * factor_nlr * factor_proceso * factor_inc, 1)


def calcular_semaforo_real(row) -> str:
    """
    Semáforo basado en el estado real del proceso — no solo días de atraso.
    Incorpora reglas de negocio de GAB-P-035.
    """
    estado_insp = str(row.get("Estado de Inspección del Ítem", ""))
    estado_odb  = str(row.get("ESTADO DE LA ODB", ""))
    proceso     = str(row.get("Estado del Proceso de Aprovisionamiento", ""))
    mr_lista    = str(row.get("MR lista para ODB?", ""))
    dias        = row.get("dias_atraso", 0)

    # Cancelados — fuera del semáforo
    if proceso == "Cancelado":
        return "CANCELADO"

    # ROJO ABSOLUTO — condiciones bloqueantes del proceso
    if estado_insp in ["Rechazado", "No Aceptado"]:
        return "ROJO"
    if estado_odb == "VENCIDA":
        return "ROJO"
    if estado_insp == "En programación" and not pd.isna(dias) and dias > 0:
        return "ROJO"  # Sin NLR con atraso = bloqueante despacho

    # AMARILLO — situaciones que requieren atención
    if estado_odb == "RECIBIDA PEND. CARGUE SAP":
        return "AMARILLO"  # Físico recibido, pendiente SAP
    if mr_lista == "NO":
        return "AMARILLO"  # MR no lista para ODB

    # VERDE — material disponible
    if proceso == "Recibido":
        return "VERDE"

    # Lógica estándar de días para el resto
    if pd.isna(dias):   return "SIN FECHA"
    elif dias <= 0:     return "VERDE"
    elif dias <= 7:     return "AMARILLO"
    else:               return "ROJO"


def validar_mr_vs_odb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta gaps entre MR y ODB.
    Basado en casos reales documentados del proyecto REFICAR.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    alertas = []

    for _, row in df.iterrows():
        codigo_mr  = row.get("Código de MR", "")
        version_mr = row.get("Versión MR", "")
        item_mr    = row.get("Ítem MR", "")
        cant_mr    = row.get("Cantidad por ítem", None)
        cant_oc    = row.get("Cantidad por ítem OC", None)
        no_oc      = row.get("No. Orden de Compra", None)
        estado_odb = str(row.get("ESTADO DE LA ODB", ""))
        mr_lista   = str(row.get("MR lista para ODB?", ""))
        proceso    = str(row.get("Estado del Proceso de Aprovisionamiento", ""))
        tipo_adq   = str(row.get("Tipo de Adquisición", ""))
        especialidad = str(row.get("Especialidad", ""))

        if proceso == "Cancelado":
            continue

        # GAP 1 — Item de abastecimiento sin ODB
        if pd.isna(no_oc) and tipo_adq == "Abastecimiento":
            alertas.append({
                "Código MR":   codigo_mr,
                "Versión MR":  version_mr,
                "Ítem":        item_mr,
                "Especialidad": especialidad,
                "Tipo Alerta": "🔴 CRÍTICO — Sin ODB",
                "Detalle":     f"Item {item_mr} no tiene ODB asociada",
                "Responsable": "Planeador / Abastecimiento",
                "Prioridad":   1,
            })

        # GAP 2 — MR no lista para ODB
        if mr_lista == "NO" and pd.isna(no_oc):
            alertas.append({
                "Código MR":   codigo_mr,
                "Versión MR":  version_mr,
                "Ítem":        item_mr,
                "Especialidad": especialidad,
                "Tipo Alerta": "🟡 ALERTA — MR no lista para ODB",
                "Detalle":     "Verificar con ingeniería antes de solicitar ODB",
                "Responsable": "Planeador",
                "Prioridad":   2,
            })

        # GAP 3 — ODB VENCIDA
        if estado_odb == "VENCIDA":
            alertas.append({
                "Código MR":   codigo_mr,
                "Versión MR":  version_mr,
                "Ítem":        item_mr,
                "Especialidad": especialidad,
                "Tipo Alerta": "🔴 CRÍTICO — ODB Vencida",
                "Detalle":     f"ODB {no_oc} está VENCIDA. Requiere renovación urgente",
                "Responsable": "Funcionario Autorizado / Expediting",
                "Prioridad":   1,
            })

        # GAP 4 — Material recibido físico sin cargue SAP
        if estado_odb == "RECIBIDA PEND. CARGUE SAP":
            alertas.append({
                "Código MR":   codigo_mr,
                "Versión MR":  version_mr,
                "Ítem":        item_mr,
                "Especialidad": especialidad,
                "Tipo Alerta": "🟡 ALERTA — Pendiente cargue SAP",
                "Detalle":     "Recibido físicamente pero sin ingreso SAP. No disponible para construcción",
                "Responsable": "Bodega / Administrador Inventarios",
                "Prioridad":   2,
            })

        # GAP 5 — Cantidades MR vs OC
        if not pd.isna(cant_mr) and not pd.isna(cant_oc):
            try:
                diff = float(cant_mr) - float(cant_oc)
                if diff > 0:
                    alertas.append({
                        "Código MR":   codigo_mr,
                        "Versión MR":  version_mr,
                        "Ítem":        item_mr,
                        "Especialidad": especialidad,
                        "Tipo Alerta": "🟡 ALERTA — Cantidad OC menor a MR",
                        "Detalle":     f"MR pide {cant_mr}, OC compra {cant_oc}. Faltante: {diff}",
                        "Responsable": "Expediting / Planeador",
                        "Prioridad":   2,
                    })
                elif diff < 0:
                    alertas.append({
                        "Código MR":   codigo_mr,
                        "Versión MR":  version_mr,
                        "Ítem":        item_mr,
                        "Especialidad": especialidad,
                        "Tipo Alerta": "🔵 INFO — Cantidad OC mayor a MR",
                        "Detalle":     f"OC compra {cant_oc}, MR pide {cant_mr}. Verificar autorización",
                        "Responsable": "Planeador",
                        "Prioridad":   3,
                    })
            except (ValueError, TypeError):
                pass

    if alertas:
        return pd.DataFrame(alertas).sort_values("Prioridad").reset_index(drop=True)
    return pd.DataFrame(columns=["Código MR", "Versión MR", "Ítem",
                                  "Especialidad", "Tipo Alerta",
                                  "Detalle", "Responsable", "Prioridad"])


def agregar_mci(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas MCI y semáforo real al dataframe."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    df["mci_score"] = df.apply(calcular_mci, axis=1)
    df["semaforo"]  = df.apply(calcular_semaforo_real, axis=1)
    return df