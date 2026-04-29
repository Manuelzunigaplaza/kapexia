# app.py — KAPEXIA v3 — Deploy ready
import streamlit as st
import pandas as pd
from data_loader import cargar_dataset, calcular_kpis
from motor_mci import agregar_mci

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
    st.selectbox("Look-Ahead (días)", [30, 60, 90],
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

# ── Tabs ─────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📋 Expediting",
    "🔭 Look-Ahead",
    "🔴 Top MCI"
])

FECHA_CORTE   = pd.Timestamp("2023-06-26")
COL_FECHA_REQ = "Fecha requerida por el proyecto para llegada del material (dd/mm/aaaa)"

with tab1:
    st.subheader("Dataset ECD19004 — Expediting")
    columnas = ["Código de MR", "Descripción del item",
                "Especialidad", "semaforo", "dias_atraso", "mci_score"]
    columnas_disp = [c for c in columnas if c in df_filtrado.columns]
    st.dataframe(df_filtrado[columnas_disp],
                 use_container_width=True, hide_index=True)

with tab2:
    ventana      = st.session_state["ventana_lookahead"]
    fecha_limite = FECHA_CORTE + pd.Timedelta(days=ventana)

    st.subheader(f"🔭 Look-Ahead {ventana} días — Items en ROJO")
    st.caption(f"Materiales requeridos entre {FECHA_CORTE.date()} "
               f"y {fecha_limite.date()}")

    if COL_FECHA_REQ in df.columns:
        df_la = df.copy()
        df_la[COL_FECHA_REQ] = pd.to_datetime(df_la[COL_FECHA_REQ], errors="coerce")
        lookahead = df_la[
            (df_la[COL_FECHA_REQ] >= FECHA_CORTE) &
            (df_la[COL_FECHA_REQ] <= fecha_limite) &
            (df_la["semaforo"] == "ROJO")
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
        demo_la = df[df["semaforo"] == "ROJO"].head(10)
        cols_la = [c for c in ["Código de MR", "Descripción del item",
                                "Especialidad", "dias_atraso", "mci_score"]
                   if c in demo_la.columns]
        st.dataframe(demo_la[cols_la],
                     use_container_width=True, hide_index=True)

with tab3:
    top_mci = df[df["mci_score"] > 0].nlargest(15, "mci_score")
    st.subheader("🔴 Top 15 Items por MCI Score")
    st.caption("Ordenados por criticidad — estos son los que el expeditor "
               "debe atender primero")
    cols_t3 = [c for c in ["Código de MR", "Descripción del item",
                            "Especialidad", "dias_atraso", "mci_score", "semaforo"]
               if c in top_mci.columns]
    st.dataframe(top_mci[cols_t3],
                 use_container_width=True, hide_index=True)

# ── Debug ─────────────────────────────────────────────────
with st.expander("🔧 Debug session_state"):
    st.json({k: str(v) for k, v in st.session_state.items()})