from dateutil.relativedelta import relativedelta
from Tools import aplicar_filtros
import streamlit as st

# ===============================================================
# =========================== MÉTRICAS ==========================
# ===============================================================
def metricas(df, date1, date2, tipo_documento, comparacion_yoy):

    # ========= DATA AÑO ACTUAL =========
    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    date1_ant = date1 - relativedelta(years=1)
    date2_ant = date2 - relativedelta(years=1)

    # ========= DATA AÑO ANTERIOR ==========
    df_anterior = aplicar_filtros(df, date1_ant, date2_ant, tipo_documento)

    tiene_datos_anio_anterior = (not df_anterior.empty)

    # ========== FUNCIÓN VARIACIÓN ============
    def calcular_variacion(actual, anterior):
        if anterior == 0:
            if actual > 0:
                return None
            return 0
        return (
            (actual - anterior)
            / anterior
        ) * 100

    # ============ MÉTRICAS ACTUALES ===========
    ventas_total = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        ["IMPORTE TOTAL DEL COMPROBANTE"]
        .sum()
    )

    num_transacciones = (
        df_filtrado["NÚMERO"]
        .nunique()
    )

    total_items = (
        df_filtrado["CANTIDAD (ITEM)"]
        .sum()
    )

    if num_transacciones > 0:
        promedio_ventas = (
            df_filtrado
            .groupby("NÚMERO")["TOTAL (ITEM)"]
            .sum()
            .mean()
        )

        items_por_transaccion = (
            df_filtrado
            .groupby("NÚMERO")["CANTIDAD (ITEM)"]
            .sum()
            .mean()
        )
    else:
        promedio_ventas = 0
        items_por_transaccion = 0


    # =========== MÉTRICAS AÑO ANTERIOR ========
    ventas_total_ant = (
        df_anterior
        .drop_duplicates(subset=["NÚMERO"])
        ["IMPORTE TOTAL DEL COMPROBANTE"]
        .sum()
    )

    num_transacciones_ant = (
        df_anterior["NÚMERO"]
        .nunique()
    )

    total_items_ant = (
        df_anterior["CANTIDAD (ITEM)"]
        .sum()
    )

    if num_transacciones_ant > 0:
        promedio_ventas_ant = (
            df_anterior
            .groupby("NÚMERO")["TOTAL (ITEM)"]
            .sum()
            .mean()
        )

        items_por_transaccion_ant = (
            df_anterior
            .groupby("NÚMERO")["CANTIDAD (ITEM)"]
            .sum()
            .mean()
        )
    else:
        promedio_ventas_ant = 0
        items_por_transaccion_ant = 0


    # ========= VARIACIONES ==========
    var_ventas = calcular_variacion(
        ventas_total,
        ventas_total_ant
    )

    var_items = calcular_variacion(
        total_items,
        total_items_ant
    )

    var_transacciones = calcular_variacion(
        num_transacciones,
        num_transacciones_ant
    )

    var_promedio = calcular_variacion(
        promedio_ventas,
        promedio_ventas_ant
    )

    var_items_trans = calcular_variacion(
        items_por_transaccion,
        items_por_transaccion_ant
    )


    # ========= VALIDACIÓN YOY =========
    if not comparacion_yoy:
        var_ventas = None
        var_items = None
        var_transacciones = None
        var_promedio = None
        var_items_trans = None

    # =========== VALIDACIÓN QUE TENGA DATOS AÑO ANTERIOR ===========
    if not tiene_datos_anio_anterior:
        var_ventas = None
        var_items = None
        var_transacciones = None
        var_promedio = None
        var_items_trans = None


    # ================ KPIs ================
    st.markdown(
        '<div class="metricas-spacing"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="kpi-contexto">
            KPIs comparados contra el mismo período del año anterior
        </div>
        """,
        unsafe_allow_html=True
    )

    if not tiene_datos_anio_anterior:
        st.warning(
            "ℹ️ No existe información suficiente del año anterior para calcular variaciones."
        )

    col1, col2, col3, col4, col5 = st.columns(5, gap="small")

    with col1:
        st.info(
            "Total en Ventas",
            icon="💰"
        )
        st.metric(
            "Suma Total S/",
            f"{ventas_total:,.2f}",
            None if var_ventas is None else f"{var_ventas:+.1f}%",
        )

    with col2:
        st.info(
            "Items Vendidos",
            icon="📦"
        )
        st.metric(
            "Total Items",
            f"{total_items:,.0f}",
            None if var_items is None else f"{var_items:+.1f}%"
        )

    with col3:
        st.info(
            "Transacciones",
            icon="🛒"
        )
        st.metric(
            "N° Transacciones",
            f"{num_transacciones:,.0f}",
            None if var_transacciones is None else f"{var_transacciones:+.1f}%"
        )

    with col4:
        st.info(
            "Ticket Promedio",
            icon="📊"
        )
        st.metric(
            "Ventas / Transacción",
            f"{promedio_ventas:,.2f}",
            None if var_promedio is None else f"{var_promedio:+.1f}%"
        )

    with col5:
        st.info(
            "Items Promedio",
            icon="📁"
        )
        st.metric(
            "Items / Transacción",
            f"{items_por_transaccion:,.2f}",
            None if var_items_trans is None else f"{var_items_trans:+.1f}%"
        )


    # ============= ALERTAS EJECUTIVAS ==============
    alertas = []

    if (comparacion_yoy and tiene_datos_anio_anterior and var_ventas is not None):
        # crecimiento importante
        if var_ventas > 20:
            alertas.append(
                (
                    "success",
                    f"📈 Las ventas crecieron {var_ventas:.1f}% respecto al mismo período del año anterior."
                )
            )

        # caída de ventas
        if var_ventas < -10:
            alertas.append(
                (
                    "warning",
                    f"⚠️ Las ventas disminuyeron {abs(var_ventas):.1f}% respecto al mismo período del año anterior."
                )
            )

        # caída de transacciones
        if var_transacciones < -10:
            alertas.append(
                (
                    "warning",
                    f"🛒 Las transacciones disminuyeron {abs(var_transacciones):.1f}% respecto al mismo período del año anterior."
                )
            )

        # caída de ticket promedio
        if var_promedio < -10:
            alertas.append(
                (
                    "warning",
                    f"📊 El ticket promedio disminuyó {abs(var_promedio):.1f}% respecto al mismo período del año anterior."
                )
            )

        if alertas:
            with st.expander(f"🚨 Alertas ejecutivas ({len(alertas)})", expanded=False):
                for tipo, mensaje in alertas[:2]:
                    if tipo == "success":
                        st.success(mensaje)
                    elif tipo == "warning":
                        st.warning(mensaje)



# ===============================================================
# ===================== MÉTRICAS VENDEDORES =====================
# ===============================================================
def metricas_vendedores(df, date1, date2, tipo_documento, comparacion_yoy):

    # DATA ACTUAL
    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # DATA AÑO ANTERIOR
    date1_ant = date1 - relativedelta(years=1)
    date2_ant = date2 - relativedelta(years=1)

    df_anterior = aplicar_filtros(df, date1_ant, date2_ant, tipo_documento)

    tiene_datos_anio_anterior = (
        not df_anterior.empty
    )

    # FUNCIÓN VARIACIÓN
    def calcular_variacion(actual, anterior):
        if anterior == 0:
            if actual > 0:
                return None
            return 0
        return (
            (actual - anterior)
            / anterior
        ) * 100

    # DATAFRAME VENDEDORES AÑO ACTUAL
    df_vendedores = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            Ventas=("IMPORTE TOTAL DEL COMPROBANTE", "sum"),
            Transacciones=("NÚMERO", "nunique")
        )
        .reset_index()
    )

    # DATAFRAME VENDEDORES AÑO ANTERIOR
    if tiene_datos_anio_anterior:
        df_vendedores_ant = (
            df_anterior
            .drop_duplicates(subset=["NÚMERO"])
            .groupby("VENDEDOR")
            .agg(
                Ventas=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
            )
            .reset_index()
        )

    # LIMPIAR NOMBRES
    df_vendedores["VENDEDOR"] = (
        df_vendedores["VENDEDOR"]
        .astype(str)
        .str.split(".")
        .str[-1]
    )
    df_vendedores["VENDEDOR"] = (
        df_vendedores["VENDEDOR"]
        .replace({
            "store": "ADMIN",
            "STORE": "ADMIN"
        })
    )

    # METRICAS ACTUALES
    # ---------- KPI 1 ----------
    lider = (
        df_vendedores
        .sort_values("Ventas", ascending=False)
        .iloc[0]
    )
    nombre_lider = lider["VENDEDOR"]
    ventas_lider = lider["Ventas"]

    # ---------- KPI 2 ----------
    ventas_totales = df_vendedores["Ventas"].sum()
    
    participacion_lider = (
        ventas_lider /
        ventas_totales
    ) * 100

    # ---------- KPI 3 ----------
    vendedores_activos = (
        df_vendedores["VENDEDOR"]
        .nunique()
    )

    # ---------- KPI 4 ----------
    productivo = (
        df_vendedores
        .sort_values(
            "Transacciones",
            ascending=False
        )
        .iloc[0]
    )
    nombre_productivo = productivo["VENDEDOR"]
    trans_productivo = productivo["Transacciones"]

    # ---------- KPI 5 ----------
    ticket_vendedor = (
        df_vendedores["Ventas"]
        /
        df_vendedores["Transacciones"]
    )
    idx_ticket = ticket_vendedor.idxmax()

    nombre_ticket = (
        df_vendedores.loc[
            idx_ticket,
            "VENDEDOR"
        ]
    )

    valor_ticket = (
        ticket_vendedor.max()
    )

    # METRICAS AÑO ANTERIOR
    # ---------- KPI 2 ----------
    if tiene_datos_anio_anterior:
        lider_ant = (
            df_vendedores_ant
            .sort_values("Ventas", ascending=False)
            .iloc[0]
        )

        # ---------- KPI 2 ----------
        participacion_lider_ant = (
            lider_ant["Ventas"]
            /
            df_vendedores_ant["Ventas"].sum()
        ) * 100

        # ---------- KPI 3 ----------
        vendedores_activos_ant = (
        df_vendedores_ant["VENDEDOR"]
            .nunique()
        )
    else:
        participacion_lider_ant = 0
        vendedores_activos_ant = 0


    # VARIACIONES
    if tiene_datos_anio_anterior:
        var_participacion = calcular_variacion(
            participacion_lider,
            participacion_lider_ant
        )

        var_activos = calcular_variacion(
            vendedores_activos,
            vendedores_activos_ant
        )
    else:
        var_participacion = None
        var_activos = None

    # VALIDACIÓN YOY
    if not comparacion_yoy:
        var_participacion = None
        var_activos = None
    

    # VALIDACIÓN QUE TENGA DATOS AÑO ANTERIOR
    if not tiene_datos_anio_anterior:
        var_participacion = None
        var_activos = None


    # =====================================================
    # KPIs
    # =====================================================
    st.markdown(
        '<div class="metricas-spacing"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="kpi-contexto">
            KPIs comparados contra el mismo período del año anterior
        </div>
        """,
        unsafe_allow_html=True
    )

    if not tiene_datos_anio_anterior:
        st.warning(
            "ℹ️ No existe información suficiente del año anterior para calcular variaciones."
        )

    col1, col2, col3, col4, col5 = st.columns(5, gap="small")
    with col1:
        st.info(
            "Líder",
            icon="🏆"
        )
        st.metric(
            label="Ventas: "+f"S/ {ventas_lider:,.2f}",
            value=nombre_lider.upper()
        )

    with col2:
        st.info(
            "Participación",
            icon="🥇"
        )
        st.metric(
            label="% Ventas",
            value=f"{participacion_lider:.1f}%",
            delta=None if var_participacion is None else f"{var_participacion:+.1f}%"
        )

    with col3:
        st.info(
            "Activos",
            icon="👥"
        )
        st.metric(
            label="Vendedores",
            value=f"{vendedores_activos:,.0f}",
            delta=None if var_activos is None else f"{var_activos:+.1f}%"
        )

    with col4:
        st.info(
            "Productividad",
            icon="🛒"
        )
        st.metric(
            label="Transacciones: "+f"{trans_productivo:,.0f}",
            value=nombre_lider.upper()
        )

    with col5:
        st.info(
            "Ticket Prom.",
            icon="🎯"
        )
        st.metric(
            label="Ticket Prom.: "+f"S/ {valor_ticket:,.2f}",
            value=nombre_ticket.upper()
        )


    # ==================================================
    # ALERTAS EJECUTIVAS VENDEDORES
    # ==================================================
    alertas = []

    if (comparacion_yoy and tiene_datos_anio_anterior):

        # Alta concentración de ventas
        if participacion_lider >= 70:
            alertas.append(
                (
                    "warning",
                    f"⚠️ Alta dependencia comercial: {nombre_lider.upper()} concentra el {participacion_lider:.1f}% de las ventas."
                )
            )
        elif participacion_lider >= 50:
            alertas.append(
                (
                    "info",
                    f"🏆 {nombre_lider.upper()} lidera con una participación de {participacion_lider:.1f}% de las ventas."
                )
            )

        # Pocos vendedores activos
        if vendedores_activos <= 1:
            alertas.append(
                (
                    "warning",
                    f"👥 Solo {vendedores_activos} vendedor(es) registraron ventas en el período."
                )
            )

        # Productividad
        if nombre_productivo == nombre_lider:
            alertas.append(
                (
                    "success",
                    f"🛒 {nombre_productivo.upper()} lidera tanto en ventas como en número de transacciones."
                )
            )

        # Ticket promedio destacado
        if valor_ticket > 0:
            alertas.append(
                (
                    "success",
                    f"🎯 {nombre_ticket.upper()} registra el ticket promedio más alto: S/ {valor_ticket:,.2f}."
                )
            )

        # MOSTRAR ALERTAS
        if alertas:
            with st.expander(f"🚨 Alertas ejecutivas ({len(alertas)})", expanded=False):
                for tipo, mensaje in alertas[:4]:
                    if tipo == "success":
                        st.success(mensaje)
                    elif tipo == "warning":
                        st.warning(mensaje)
                    elif tipo == "info":
                        st.info(mensaje)



# ===============================================================
# ====================== MÉTRICAS PRODUCTOS =====================
# ===============================================================
def metricas_productos(df_ventas, df_productos, date1, date2, tipo_documento):
    #st.header("📦 Inventario")
    st.markdown("""<div class="block-title">📦 Inventario</div>""", unsafe_allow_html=True)

    # ======== VENTAS FILTRADAS ==========
    df_filtrado = aplicar_filtros(df_ventas, date1, date2, tipo_documento)


    # ======== STOCK DISPONIBLE =========
    df_base = df_productos.copy()


    # ======== METRICAS =========
    total_productos = len(df_productos)

    con_stock = (
        df_productos[
            df_productos["CANTIDAD"] > 0
        ]
        .shape[0]
    )

    unidades = df_base['CANTIDAD'].sum()

    valor_inventario = (
        df_productos["PRECIO DE COMPRA"]
        *
        df_productos["CANTIDAD"]
    ).sum()

    valor_potencial_venta = (
        df_productos["PRECIO DE VENTA"]
        *
        df_productos["CANTIDAD"]
    ).sum()

    margen_potencial = (
        valor_potencial_venta
        -
        valor_inventario
    )


    # =========== KPIs ============
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.metric(
            label="📦 Productos Registrados",
            value=f"{total_productos:,.0f}"
        )

    with col2:
        st.metric(
            label="📦 Productos Con Stock",
            value=f"{con_stock:,.0f}"
        )

    with col3:
        st.metric(
            "📦 Unidades en Inventario",
            f"{unidades:,.0f}"
        )

    col4, col5, col6 = st.columns(3, gap="small")
    with col4:
        st.metric(
            label="💰 Valor Total del Inventario",
            value=f"S/ {valor_inventario:,.2f}"
        )

    with col5:
        st.metric(
            label="💵 Valor Potencial de Venta",
            value=f"S/ {valor_potencial_venta:,.2f}"
        )

    with col6:
        st.metric(
            label="📈 Margen Potencial del Inventario",
            value=f"S/ {margen_potencial:,.2f}"
        )
