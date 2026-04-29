# app.py — KAPEXIA v5 — Motor MCI real + Validación MR→ODB
import streamlit as st
import pandas as pd
from data_loader import cargar_dataset, calcular_kpis
from motor_mci import agregar_mci, validar_mr_vs_odb
from login import inicializar_login, mostrar_login, cerrar_sesion, requiere_rol

st.set_page_config(
    page_title="KAPEXIA",
    page_icon="🏗️",
    layout="wide"
)

# ── Login ────────────────────────────────────────────────
inicializar_login()

if not st.session_state["autenticado"]:
    mostrar_login()
    st.stop()

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
    st.caption("⚡ Demo — 200 items simulados")
    st.divider()

    rol    = st.session_state["rol_actual"]
    nombre = st.session_state.get("nombre_actual", "Usuario")
    st.caption(f"👤 {nombre}")
    st.caption(f"🔑 Rol: {rol.upper()}")
    st.divider()

    especialidades = ["Todas"] + sorted(df["Especialidad"].unique().tolist())
    st.selectbox("Especialidad", especialidades,
                 key="filtro_especialidad")
    st.selectbox("Semáforo",
                 ["Todos", "VERDE", "AMARILLO", "ROJO", "SIN FECHA", "CANCELADO"],
                 key="filtro_semaforo")
    st.divider()
    st.selectbox("Look-Ahead (días)", [30, 60, 90],
                 key="ventana_lookahead")
    st.divider()
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        cerrar_sesion()

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

# ── Tabs por rol ─────────────────────────────────────────
FECHA_CORTE   = pd.Timestamp("2023-06-26")
COL_FECHA_REQ = "Fecha requerida por el proyecto para llegada del material (dd/mm/aaaa)"

if requiere_rol(["admin", "gerente"]):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Expediting",
        "🔭 Look-Ahead",
        "🔴 Top MCI",
        "⚠️ Validación MR→ODB"
    ])
    mostrar_tab4 = True
else:
    tab1, = st.tabs(["📋 Expediting"])
    tab2 = tab3 = tab4 = None
    mostrar_tab4 = False

# ── Tab 1 — Expediting ────────────────────────────────────
with tab1:
    st.subheader("Dataset ECD19004 — Expediting")
    columnas = ["Código de MR", "Descripción del item",
                "Especialidad", "semaforo", "dias_atraso", "mci_score"]
    columnas_disp = [c for c in columnas if c in df_filtrado.columns]
    st.dataframe(df_filtrado[columnas_disp],
                 use_container_width=True, hide_index=True)

# ── Tab 2 — Look-Ahead ───────────────────────────────────
if tab2:
    with tab2:
        ventana      = st.session_state["ventana_lookahead"]
        fecha_limite = FECHA_CORTE + pd.Timedelta(days=ventana)
        st.subheader(f"🔭 Look-Ahead {ventana} días — Items en ROJO")
        st.caption(f"Materiales requeridos entre {FECHA_CORTE.date()} "
                   f"y {fecha_limite.date()}")

        if COL_FECHA_REQ in df.columns:
            df_la = df.copy()
            df_la[COL_FECHA_REQ] = pd.to_datetime(
                df_la[COL_FECHA_REQ], errors="coerce")
            lookahead = df_la[
                (df_la[COL_FECHA_REQ] >= FECHA_CORTE) &
                (df_la[COL_FECHA_REQ] <= fecha_limite) &
                (df_la["semaforo"] == "ROJO")
            ].sort_values("mci_score", ascending=False)
            st.metric("Items en ventana", len(lookahead))
            cols_la = [c for c in ["Código de MR", "Descripción del item",
                                    "Especialidad", "dias_atraso", "mci_score"]
                       if c in lookahead.columns]
            if len(lookahead) > 0:
                st.dataframe(lookahead[cols_la],
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

# ── Tab 3 — Top MCI ──────────────────────────────────────
if tab3:
    with tab3:
        top_mci = df[df["mci_score"] > 0].nlargest(15, "mci_score")
        st.subheader("🔴 Top 15 Items por MCI Score")
        st.caption("Criticidad real: NLR + Estado ODB + Proceso + INCOTERM")
        cols_t3 = [c for c in ["Código de MR", "Descripción del item",
                                "Especialidad", "dias_atraso",
                                "mci_score", "semaforo"]
                   if c in top_mci.columns]
        st.dataframe(top_mci[cols_t3],
                     use_container_width=True, hide_index=True)

# ── Tab 4 — Validación MR→ODB ────────────────────────────
if tab4 and mostrar_tab4:
    with tab4:
        st.subheader("⚠️ Validación MR → ODB")
        st.caption("Gaps detectados automáticamente entre requisiciones "
                   "de ingeniería y órdenes de compra")

        alertas = validar_mr_vs_odb(df)

        if len(alertas) > 0:
            criticos  = alertas[alertas["Prioridad"] == 1]
            moderados = alertas[alertas["Prioridad"] == 2]
            info      = alertas[alertas["Prioridad"] == 3]

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("🔴 Críticos",  len(criticos))
            col_b.metric("🟡 Alertas",   len(moderados))
            col_c.metric("🔵 Info",      len(info))
            st.divider()

            if len(criticos) > 0:
                st.markdown("### 🔴 Gaps Críticos")
                st.dataframe(
                    criticos[["Código MR", "Ítem", "Especialidad",
                               "Tipo Alerta", "Detalle", "Responsable"]],
                    use_container_width=True, hide_index=True)

            if len(moderados) > 0:
                st.markdown("### 🟡 Alertas Moderadas")
                st.dataframe(
                    moderados[["Código MR", "Ítem", "Especialidad",
                                "Tipo Alerta", "Detalle", "Responsable"]],
                    use_container_width=True, hide_index=True)

            if len(info) > 0:
                st.markdown("### 🔵 Para Revisión")
                st.dataframe(
                    info[["Código MR", "Ítem", "Especialidad",
                           "Tipo Alerta", "Detalle", "Responsable"]],
                    use_container_width=True, hide_index=True)
        else:
            st.success("✅ No se detectaron gaps entre MR y ODB")

# ── Debug solo admin ──────────────────────────────────────
if requiere_rol(["admin"]):
    with st.expander("🔧 Debug session_state"):
        st.json({k: str(v) for k, v in st.session_state.items()})