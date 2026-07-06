import streamlit as st
import pandas as pd


# =========================== FILTRO FECHAS ===========================
def filtro_fechas(df):
    # convertir fechas
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

    # fecha actual
    hoy = pd.Timestamp.now().normalize()

    # última fecha disponible del dataset
    max_fecha_df = df["FECHA"].max().normalize()

    # fecha final inteligente
    fecha_fin_default = min(hoy, max_fecha_df)

    # fecha inicial = últimos 7 días
    fecha_inicio_default = (fecha_fin_default - pd.Timedelta(days=7))

    # título bloque
    st.markdown("""<div class="filter-title">📅 Rango de Fechas</div>""", unsafe_allow_html=True)

    # columnas responsive
    col1, col2 = st.columns([1,1], gap="medium")

    # fecha inicial
    with col1:
        fecha_inicio = st.date_input(
            "Fecha Inicial",
            value=fecha_inicio_default,
            min_value=df["FECHA"].min(),
            max_value=max_fecha_df,
            format="DD/MM/YYYY"
        )
        date1 = pd.to_datetime(
            fecha_inicio
        )
 
    # fecha final
    with col2:
        fecha_fin = st.date_input(
            "Fecha Final",
            value=fecha_fin_default,
            min_value=df["FECHA"].min(),
            max_value=max_fecha_df,
            format="DD/MM/YYYY"
        )
        date2 = pd.to_datetime(
            fecha_fin
        ).replace(
            hour=23,
            minute=59,
            second=59
        )

    # validación
    if fecha_inicio > fecha_fin:
        st.error(
            "❌ Error: La fecha inicial no puede ser mayor que la fecha final."
        )
        st.stop()
    return date1, date2


#====================== FILTRO TIPO DE DOCUMENTO ================
def filtro_tipo_documento():
    st.sidebar.header('Filtros: ')

    tipo_documento = st.sidebar.multiselect(
        '📍 Selecciona Tipo de Documento',
        options=['Factura', 'Boleta', 'Ticket'],
        placeholder='Opciones',
        help='Selecciona uno o más tipos de documento'
    )
    return tipo_documento