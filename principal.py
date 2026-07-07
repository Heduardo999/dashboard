import datetime
import time
import math
import base64

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import streamlit as st
import streamlit.components.v1 as components

from dateutil.relativedelta import relativedelta
from numerize.numerize import numerize
from streamlit_option_menu import option_menu

from reportes import crear_pdf_reporte
from email_sender import enviar_email
from whatsapp_sender import enviar_whatsapp
from auth import login, logout, show_login_error, show_login_success

from componentes.filtros import filtro_fechas, filtro_tipo_documento
from componentes.metricas import metricas, metricas_vendedores, metricas_productos
from componentes.loader import show_overlay_loader
from componentes.data_loader import (cargar_ventas, cargar_pagos, cargar_productos)

from componentes.graficos import (
    graph_time_dia,
    graph_time_mes,
    graph_categoria,
    graph_vendedor,
    graph_tipo_pago,
    graph_anulados,
    graph_ranking_vendedores,
    graph_participacion_vendedor,
    graph_productividad_vendedores,
    graph_ticket_promedio_vendedor,
    graph_gestion_comercial_anulados,
    graph_gestion_comercial_descuentos,
    graph_ranking_productos,
    graph_participacion_productos,
    graph_alta_rotacion_productos,
    graph_productos_rentables,
    graph_valor_inventario
)

from componentes.tablas import (
    tabla_productos,
    tabla_baja_rotacion,
    tabla_stock_critico,
    tabla_sin_stock,
    tabla_sin_movimiento,
    tabla_margen_bajo,
)

from Tools import (
    aplicar_filtros,
    agregar_fila_totales,
    download_csv_from_df,
    limpiar_nombre_vendedor,
    render_divider,
    styled_dataframe,
)

from componentes.metricas import metricas


# ====================== CONFIG ======================
st.set_page_config(page_title='Dashboard', page_icon='🌎', layout='wide'
)


# ====================== CARGAR CSS ======================
def cargar_css():
    with open("assets/estilos.css", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

cargar_css()


# ====================== CARGAR LOGO ======================
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:

        return base64.b64encode(
            img_file.read()
        ).decode()

logo = get_base64_image("assets/logoRF.png")


# ====================== CARGAR BOOTSTRAP ======================
st.markdown("""
    <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
""", unsafe_allow_html=True)


# ====================== SESSION ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "loading" not in st.session_state:
    st.session_state.loading = False


# ====================== LOGIN ======================
def render_login():
    col1, col2, col3 = st.columns([1, 0.65, 1])
    with col2:
        st.markdown(f"""
            <div class="login-card">
                <div class="login-logo">
                    <img src="data:image/png;base64,{logo}">
                </div>
                <div class="login-title">
                    EL MUNDO DEL CELULAR
                </div>
                <div class="login-subtitle">
                    Business Intelligence Dashboard
                </div>
            </div>
        """, unsafe_allow_html=True)

        usuario = st.text_input("Usuario", placeholder="Ingrese su usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña",
                                    key="login_password")

        login_btn = st.button("Ingresar", use_container_width=True, type="primary")

        if login_btn:
            ok = login(usuario, password)

            if ok:
                st.session_state.loading = True
                st.rerun()
            else:
                show_login_error("Usuario o contraseña incorrectos")



# ====================== SHOW LOGIN ======================
if st.session_state.loading:

    show_overlay_loader("Ingresando...")

    time.sleep(0.8)

    st.session_state.logged_in = True
    st.session_state.loading = False
    st.rerun()

if not st.session_state.logged_in:
    render_login()
    st.stop()


#================== CARGAMOS ARCHIVOS ========================
df = cargar_ventas() # df_ventas
df_dos = cargar_pagos() # df_pagos
df_productos = cargar_productos() # df_productos

#==================== SIDEBAR - LOGO ======================
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo-container">
            <img src="data:image/png;base64,{logo}" class="sidebar-logo">
            <div class="sidebar-date">
                Business Intelligence Dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==================== FILTROS ====================
tipo_documento = filtro_tipo_documento()


# ================== HEADER + PERFIL =================
ultima_fecha = pd.to_datetime(df["FECHA"]).max()
meses_es = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
             7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

fecha_formateada = (
    f"{ultima_fecha.day} "
    f"{meses_es[ultima_fecha.month]} "
    f"{ultima_fecha.year}"
)

col1, col2 = st.columns([8, 2])
with col1:
    st.markdown("""<div class="store-title">🏠 Tienda Av. Larco 986</div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="update-box">
        <div class="update-desktop">
            <div class="update-title">
                Última actualización
            </div>
            <div class="update-date">
                {fecha_formateada}
            </div>
        </div>
        <div class="update-mobile">
            <strong>Última actualización:</strong> {fecha_formateada}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ======================================================================
# =========================== SIDEBAR - MENÚ ===========================
# ======================================================================
def sidebar():
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menú",
            #options=["Ventas", "Productos", "Fuente", "Vendedores"],
            #icons=["cart4", "bag", "p-circle", "people-fill"],
            options=["Ventas", "Productos", "Vendedores"],
            icons=["cart4", "p-circle", "people-fill"],
            menu_icon="cast",
            default_index=0
        )
        st.markdown("<div class='sidebar-logout-space'></div>", unsafe_allow_html=True)

        if st.button(
            "🚪 Cerrar sesión",
            key="sidebar_logout_btn",
            use_container_width=True,
        ):
            logout()
            st.session_state.logged_in = False
            st.rerun()

    # VENTAS 
    if selected == "Ventas":
        st.markdown(f"""<div class="page-title"><i class="bi bi-cart4"></i> Dashboard de {selected}</div>""", unsafe_allow_html=True)
        st.markdown("---")

        # aplicar filtros
        date1, date2 = filtro_fechas(df)

        fecha_min_df = df["FECHA"].min().normalize()
        comparacion_yoy = (date1 - relativedelta(years=1)) >= fecha_min_df

        df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

        if df_filtrado.empty:
            st.warning(
                "⚠️ No existen ventas para los filtros seleccionados. Modifique el rango de fechas o los filtros aplicados."
            )
            st.stop()

        # métricas SIEMPRE
        metricas(df, date1, date2, tipo_documento, comparacion_yoy)

        # validar gráficos
        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados")
        else:
            graph_time_dia(df, date1, date2, tipo_documento)
            graph_time_mes(df, date1, date2, tipo_documento)
            graph_categoria(df, date1, date2, tipo_documento)
            graph_vendedor(df, date1, date2, tipo_documento)
            graph_tipo_pago(df_dos, date1, date2, tipo_documento)
            graph_anulados(df, date1, date2, tipo_documento)

            tabla_productos(df_filtrado)

    # PRODUCTOS
    elif selected == "Fuentes":
        st.markdown(f"""<div class="page-title"><i class="bi bi-bag-fill"></i> Dashboard de {selected}</div>""", unsafe_allow_html=True)
        st.markdown("---")
        #st.info("🚧 Página en construcción")

        # aplicar filtros
        date1, date2 = filtro_fechas(df)

        fecha_min_df = df["FECHA"].min().normalize()
        comparacion_yoy = (date1 - relativedelta(years=1)) >= fecha_min_df

        df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

        if df_filtrado.empty:
            st.warning(
                "⚠️ No existen ventas para los filtros seleccionados. Modifique el rango de fechas o los filtros aplicados."
            )
            st.stop()

        # métricas SIEMPRE
        metricas_productos(df, df_productos, date1, date2, tipo_documento)

        # validar gráficos
        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados")
        else:
            graph_valor_inventario(df_productos, date1, date2, tipo_documento)

    # FUENTE
    elif selected == "Productos":
        st.markdown(f"""<div class="page-title"><i class="bi bi-phone-fill"></i> Dashboard de {selected}</div>""", unsafe_allow_html=True)
        st.markdown("---")

        # aplicar filtros
        date1, date2 = filtro_fechas(df)

        fecha_min_df = df["FECHA"].min().normalize()
        comparacion_yoy = (date1 - relativedelta(years=1)) >= fecha_min_df

        df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

        if df_productos.empty:
            st.warning(
                "⚠️ No existen ventas para los filtros seleccionados. Modifique el rango de fechas o los filtros aplicados."
            )
            st.stop()

        # métricas SIEMPRE
        metricas_productos(df, df_productos, date1, date2, tipo_documento)

        # validar gráficos
        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados")
        else:
            graph_ranking_productos(df, date1, date2, tipo_documento)
            graph_participacion_productos(df, date1, date2, tipo_documento)
            graph_alta_rotacion_productos(df, date1, date2, tipo_documento)
            graph_productos_rentables(df, df_productos, date1, date2, tipo_documento)
        
            tabla_baja_rotacion(df, date1, date2, tipo_documento)
            tabla_stock_critico(df_productos, date1, date2, tipo_documento)
            tabla_sin_stock(df_productos, date1, date2, tipo_documento)
            tabla_sin_movimiento(df, df_productos, date1, date2, tipo_documento)
            tabla_margen_bajo(df, df_productos, date1, date2, tipo_documento)
            #tabla_valor_inventario(df_productos, date1, date2, tipo_documento)

    # VENDEDORES
    elif selected == "Vendedores":
        st.markdown(f"""<div class="page-title"><i class="bi bi-people-fill"></i> Dashboard de {selected}</div>""", unsafe_allow_html=True)
        st.markdown("---")

        # aplicar filtros
        date1, date2 = filtro_fechas(df)

        fecha_min_df = df["FECHA"].min().normalize()
        comparacion_yoy = (
            date1 - relativedelta(years=1)
        ) >= fecha_min_df

        df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

        if df_filtrado.empty:
            st.warning(
                "⚠️ No existen ventas para los filtros seleccionados. Modifique el rango de fechas o los filtros aplicados."
            )
            st.stop()

        # métricas SIEMPRE
        metricas_vendedores(df, date1, date2, tipo_documento, comparacion_yoy)

        # validar gráficos
        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados")
        else:
            graph_ranking_vendedores(df, date1, date2, tipo_documento)
            graph_participacion_vendedor(df, date1, date2, tipo_documento)
            graph_productividad_vendedores(df, date1, date2, tipo_documento)
            graph_ticket_promedio_vendedor(df, date1, date2, tipo_documento)
            graph_gestion_comercial_anulados(df, date1, date2, tipo_documento)
            graph_gestion_comercial_descuentos(df, date1, date2, tipo_documento)

if __name__ == '__main__':
    sidebar()
