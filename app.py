# app.py — Version 3: MCI + Look-Ahead integrados
import streamlit as st
import pandas as pd
import sqlite3
from data_loader import cargar_dataset, calcular_kpis
from motor_mci import agregar_mci, PESO_ESPECIALIDAD

st.set_page_config(
    page_title="KAPEXIA",
    page_icon="🏗️",
    layout="wide"
)

# ── Cache ────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = cargar_dataset()
    df = agregar_mci(df)
    return df

# ── Session state ────────────────────────────────────────
if "filtro_especialidad" not in st.session_state:
    st.session_state["filtro_especialidad"] = "Todas"
if "filtro_semaforo" not in st.session_state:
    st.session_state["filtro_semaforo"] = "Todos"
if "ventana_lookahead" not in st.session_state:
    st.session_state["ventana_lookahead"] = 30

# ── Cargar datos ─────────────────────────────────────────
df = cargar_datos()

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.title("🏗️ KAPEXIA")
    st.divider()

    especialidades = ["Todas"] + sorted(df["Especialidad"].unique().tolist())
    st.selectbox("Especialidad", especialidades,
                 key="filtro_especialidad")

    st.selectbox("Semáforo",
                 ["Todos", "VERDE", "AMARILLO", "ROJO", "SIN FECHA"],
                 key="filtro_semaforo")

    st.divider()
    st.selectbox("Look-Ahead (días)",
                 [30, 60, 90],
                 key="ventana_lookahead")

# ── Filtrado ─────────────────────────────────────────────
df_filtrado = df.copy()
if st.session_state["filtro_especialidad"] != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Especialidad"] == st.session_state["filtro_especialidad"]
    ]
if st.session_state["filtro_semaforo"] != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["semaforo"] == st.session_state["filtro_semaforo"]
    ]

# ── KPIs ─────────────────────────────────────────────────
kpis = calcular_kpis(df_filtrado)

st.title("🏗️ KAPEXIA — Dashboard Ejecutivo")
st.caption(f"Mostrando {len(df_filtrado)} de {len(df)} items · "
           f"Fecha de corte: 26/06/2023")
st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Items",    kpis["total_items"])
col2.metric("Items en ROJO",  kpis["items_rojo"],
            delta=f"{kpis['pct_rojo']}%", delta_color="inverse")
col3.metric("Items en VERDE", kpis["items_verde"],
            delta=f"{kpis['pct_verde']}%")
col4.metric("Sin Fecha",      kpis["sin_fecha"])

st.divider()

# ── Tabs: Expediting | Look-Ahead | Top MCI ──────────────
tab1, tab2, tab3 = st.tabs([
    "📋 Expediting",
    "🔭 Look-Ahead",
    "🔴 Top MCI"
])

FECHA_CORTE = pd.Timestamp("2023-06-26")
COL_FECHA_REQ = "Fecha requerida por el proyecto para llegada del material (dd/mm/aaaa)"

with tab1:
    st.subheader("Dataset ECD19004 — Expediting")
    st.dataframe(
        df_filtrado[[
            "Código de MR", "Descripción del item",
            "Especialidad", "semaforo",
            "dias_atraso", "mci_score"
        ]],
        use_container_width=True,
        hide_index=True
    )

with tab2:
    ventana = st.session_state["ventana_lookahead"]
    fecha_limite = FECHA_CORTE + pd.Timedelta(days=ventana)

    df[COL_FECHA_REQ] = pd.to_datetime(df[COL_FECHA_REQ], errors="coerce")
    lookahead = df[
        (df[COL_FECHA_REQ] >= FECHA_CORTE) &
        (df[COL_FECHA_REQ] <= fecha_limite) &
        (df["semaforo"] == "ROJO")
    ].sort_values("mci_score", ascending=False)

    st.subheader(f"🔭 Look-Ahead {ventana} días — Items en ROJO")
    st.caption(f"Materiales requeridos entre {FECHA_CORTE.date()} "
               f"y {fecha_limite.date()}")
    st.metric("Items en ventana", len(lookahead))

    if len(lookahead) > 0:
        st.dataframe(
            lookahead[[
                "Código de MR", "Descripción del item",
                "Especialidad", COL_FECHA_REQ,
                "dias_atraso", "mci_score"
            ]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No hay items críticos en esta ventana")

with tab2:
    ventana = st.session_state["ventana_lookahead"]
    fecha_limite = FECHA_CORTE + pd.Timedelta(days=ventana)

    st.subheader(f"🔭 Look-Ahead {ventana} días — Items en ROJO")
    st.caption(f"Materiales requeridos entre {FECHA_CORTE.date()} y {fecha_limite.date()}")

    if COL_FECHA_REQ in df.columns:
        df[COL_FECHA_REQ] = pd.to_datetime(df[COL_FECHA_REQ], errors="coerce")
        lookahead = df[
            (df[COL_FECHA_REQ] >= FECHA_CORTE) &
            (df[COL_FECHA_REQ] <= fecha_limite) &
            (df["semaforo"] == "ROJO")
        ].sort_values("mci_score", ascending=False)
        st.metric("Items en ventana", len(lookahead))
        if len(lookahead) > 0:
            st.dataframe(
                lookahead[["Código de MR", "Descripción del item",
                           "Especialidad", COL_FECHA_REQ,
                           "dias_atraso", "mci_score"]],
                use_container_width=True, hide_index=True)
        else:
            st.success("✅ No hay items críticos en esta ventana")
    else:
        st.info("ℹ️ Look-ahead disponible con datos reales del proyecto.")
        st.caption("En la versión demo esta funcionalidad muestra datos simulados.")
        demo_lookahead = df[df["semaforo"] == "ROJO"].head(10)
        st.dataframe(demo_lookahead[["Código de MR", "Descripción del item",
                                      "Especialidad", "dias_atraso", "mci_score"]],
                     use_container_width=True, hide_index=True)

# ── Debug ─────────────────────────────────────────────────
with st.expander("🔧 Debug session_state"):
    st.json({k: str(v) for k, v in st.session_state.items()})