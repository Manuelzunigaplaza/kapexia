# login.py — Sistema de autenticacion basico KAPEXIA
import streamlit as st

USUARIOS = {
    "expeditor": {
        "password": "kapex2024",
        "rol":      "expeditor",
        "nombre":   "Expeditor KAPEXIA",
    },
    "gerente": {
        "password": "gerente2024",
        "rol":      "gerente",
        "nombre":   "Gerente de Proyecto",
    },
    "admin": {
        "password": "admin2024",
        "rol":      "admin",
        "nombre":   "Administrador KAPEXIA",
    },
}

def inicializar_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "usuario_actual" not in st.session_state:
        st.session_state["usuario_actual"] = None
    if "rol_actual" not in st.session_state:
        st.session_state["rol_actual"] = None

def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("##")
        st.title("🏗️ KAPEXIA")
        st.subheader("Capital Projects Execution Platform")
        st.divider()
        usuario  = st.text_input("Usuario", placeholder="expeditor / gerente / admin")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
                st.session_state["autenticado"]    = True
                st.session_state["usuario_actual"] = usuario
                st.session_state["rol_actual"]     = USUARIOS[usuario]["rol"]
                st.session_state["nombre_actual"]  = USUARIOS[usuario]["nombre"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        st.caption("Demo: expeditor/kapex2024 · gerente/gerente2024 · admin/admin2024")

def cerrar_sesion():
    st.session_state["autenticado"]    = False
    st.session_state["usuario_actual"] = None
    st.session_state["rol_actual"]     = None
    st.rerun()

def requiere_rol(roles_permitidos: list) -> bool:
    return st.session_state.get("rol_actual") in roles_permitidos