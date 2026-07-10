import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import plotly.express as px

from dateutil.relativedelta import relativedelta
from reportes import generar_pdf_productos
from streamlit_js_eval import streamlit_js_eval
from Tools import (
    aplicar_filtros,
    styled_dataframe,
    render_divider,
    limpiar_nombre_vendedor,
    obtener_altura_grafico,
)


import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# ============== GRÁFICO VENTAS POR DÍA ===================
# =========================================================
def graph_time_dia(df, date1, date2, tipo_documento):

    # ========== FECHAS ============
    fecha_fin = pd.to_datetime(date2)
    fecha_inicio = (fecha_fin - pd.Timedelta(days=6)).normalize()

    fecha_inicio_anterior = fecha_inicio - relativedelta(years=1)
    fecha_fin_anterior = fecha_fin - relativedelta(years=1)

    # ================= FILTROS =================
    df_base = aplicar_filtros(df, date1, date2, tipo_documento, eliminar_fechas=False)

    # DATA ACTUAL
    df_actual = df_base[
        (df_base["FECHA"] >= fecha_inicio)
        &
        (df_base["FECHA"] <= fecha_fin)
    ].copy()

    # DATA ANTERIOR
    df_anterior = df_base[
        (df_base["FECHA"] >= fecha_inicio_anterior)
        &
        (df_base["FECHA"] <= fecha_fin_anterior)
    ].copy()

    # ==================================================
    # FUNCIÓN AUXILIAR
    # ==================================================
    def preparar_ventas(df_temp, inicio, fin):

        rango = pd.date_range(
            start=inicio,
            end=fin,
            freq="D"
        )

        if df_temp.empty:
            df_vacio = pd.DataFrame({
                "FECHA": rango,
                "VENTAS": 0
            })

            df_vacio["LABEL"] = (
                pd.to_datetime(df_vacio["FECHA"])
                .dt.strftime("%d/%m")
            )

            return df_vacio

        ventas = (
            df_temp
            .drop_duplicates(subset=["NÚMERO"])
            .groupby(df_temp["FECHA"].dt.date)
            ["IMPORTE TOTAL DEL COMPROBANTE"]
            .sum()
            .reset_index()
        )

        ventas.columns = ["FECHA", "VENTAS"]

        ventas = (
            ventas
            .set_index("FECHA")
            .reindex(rango.date, fill_value=0)
            .reset_index()
        )

        ventas.columns = ["FECHA", "VENTAS"]

        ventas["LABEL"] = (
            pd.to_datetime(ventas["FECHA"])
            .dt.strftime("%d/%m")
        )

        return ventas

    # ================= DATA FINAL =================
    ventas_actual = preparar_ventas(
        df_actual,
        fecha_inicio,
        fecha_fin
    )

    ventas_anterior = preparar_ventas(
        df_anterior,
        fecha_inicio_anterior,
        fecha_fin_anterior
    )

    # ================= GRÁFICO =================
    st.subheader("📉 Ventas Diarias")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=ventas_actual["LABEL"],
            y=ventas_actual["VENTAS"],
            mode="lines+markers",
            name=str(fecha_fin.year),
            line=dict(
                color="#FFD700",
                width=3,
                shape="spline"
            ),
            marker=dict(
                size=7,
                color="#FFD700"
            ),
            hovertemplate=
            #"<span style='color:#FFD700'>●</span> " + str(fecha_fin.year) + ": S/ %{y:,.2f}" +
            str(fecha_fin.year) + ": S/ %{y:,.2f}" +
            "<extra></extra>"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ventas_anterior["LABEL"],
            y=ventas_anterior["VENTAS"],
            mode="lines+markers",
            name=str(fecha_fin.year - 1),
            line=dict(
                color="#3B82F6",
                width=2,
                dash="dot",
                shape="spline"
            ),
            marker=dict(
                size=6,
                color="#3B82F6"
            ),
            hovertemplate=
            str(fecha_fin.year - 1) + ": S/ %{y:,.2f}" +
            "<extra></extra>"
        )
    )

    fig.update_layout(
        template="plotly_dark",
        height=360, # 430
        dragmode=False,
        margin=dict(
            l=5,
            r=5,
            t=45,
            b=25
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1E1E1E",
            font_size=13,
            font_color="white"
        ),
        xaxis=dict(
            title="Día",
            showgrid=False,
            showspikes=True,
            spikecolor="rgba(255,255,255,0.35)",
            spikesnap="hovered data",
            spikemode="across",
            spikethickness=1
        ),
        yaxis=dict(
            title="Ventas (S/)",
            gridcolor="rgba(255,255,255,0.06)"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        title=dict(
            text=f"Últimos 7 días vs {fecha_fin.year - 1}",
            font=dict(size=16)
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        }
    )
    render_divider()


# ==================================================================================
# =========================== GRÁFICO DE VENTAS POR MES ============================
# ==================================================================================
def graph_time_mes(df, date1, date2, tipo_documento):

    # ===== FECHAS ACTUALES =====
    fecha_fin_actual = pd.to_datetime(date2)
    fecha_inicio_actual = pd.Timestamp(year=fecha_fin_actual.year, month=1, day=1)

    # ===== FECHAS AÑO ANTERIOR =====
    fecha_inicio_anterior = fecha_inicio_actual - relativedelta(years=1)
    fecha_fin_anterior = fecha_fin_actual - relativedelta(years=1)

    # ================= FILTROS =================
    df_base = aplicar_filtros(df, date1, date2, tipo_documento, eliminar_fechas=False)

    # DATA ACTUAL
    df_actual = df_base[
        (df_base["FECHA"] >= fecha_inicio_actual)
        &
        (df_base["FECHA"] <= fecha_fin_actual)
        ].copy()

    # DATA ANTERIOR
    df_anterior = df_base[
        (df_base["FECHA"] >= fecha_inicio_anterior)
        &
        (df_base["FECHA"] <= fecha_fin_anterior)
    ].copy()

    # =========================================================
    # FUNCIÓN AUXILIAR
    # =========================================================
    def preparar_dataframe(df_data, start_date, end_date):

        if df_data.empty:
            meses = pd.period_range(
                start=start_date.to_period("M"),
                end=end_date.to_period("M"),
                freq="M"
            )

            meses_es = {
                1: "Ene", 2: "Feb", 3: "Mar",
                4: "Abr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Sep",
                10: "Oct", 11: "Nov", 12: "Dic"
            }

            return pd.DataFrame({
                "PERIODO": meses,
                "VENTAS": [0] * len(meses),
                "LABEL": [meses_es[m.month] for m in meses]
            })

        ventas = (
            df_data
            .drop_duplicates(subset=["NÚMERO"])
            .assign(
                PERIODO=lambda x:
                x["FECHA"].dt.to_period("M")
            )
            .groupby(
                "PERIODO",
                as_index=False
            )["IMPORTE TOTAL DEL COMPROBANTE"]
            .sum()
        )

        ventas.columns = ["PERIODO", "VENTAS"]

        meses = pd.period_range(
            start=start_date.to_period("M"),
            end=end_date.to_period("M"),
            freq="M"
        )

        ventas = (
            ventas
            .set_index("PERIODO")
            .reindex(meses, fill_value=0)
            .rename_axis("PERIODO")
            .reset_index()
        )

        meses_es = {
            1: "Ene", 2: "Feb", 3: "Mar",
            4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep",
            10: "Oct", 11: "Nov", 12: "Dic"
        }

        ventas["LABEL"] = (
            ventas["PERIODO"]
            .dt.month
            .map(meses_es)
        )

        return ventas

    # ================= PREPARAR DATA =================
    ventas_actual = preparar_dataframe(
        df_actual,
        fecha_inicio_actual,
        fecha_fin_actual
    )

    ventas_anterior = preparar_dataframe(
        df_anterior,
        fecha_inicio_anterior,
        fecha_fin_anterior
    )

    # =========================================================
    # GRÁFICO
    # =========================================================
    st.subheader("📈 Ventas Mensuales")

    fig = go.Figure()

    # ===== AÑO ACTUAL =====
    fig.add_trace(
        go.Scatter(
            x=ventas_actual["LABEL"],
            y=ventas_actual["VENTAS"],
            mode="lines+markers",
            name=str(fecha_fin_actual.year),
            line=dict(
                color="#FFD700",
                width=3,
                shape="spline",
                smoothing=1.1
            ),
            marker=dict(
                color="#FFD700",
                size=7
            ),
            hovertemplate=
            str(fecha_fin_actual.year) + ": S/ %{y:,.2f}" +
            "<extra></extra>"
        )
    )

    # ===== AÑO ANTERIOR =====
    fig.add_trace(
        go.Scatter(
            x=ventas_anterior["LABEL"],
            y=ventas_anterior["VENTAS"],
            mode="lines+markers",
            name=str(fecha_fin_actual.year - 1),
            line=dict(
                color="#3B82F6",
                width=3,
                dash="dot",
                shape="spline",
                smoothing=1.1
            ),
            marker=dict(
                color="#3B82F6",
                size=6
            ),
            hovertemplate=
            str(fecha_fin_actual.year - 1) + ": S/ %{y:,.2f}" +
            "<extra></extra>"
        )
    )

    # ================= LAYOUT ORIGINAL =================
    fig.update_layout(
        template="plotly_dark",
        height=340, #340
        dragmode=False,
        margin=dict(
            l=5,
            r=5,
            t=40,
            b=20
        ),
        title=dict(
            text=f"Comparativa {fecha_fin_actual.year-1} vs {fecha_fin_actual.year}",
            x=0.02,
            font=dict(size=16)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Mes",
            showgrid=False,
            showspikes=True,
            spikecolor="rgba(255,255,255,0.35)",
            spikesnap="hovered data",
            spikemode="across",
            spikethickness=1
        ),
        yaxis=dict(
            title="Ventas (S/)",
            gridcolor="rgba(255,255,255,0.08)"
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1E1E1E",
            font_size=13,
            font_color="white"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        }
    )
    render_divider()


# =======================================================================================
# =========================== GRÁFICO DE VENTAS POR CATEGORÍA ===========================
# =======================================================================================
def graph_categoria(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ================= CÁLCULOS ORIGINALES =================
    # ============ ITEMS ============
    df_items = (
        df_filtrado
        .groupby("CATEGORÍA (ITEM)")
        .agg({"CANTIDAD (ITEM)": "sum"})
        .reset_index()
    )

    # ========== VENTAS Y TRANSACCIONES ==========
    df_ventas_trans = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("CATEGORÍA (ITEM)")
        .agg(
            VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum"),
            TRANSACCIONES=("NÚMERO", "nunique")
        )
        .reset_index()
    )

    # ======= UNIMOS ITEMS, VENTAS Y TRANSACCIONES =======
    df_categoria = df_ventas_trans.merge(
        df_items,
        on="CATEGORÍA (ITEM)",
        how="left"
    )

    # DEFINIMOS EL NUEVO ORDEN DE LAS COLUMNAS
    nuevo_orden = ['CATEGORÍA (ITEM)', 'VENTAS', 'CANTIDAD (ITEM)', 'TRANSACCIONES']
    # APLICAMOS EL NUEVO ORDEN
    df_categoria = df_categoria.reindex(columns=nuevo_orden)

    # RENOMBRAMOS LAS COLUMNAS
    df_categoria.rename(
        columns={
            "CATEGORÍA (ITEM)": "Categoría",
            "VENTAS": "Ventas",
            "CANTIDAD (ITEM)": "Items",
            "TRANSACCIONES": "Trans."
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
    df_categoria = (
        df_categoria
        .sort_values(
            "Ventas",
            ascending=False
        )
        .head(10)
        .reset_index(drop=True)
    )

    # ================= LAYOUT =================
    col1, col2 = st.columns([1.6, 1])

    # =====================================================
    # GRÁFICO
    # =====================================================
    with col1:
        st.subheader("📦 Top 10 Categorías")

        max_ventas = df_categoria["Ventas"].max()

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_categoria["Ventas"],
                y=df_categoria["Categoría"],

                orientation="h",

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_categoria["Ventas"]
                ],

                textposition="outside",

                marker=dict(
                    color="#FFD700",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=430,
            margin=dict(l=10, r=20, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Ventas (S/)",
                range=[0, max_ventas * 1.15],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =====================================================
    # TABLA RESUMEN
    # =====================================================
    with col2:
        st.subheader("📋 Resumen")

        total_ventas = df_categoria["Ventas"].sum()
        total_items = df_categoria["Items"].sum()
        total_trans = df_categoria["Trans."].sum()

        df_tabla = df_categoria.copy()

        df_tabla.loc[len(df_tabla)] = [
            "TOTAL",
            total_ventas,
            total_items,
            total_trans
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Items": "{:.0f}",
                    "Trans.": "{:.0f}"
                },

                cmap="YlOrBr",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=430
        )

    render_divider()


# ======================================================================================
# ========================== GRÁFICO DE VENTAS POR VENDEDOR ============================
# ======================================================================================
def graph_vendedor(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ================= ITEMS =================
    df_items = (
        df_filtrado
        .groupby("VENDEDOR")
        .agg(
            ITEMS=("CANTIDAD (ITEM)", "sum")
        )
        .reset_index()
    )
    
    # ========== VENTAS Y TRANSACCIONES ==========
    df_ventas_trans = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum"),
            TRANSACCIONES=("NÚMERO", "nunique")
        )
        .reset_index()
    )

    # ======= UNIMOS ITEMS, VENTAS Y TRANSACCIONES =======
    df_vendedor = df_ventas_trans.merge(
        df_items,
        on="VENDEDOR",
        how="left"
    )

    # CALCULAMOS AL METRICAS EN CASO HAYA
    #df_vendedor["Ticket Promedio"] = (
    #    df_vendedor["Ventas"]
    #    / df_vendedor["Transacciones"]
    #)

    # DEFINIMOS EL NUEVO ORDEN DE LAS COLUMNAS
    nuevo_orden = ['VENDEDOR', 'VENTAS', 'ITEMS', 'TRANSACCIONES']
    # APLICAMOS EL NUEVO ORDEN
    df_vendedor = df_vendedor.reindex(columns=nuevo_orden)

    # RENOMBRAMOS LAS COLUMNAS
    df_vendedor.rename(
        columns={
            "VENDEDOR": "Vendedor",
            "VENTAS": "Ventas",
            "ITEMS": "Items",
            "TRANSACCIONES": "Trans.",
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
    df_vendedor = (
        df_vendedor
        .sort_values(
            "Ventas",
            ascending=False
        )
        .head(10)
        .reset_index(drop=True)
    )

    # LIMPIAMOS LOS NOMBRES
    df_vendedor["Vendedor"] = (
        df_vendedor["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "store": "ADMIN",
            "STORE": "ADMIN"
        })
    )

    # ====================== LAYOUT ======================
    col1, col2 = st.columns([1.6, 1])

    # =====================================================
    # GRÁFICO
    # =====================================================
    with col1:
        st.subheader("👨‍💼 Participación por Vendedor")

        max_ventas = df_vendedor["Ventas"].max()

        cantidad = len(df_vendedor)
        altura_grafico = obtener_altura_grafico(cantidad)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_vendedor["Ventas"],
                y=df_vendedor["Vendedor"],

                orientation="h",

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_vendedor["Ventas"]
                ],

                textposition="outside",

                marker=dict(
                    color="#F97316",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Ventas (S/)",
                range=[0, max_ventas * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:
        st.subheader("📋 Resumen")

        total_ventas = df_vendedor["Ventas"].sum()
        total_items = df_vendedor["Items"].sum()
        total_trans = df_vendedor["Trans."].sum()

        df_tabla = df_vendedor.copy()

        df_tabla.loc[len(df_tabla)] = [
            "Total",
            total_ventas,
            total_items,
            total_trans
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Items": "{:.0f}",
                    "Trans.": "{:.0f}"
                },

                cmap="YlOrBr",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()



# =======================================================================================
# ========================= GRÁFICO DE VENTAS POR MÉTODO DE PAGO ========================
# =======================================================================================
def graph_tipo_pago(df_dos, date1, date2, tipo_documento):

    if "DOCUMENTOS" not in df_dos.columns:
        st.error(
            f"df_dos no tiene la columna DOCUMENTOS. "
            f"Columnas disponibles: {list(df_dos.columns)}"
        )
        return

    # ======== FILTROS =========
    df_filtrado = aplicar_filtros(df_dos, date1, date2, tipo_documento)

    # ======== VENTAS Y TRANSACCIONES ========
    df_ventas_trans = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("MÉTODO (PAGO)")
        .agg(
            VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum"),
            TRANSACCIONES=("NÚMERO", "nunique")
        )
        .reset_index()
    )

    df_tipo_pago = df_ventas_trans

    # CALCULAMOS AL METRICAS EN CASO HAYA

    # DEFINIMOS EL NUEVO ORDEN DE LAS COLUMNAS

    # RENOMBRAMOS LAS COLUMNAS
    df_tipo_pago.rename(
        columns={
            "MÉTODO (PAGO)": "Método de Pago",
            "VENTAS": "Ventas",
            "TRANSACCIONES": "Trans."
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
    df_tipo_pago = (
        df_tipo_pago
        .sort_values(
            "Ventas",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # LIMPIAMOS LOS NOMBRES

    # ====================== LAYOUT ======================
    col1, col2 = st.columns([1.6, 1])

    # =========================================================
    # GRÁFICO
    # =========================================================
    with col1:
        st.subheader("💳 Participación por Método de Pago")

        # =============== ALTURA DINÁMICA =================
        max_ventas = df_tipo_pago["Ventas"].max()

        cantidad = len(df_tipo_pago)
        altura_grafico = obtener_altura_grafico(cantidad)

        # ========= GRAFICO ===========
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_tipo_pago["Ventas"],
                y=df_tipo_pago["Método de Pago"],

                orientation="h",

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_tipo_pago["Ventas"]
                ],

                textposition="outside",

                marker=dict(
                    color="#22C55E",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Ventas (S/)",
                range=[0, max_ventas * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =========================================================
    # TABLA
    # =========================================================
    with col2:

        st.subheader("📋 Resumen")

        total_ventas = (
            df_tipo_pago["Ventas"]
            .sum()
        )

        total_trans = (
            df_tipo_pago["Trans."]
            .sum()
        )

        df_tabla = df_tipo_pago.copy()

        df_tabla.loc[len(df_tabla)] = [
            "TOTAL",
            total_ventas,
            total_trans
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Trans.": "{:.0f}"
                },

                cmap="Greens",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()



# ================================================================================================
# ================== GRÁFICO DE VENTAS ANULADAS Y DESCUENTOS POR VENDEDOR ========================
# ================================================================================================
def graph_anulados(df, date1, date2, tipo_documento):
    col1, col2 = st.columns([1, 1])

    # ==================================================
    # ANULADOS
    # ==================================================
    with col1:
        df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento, eliminar_anulados=False)

        df_anulados = df_filtrado[df_filtrado["ESTADO"] == "Anulado"]

        if df_anulados.empty:
            st.subheader("🛑 Ventas Anulados por Vendedor")

            st.success(
                "✅ No se registran ventas anuladas en el período seleccionado"
            )
            render_divider()
            #return
        else:
            # ======== VENTAS ========
            df_ventas = (
                df_anulados
                .drop_duplicates(subset=["NÚMERO"])
                .groupby("VENDEDOR")
                .agg(
                    VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
                )
                .reset_index()
            )

            # ======= DATAFRAME BASE =========
            df_anulados = df_ventas

            # RENOMBRAMOS LAS COLUMNAS
            df_anulados.rename(
                columns={
                    "VENDEDOR": "Vendedor",
                    "VENTAS": "Ventas",
                },
                inplace=True
            )

            # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
            df_anulados = (df_anulados.sort_values(
                "Ventas",
                ascending=False
                )
                .reset_index(drop=True)
            )

            # LIMPIAMOS LOS NOMBRES
            df_anulados["Vendedor"] = (
                df_anulados["Vendedor"]
                .astype(str)
                .str.split(".")
                .str[-1]
                .str.upper()
                .replace({
                    "store": "ADMIN",
                    "STORE": "ADMIN"
                })
            )

            # =====================================================
            # GRÁFICO ANULADOS
            # =====================================================
            st.subheader("🛑 Ventas Anuladas por Vendedor")

            max_ventas = df_anulados["Ventas"].max()

            cantidad = len(df_anulados)
            altura_grafico = obtener_altura_grafico(cantidad)

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=df_anulados["Ventas"],
                    y=df_anulados["Vendedor"],

                    orientation="h",

                    text=[
                        f"S/ {x:,.0f}"
                        for x in df_anulados["Ventas"]
                    ],

                    textposition="outside",

                    marker=dict(
                        color="#EF4444",
                        line=dict(
                            color="rgba(255,255,255,0.15)",
                            width=1
                        )
                    ),
                )
            )

            fig.update_layout(
                template="plotly_dark",
                height=altura_grafico,
                margin=dict(l=10, r=10, t=10, b=10),

                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                dragmode=False,

                xaxis=dict(
                    title="Ventas Anuladas (S/)",
                    range=[0, max_ventas * 1.20],
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    zeroline=False
                ),

                yaxis=dict(
                    title="",
                    categoryorder="total ascending"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

    # ==================================================
    # DESCUENTOS
    # ==================================================
    with col2:
        df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

        df_descuentos = df_filtrado[df_filtrado["DESCUENTO GLOBAL CON IGV"] > 0]

        if df_descuentos.empty:
            st.subheader("💸 Descuentos por Vendedor")

            st.success(
                "ℹ️ No se registran descuentos en el período seleccionado"
            )
            render_divider()
            return
        else:
            # ======= VENTAS ========
            df_ventas = (
                df_descuentos
                .drop_duplicates(subset=["NÚMERO"])
                .groupby("VENDEDOR")
                .agg(
                    VENTAS=("DESCUENTO GLOBAL CON IGV", "sum")
                )
                .reset_index()
            )

            # ======= DATAFRAME BASE =========
            df_descuentos = df_ventas

            # RENOMBRAMOS LAS COLUMNAS
            df_descuentos.rename(
                columns={
                    "VENDEDOR": "Vendedor",
                    "VENTAS": "Ventas",
                },
                inplace=True
            )

            # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
            df_descuentos = (
                df_descuentos
                .sort_values(
                    "Ventas",
                    ascending=False
                )
                .reset_index(drop=True)
            )

            # LIMPIAMOS LOS NOMBRES
            df_descuentos["Vendedor"] = (
                df_descuentos["Vendedor"]
                .astype(str)
                .str.split(".")
                .str[-1]
                .str.upper()
                .replace({
                    "store": "ADMIN",
                    "STORE": "ADMIN"
                })
            )

            # =====================================================
            # GRÁFICO
            # =====================================================
            st.subheader("💸 Descuentos por Vendedor")

            max_ventas = df_descuentos["Ventas"].max()

            cantidad = len(df_descuentos)
            altura_grafico = obtener_altura_grafico(cantidad)

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=df_descuentos["Ventas"],
                    y=df_descuentos["Vendedor"],

                    orientation="h",

                    text=[
                        f"S/ {x:,.0f}"
                        for x in df_descuentos["Ventas"]
                    ],

                    textposition="outside",

                    marker=dict(
                        color="#F59E0B",
                        line=dict(
                            color="rgba(255,255,255,0.15)",
                            width=1
                        )
                    ),
                )
            )

            fig.update_layout(
                template="plotly_dark",
                height=altura_grafico,
                margin=dict(l=10, r=10, t=10, b=10),

                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                dragmode=False,

                xaxis=dict(
                    title="Descuentos (S/)",
                    range=[0, max_ventas * 1.25],
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    zeroline=False
                ),

                yaxis=dict(
                    title="",
                    categoryorder="total ascending"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

    render_divider()


# ======================================================================================
# ======================== RANKING COMERCIAL VENDEDORES ================================
# ======================================================================================
def graph_ranking_vendedores(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)


    # ==================== BASE ==========================
    df_base = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum"),
            TRANSACCIONES=("NÚMERO", "nunique")
        )
        .reset_index()
    )

    # =============== MÉTRICAS ==================
    total_ventas = df_base["VENTAS"].sum()

    df_base["PPARTICIPACION %"] = (
        df_base["VENTAS"]
        / total_ventas
        * 100
    )

    df_base["TICKET PROMEDIO"] = (
        df_base["VENTAS"]
        / df_base["TRANSACCIONES"]
    )

    # DEFINIMOS EL NUEVO ORDEN DE LAS COLUMNAS
    nuevo_orden = ['VENDEDOR', 'VENTAS', 'PPARTICIPACION %', 'TRANSACCIONES', 'TICKET PROMEDIO']
    # APLICAMOS EL NUEVO ORDEN
    df_base = df_base.reindex(columns=nuevo_orden)

    # RENOMBRAMOS LAS COLUMNAS
    df_base.rename(
        columns={
            "VENDEDOR": "Vendedor",
            "VENTAS": "Ventas",
            "PPARTICIPACION %": "Particip. %",
            "TRANSACCIONES": "Trans.",
            "TICKET PROMEDIO": "Ticket Prom."
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
    df_base = (
        df_base
        .sort_values(
            "Ventas",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # LIMPIAMOS LOS NOMBRES
    df_base["Vendedor"] = (
        df_base["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "store": "ADMIN",
            "STORE": "ADMIN"
        })
    )

    df_base = df_base.drop("Particip. %", axis=1)

    # =====================================================
    # LAYOUT
    # =====================================================
    col1, col2 = st.columns([1.6, 1])

    # =====================================================
    # GRÁFICO
    # =====================================================
    with col1:
        st.subheader("🏆 Ranking Comercial")

        max_ventas = df_base["Ventas"].max()
        
        cantidad = len(df_base)
        altura_grafico = obtener_altura_grafico(cantidad)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Ventas"],
                y=df_base["Vendedor"],

                orientation="h",

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_base["Ventas"]
                ],

                textposition="outside",

                marker=dict(
                    color="#FFD700",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Ventas (S/)",
                range=[0, max_ventas * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:
        st.subheader("📋 Resumen Comercial")

        total_ventas = df_base["Ventas"].sum()
        total_trans = df_base["Trans."].sum()
        ticket_global = (
            total_ventas / total_trans
            if total_trans > 0
            else 0
        )

        df_tabla = df_base.copy()

        df_tabla.loc[len(df_tabla)] = [
            "Total",
            total_ventas,
            #100,
            total_trans,
            ticket_global
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Particip. %": "{:.2f}%",
                    "Trans.": "{:.0f}",
                    "Ticket Prom.": "S/ {:,.2f}"
                },

                cmap="YlOrBr",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()


# ======================================================================================
# ========================= PARTICIPACIÓN DE VENTAS ====================================
# ======================================================================================
def graph_participacion_vendedor(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # =============== BASE =============
    df_base = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
        )
        .reset_index()
    )

    # ============== MÉTRICAS ===============
    total_ventas = (df_base["VENTAS"].sum())

    df_base["PARTICIPACION %"] = (
        df_base["VENTAS"]
        / total_ventas
        * 100
    )

    # ===== RENOMBRAMOS LAS COLUMNAS =======
    df_base.rename(
        columns={
            "VENDEDOR": "Vendedor",
            "VENTAS": "Ventas",
            "PARTICIPACION %": "Participación (%)",
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR
    df_base = (
        df_base
        .sort_values(
            "Participación (%)",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # ======== LIMPIAR NOMBRES =========
    df_base["Vendedor"] = (
        df_base["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "STORE": "ADMIN",
            "store": "ADMIN"
        })
    )

    # =====================================================
    # LAYOUT
    # =====================================================
    col1, col2 = st.columns([1.6, 1])

    # =====================================================
    # GRÁFICO
    # =====================================================
    with col1:
        st.subheader("📊 Participación de Ventas")

        max_participacion = (df_base["Participación (%)"].max())

        cantidad = len(df_base)
        altura_grafico = obtener_altura_grafico(cantidad)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Participación (%)"],
                y=df_base["Vendedor"],

                orientation="h",

                text=[
                    f"{x:.1f}%"
                    for x in df_base["Participación (%)"]
                ],

                textposition="outside",

                marker=dict(
                    color="#3B82F6",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Participación (%)",
                range=[0, max_participacion * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:

        st.subheader("📋 Resumen")

        df_tabla = df_base.copy()

        df_tabla.loc[len(df_tabla)] = [
            "Total",
            total_ventas,
            100
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Participación (%)": "{:.1f}%"
                },

                cmap="Blues",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()



# ======================================================================================
# ======================== PRODUCTIVIDAD COMERCIAL =====================================
# ======================================================================================
def graph_productividad_vendedores(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ========== DATAFRAME BASE ===========
    df_base = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            TRANSACCIONES=("NÚMERO", "nunique"),
            VENTAS=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
        )
        .reset_index()
    )

    # ============= MÉTRICAS ============
    df_base["TICKET PROMEDIO"] = (
        df_base["VENTAS"]
        /
        df_base["TRANSACCIONES"]
    )

    # ===== RENOMBRAMOS LAS COLUMNAS =======
    df_base.rename(
        columns={
            "VENDEDOR": "Vendedor",
            "TRANSACCIONES": "Trans.",
            "VENTAS": "Ventas",
            "TICKET PROMEDIO": "Ticket Prom.",
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR TRANSACCIONES DE MAYOR A MENOR
    df_base = (
        df_base
        .sort_values(
            "Trans.",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # ========== LIMPIAR NOMBRES ==========
    df_base["Vendedor"] = (
        df_base["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "STORE": "ADMIN",
            "store": "ADMIN"
        })
    )

    # ========= LAYOUT ===============
    col1, col2 = st.columns([1.6, 1])

    # ============== GRÁFICO =============
    with col1:
        st.subheader("🛒 Productividad Comercial")

        max_trans = (df_base["Trans."].max())

        cantidad = len(df_base)
        altura_grafico = obtener_altura_grafico(cantidad)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Trans."],
                y=df_base["Vendedor"],

                orientation="h",

                text=[
                    f"{x:,.0f}"
                    for x in df_base["Trans."]
                ],

                textposition="outside",

                marker=dict(
                    color="#10B981",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Transacciones",
                range=[0, max_trans * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:
        st.subheader("📋 Resumen Productividad")

        df_tabla = df_base.copy()

        total_trans = (
            df_tabla["Trans."]
            .sum()
        )

        total_ventas = (
            df_tabla["Ventas"]
            .sum()
        )

        ticket_global = (
            total_ventas / total_trans
            if total_trans > 0
            else 0
        )

        df_tabla.loc[len(df_tabla)] = [
            "TotalL",
            total_trans,
            total_ventas,
            ticket_global
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Trans.": "{:,.0f}",
                    "Ventas": "S/ {:,.2f}",
                    "Ticket Prom.": "S/ {:,.2f}"
                },

                cmap="Greens",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()


# ======================================================================================
# ====================== TICKET PROMEDIO POR VENDEDOR ==================================
# ======================================================================================
def graph_ticket_promedio_vendedor(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ================ BASE =================
    df_ticket = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            Ventas=("IMPORTE TOTAL DEL COMPROBANTE", "sum"),
            Transacciones=("NÚMERO", "nunique")
        )
        .reset_index()
    )

    # ============ METRICAS =============
    df_ticket["Ticket Promedio"] = (
        df_ticket["Ventas"]
        /
        df_ticket["Transacciones"]
    )

    # =========== ORDEN COLUMNAS ============
    nuevo_orden = ["VENDEDOR", "Ticket Promedio", "Ventas", "Transacciones"]
    df_ticket = df_ticket.reindex(columns=nuevo_orden)

    # =========== RENOMBRAR ==============
    df_ticket.rename(
        columns={
            "VENDEDOR": "Vendedor",
            "Ticket Promedio": "Ticket Prom.",
            "Ventas": "Ventas",
            "Transacciones": "Trans."
        },
        inplace=True
    )

    # =========== ORDENAR ===============
    df_ticket = (
        df_ticket
        .sort_values(
            "Ticket Prom.",
            ascending=False
        )
        .head(10)
        .reset_index(drop=True)
    )

    # =========== LIMPIAR NOMBRES ==========
    df_ticket["Vendedor"] = (
        df_ticket["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "store": "ADMIN",
            "STORE": "ADMIN"
        })
    )

    # ================ LAYOUT ===================
    col1, col2 = st.columns([1.6, 1])

    # ================ GRÁFICO ==================
    with col1:
        st.subheader("🎯 Ticket Promedio por Vendedor")

        max_ticket = (df_ticket["Ticket Prom."].max())

        cantidad = len(df_ticket)

        altura_grafico = obtener_altura_grafico(cantidad)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_ticket["Ticket Prom."],
                y=df_ticket["Vendedor"],

                orientation="h",

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_ticket["Ticket Prom."]
                ],

                textposition="outside",

                marker=dict(
                    color="#8B5CF6",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                )
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Ticket Promedio (S/)",
                range=[0, max_ticket * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:
        st.subheader("📋 Resumen")

        total_ventas = (
            df_ticket["Ventas"]
            .sum()
        )

        total_trans = (
            df_ticket["Trans."]
            .sum()
        )

        ticket_global = (
            total_ventas / total_trans
            if total_trans > 0
            else 0
        )

        df_tabla = df_ticket.copy()

        df_tabla.loc[len(df_tabla)] = [
            "Total",
            ticket_global,
            total_ventas,
            total_trans
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ticket Prom.": "S/ {:,.2f}",
                    "Ventas": "S/ {:,.2f}",
                    "Trans.": "{:.0f}"
                },

                cmap="Purples",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()


# ======================================================================================
# ================= GESTIÓN COMERCIAL POR VENDEDOR - ANULADAS ==========================
# ======================================================================================
def graph_gestion_comercial_anulados(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento, eliminar_anulados=False)

    df_anulados = df_filtrado[df_filtrado["ESTADO"] == "Anulado"]

    if df_anulados.empty:
        st.subheader("🛑 % Anulados por Vendedor")

        st.success(
            "✅ No se registran ventas anuladas en el período seleccionado"
        )
        render_divider()
        return

    # ======= VENTAS POR VENDEDOR ==========
    df_ventas = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            Ventas=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
        )
        .reset_index()
    )

    # ====== VENTAS ANULADAS ======
    df_anulados = (
        df_anulados
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            Anulados=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
        )
        .reset_index()
    )

    # ====== UNIMOS VENTAS CON ANULADOS =======
    df_anulados_base = (
        df_ventas
        .merge(
            df_anulados,
            on="VENDEDOR",
            how="left"
        )
        .fillna(0)
    )

    # ========== METRICA =========
    df_anulados_base["% Anulado"] = (
        df_anulados_base["Anulados"]
        /
        df_anulados_base["Ventas"]
        * 100
    ).fillna(0)

    # ======== RENOMBRAR COLUMNAS ======
    df_anulados_base.rename(
        columns={
            "VENDEDOR": "Vendedor",
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR            
    df_anulados_base = (
        df_anulados_base
        .sort_values(
            "% Anulado",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # ===== LIMPIAR NOMBRES ========
    df_anulados_base["Vendedor"] = (
        df_anulados_base["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "store": "ADMIN",
            "STORE": "ADMIN"
        })
    )

    # ========= (FILTRAMOS VENDEDORES CON ANULADOS = 0) ==========
    df_anulados_base_graph = (
        df_anulados_base[
            df_anulados_base["Anulados"] > 0
        ]
    )

    max_valor = (df_anulados_base_graph["% Anulado"].max())

    cantidad = len(df_anulados_base_graph)
    altura_grafico = obtener_altura_grafico(cantidad)

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.subheader("🛑 % Anulados por Vendedor")

        # ====== grafico de anulados """"""""
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_anulados_base_graph["% Anulado"],
                y=df_anulados_base_graph["Vendedor"],

                orientation="h",

                text=[
                    f"{x:.2f}%"
                    for x in df_anulados_base_graph["% Anulado"]
                ],

                textposition="outside",

                marker=dict(
                    color="#EF4444",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                )
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="% Anulado",
                range=[0, max_valor * 1.20 if max_valor > 0 else 1],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # ========= TABLA ANULADOS ===========
    with col2:
        st.subheader("📋 Resumen")

        df_anulados_base.loc[len(df_anulados_base)] = [
            "Total",
            df_anulados_base["Ventas"].sum(),
            df_anulados_base["Anulados"].sum(),
            (
                df_anulados_base["Anulados"].sum()
                /
                df_anulados_base["Ventas"].sum()
                * 100
            )
            if df_anulados_base["Ventas"].sum() > 0
            else 0
        ]

        st.dataframe(
            styled_dataframe(
                df_anulados_base,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Anulados": "S/ {:,.2f}",
                    "% Anulado": "{:.2f}%"
                },

                cmap="Reds",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()


# ======================================================================================
# ================= GESTIÓN COMERCIAL POR VENDEDOR - DESCUENTOS ========================
# ======================================================================================
def graph_gestion_comercial_descuentos(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    df_descuentos = df_filtrado[df_filtrado["DESCUENTO GLOBAL CON IGV"] > 0]

    if df_descuentos.empty:
        st.subheader("💸 % Descuentos por Vendedor")

        st.success(
            "✅ No se registran descuentos en el período seleccionado"
        )
        render_divider()
        return

    # ======= VENTAS POR VENDEDOR ==========
    df_ventas = (
        df_filtrado
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            Ventas=("IMPORTE TOTAL DEL COMPROBANTE", "sum")
        )
        .reset_index()
    )

    # ============ DESCUENTOS =============
    df_descuentos = (
        df_descuentos
        .drop_duplicates(subset=["NÚMERO"])
        .groupby("VENDEDOR")
        .agg(
            Descuentos=("DESCUENTO GLOBAL CON IGV", "sum")
        )
        .reset_index()
    )

    # ========= UNIMOS VENTAS CON DESCUENTOS ==========
    df_descuentos_base = (
        df_ventas
        .merge(
            df_descuentos,
            on="VENDEDOR",
            how="left"
        )
        .fillna(0)
    )

    # ========== METRICA ===============
    df_descuentos_base["% Descuento"] = (
        df_descuentos_base["Descuentos"]
        /
        df_descuentos_base["Ventas"]
        * 100
    ).fillna(0)

    # ======== RENOMBRAR COLUMNAS ======
    df_descuentos_base.rename(
        columns={
            "VENDEDOR": "Vendedor",
        },
        inplace=True
    )

    # ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR            
    df_descuentos_base = (
        df_descuentos_base
        .sort_values(
            "% Descuento",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # ===== LIMPIAR NOMBRES ========
    df_descuentos_base["Vendedor"] = (
        df_descuentos_base["Vendedor"]
        .astype(str)
        .str.split(".")
        .str[-1]
        .str.upper()
        .replace({
            "store": "ADMIN",
            "STORE": "ADMIN"
        })
    )

    # ========= (FILTRAMOS VENDEDORES CON DESCUENTOS = 0) ==========
    df_descuentos_base_graph = (
        df_descuentos_base[
            df_descuentos_base["Descuentos"] > 0
        ]
    )

    max_valor = (df_descuentos_base_graph["% Descuento"].max())

    cantidad = len(df_descuentos_base_graph)
    altura_grafico = obtener_altura_grafico(cantidad)

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.subheader("💸 % Descuentos por Vendedor")

        # ====== GRAFICO DESCUENTOS ===========
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_descuentos_base_graph["% Descuento"],
                y=df_descuentos_base_graph["Vendedor"],

                orientation="h",

                text=[
                    f"{x:.2f}%"
                    for x in df_descuentos_base_graph["% Descuento"]
                ],

                textposition="outside",

                marker=dict(
                    color="#F59E0B",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                )
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="% Descuento",
                range=[0, max_valor * 1.20 if max_valor > 0 else 1],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # ========= TABLA DESCUENTOS ===========
    with col2:
        st.subheader("📋 Resumen")

        df_descuentos_base.loc[len(df_descuentos_base)] = [
            "TOTAL",
            df_descuentos_base["Ventas"].sum(),
            df_descuentos_base["Descuentos"].sum(),
            (
                df_descuentos_base["Descuentos"].sum()
                /
                df_descuentos_base["Ventas"].sum()
                * 100
            )
            if df_descuentos_base["Ventas"].sum() > 0
            else 0
        ]

        st.dataframe(
            styled_dataframe(
                df_descuentos_base,

                format_dict={
                    "Ventas": "S/ {:,.2f}",
                    "Descuentos": "S/ {:,.2f}",
                    "% Descuento": "{:.2f}%"
                },

                cmap="YlOrBr",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()



# ======================================================================================
# ======================= RANKING COMERCIAL DE PRODUCTOS ===============================
# ======================================================================================
def graph_ranking_productos(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ============ BASE =============
    df_base = (
        df_filtrado
        .groupby("DESCRIPCIÓN (ITEM)")
        .agg(
            VENTAS=("TOTAL (ITEM)", "sum"),
            UNIDADES=("CANTIDAD (ITEM)", "sum")
        )
        .reset_index()
    )

    # ============= MÉTRICAS ===========
    total_ventas = (
        df_base["VENTAS"]
        .sum()
    )

    df_base["PARTICIPACION %"] = (
        df_base["VENTAS"]
        /
        total_ventas
        *
        100
    )

    # ======= NOMBRE PRODUCTO COMPLETO =========
    df_base["Producto Completo"] = (
        df_base["DESCRIPCIÓN (ITEM)"]
        .astype(str)
        .str.upper()
    )

    # ========= NOMBRE PRODUCTO CORTO ============
    df_base["Producto Corto"] = np.where(
        df_base["Producto Completo"].str.len() > 35,
        df_base["Producto Completo"].str.slice(0, 35) + "...",
        df_base["Producto Completo"]
    )

    df_base = df_base[
        [
            "Producto Completo",
            "Producto Corto",
            "VENTAS",
            "UNIDADES",
            "PARTICIPACION %"
        ]
    ].copy()

    # ========= RENOMBRAMOS LAS COLUMNAS ========
    df_base.rename(
        columns={
            "Producto Completo": "Producto Completo",
            "Producto Corto": "Producto",
            "VENTAS": "Ventas",
            "UNIDADES": "Unid.",
            "PARTICIPACION %": "Partic. %"
        },
        inplace=True
    )

    # ===== ORDENAMOS EL DATAFRAME POR VENTAS DE MAYOR A MENOR ======
    df_base = (
        df_base
        .sort_values(
            "Ventas",
            ascending=False
        )
        .head(10)
        .reset_index(drop=True)
    )


    # ============== LAYOUT =====================
    col1, col2 = st.columns([1.6, 1])

    # ============== GRÁFICO ====================
    with col1:
        st.subheader("🏆 Ranking de Productos")

        max_ventas = (df_base["Ventas"].max())

        cantidad = len(df_base)
        altura_grafico = (obtener_altura_grafico(cantidad))

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Ventas"],
                y=df_base["Producto"],

                orientation="h",

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_base["Ventas"]
                ],

                textposition="outside",

                marker=dict(
                    color="#3B82F6",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),

                customdata=df_base[["Producto Completo"]],

                hovertemplate=
                "<b>%{customdata[0]}</b><br>"
                "Ventas: S/ %{x:,.2f}"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Ventas (S/)",
                range=[0, max_ventas * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                #"staticPlot": True
            }
        )

    # ============== TABLA ================
    with col2:
        st.subheader("📋 Resumen")

        df_tabla = df_base[
            [
                "Producto",
                "Ventas",
                "Unid.",
                "Partic. %"
            ]
        ].copy()

        df_tabla.loc[
            len(df_tabla)
        ] = [
            "Total",
            df_tabla["Ventas"].sum(),
            df_tabla["Unid."].sum(),
            100
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Ventas":
                    "S/ {:,.2f}",

                    "Unid.":
                    "{:,.0f}",

                    "Partic. %":
                    "{:.1f}%"
                },

                cmap="Blues",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            (
                                "background-color",
                                "#1E3A8A"
                            ),
                            (
                                "color",
                                "white"
                            ),
                            (
                                "font-weight",
                                "bold"
                            )
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()


# ======================================================================================
# ===================== PARTICIPACIÓN DE VENTAS POR PRODUCTO ===========================
# ======================================================================================
def graph_participacion_productos(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ================= BASE =================
    df_base = (
        df_filtrado
        .groupby("DESCRIPCIÓN (ITEM)")
        .agg(
            VENTAS=("TOTAL (ITEM)", "sum")
        )
        .reset_index()
    )

    # ========= METRICAS =========
    total_ventas = df_base["VENTAS"].sum()

    df_base["PARTICIPACION %"] = (
        df_base["VENTAS"]
        /
        total_ventas
        *
        100
    )

    # ===== NOMBRE COMPLETO =====
    df_base["Producto Completo"] = (
        df_base["DESCRIPCIÓN (ITEM)"]
        .astype(str)
        .str.upper()
    )

    # ===== NOMBRE CORTO =====
    df_base["Producto Corto"] = np.where(
        df_base["Producto Completo"].str.len() > 35,
        df_base["Producto Completo"].str.slice(0, 35) + "...",
        df_base["Producto Completo"]
    )

    # ===== TOP 10 =====
    df_base = (
        df_base
        .sort_values(
            "PARTICIPACION %",
            ascending=False
        )
        .head(10)
        .reset_index(drop=True)
    )

    # ======= RENOMBRAMOS LAS COLUMNAS ===========
    df_base.rename(
        columns={
            "Producto Corto": "Producto",
            "PARTICIPACION %": "Partic. %"
        },
        inplace=True
    )

    # ================= LAYOUT =================
    col1, col2 = st.columns([1.6, 1])

    # =====================================================
    # GRÁFICO
    # =====================================================
    with col1:
        st.subheader("🥧 Participación de Ventas")

        max_partic = (df_base["Partic. %"].max())

        cantidad = len(df_base)
        altura_grafico = (obtener_altura_grafico(cantidad))

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Partic. %"],
                y=df_base["Producto"],

                orientation="h",

                text=[
                    f"{x:.2f}%"
                    for x in df_base["Partic. %"]
                ],

                textposition="outside",

                marker=dict(
                    color="#8B5CF6",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),

                customdata=df_base[
                    ["Producto Completo"]
                ],

                hovertemplate=
                "<b>%{customdata[0]}</b><br>"
                "Participación: %{x:.2f}%"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Participación (%)",
                range=[0, max_partic * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                #"staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:
        st.subheader("📋 Resumen")

        df_tabla = df_base[
            [
                "Producto",
                "Partic. %"
            ]
        ].copy()

        df_tabla.loc[
            len(df_tabla)
        ] = [
            "Total",
            100
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Partic. %":
                    "{:.2f}%"
                },

                cmap="Purples",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            (
                                "background-color",
                                "#1E3A8A"
                            ),
                            (
                                "color",
                                "white"
                            ),
                            (
                                "font-weight",
                                "bold"
                            )
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()



# ======================================================================================
# ======================== ALTA ROTACIÓN DE PRODUCTOS ==================================
# ======================================================================================
def graph_alta_rotacion_productos(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ================= BASE =================
    df_base = (
        df_filtrado
        .groupby("DESCRIPCIÓN (ITEM)")
        .agg(
            UNIDADES=("CANTIDAD (ITEM)", "sum")
        )
        .reset_index()
    )

    # ===== NOMBRE COMPLETO =====
    df_base["Producto Completo"] = (
        df_base["DESCRIPCIÓN (ITEM)"]
        .astype(str)
        .str.upper()
    )

    # ===== NOMBRE CORTO =====
    df_base["Producto Corto"] = np.where(
        df_base["Producto Completo"].str.len() > 35,
        df_base["Producto Completo"].str.slice(0, 35) + "...",
        df_base["Producto Completo"]
    )

    # ===== TOP 10 =====
    df_base = (
        df_base
        .sort_values(
            "UNIDADES",
            ascending=False
        )
        .head(10)
        .reset_index(drop=True)
    )

    # ======= RENOMBRAMOS LAS COLUMNAS ========
    df_base.rename(
        columns={
            "Producto Corto": "Producto",
            "UNIDADES": "Unid."
        },
        inplace=True
    )

    # ================= LAYOUT =================
    col1, col2 = st.columns([1.6, 1])

    # =====================================================
    # GRÁFICO
    # =====================================================
    with col1:
        st.subheader("🚀 Alta Rotación")

        max_unidades = (df_base["Unid."].max())

        cantidad = len(df_base)
        altura_grafico = (obtener_altura_grafico(cantidad))

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Unid."],
                y=df_base["Producto"],

                orientation="h",

                text=[
                    f"{x:,.0f}"
                    for x in df_base["Unid."]
                ],

                textposition="outside",

                marker=dict(
                    color="#22C55E",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1
                    )
                ),

                customdata=df_base[
                    ["Producto Completo"]
                ],

                hovertemplate=
                "<b>%{customdata[0]}</b><br>"
                "Unidades: %{x:,.0f}"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Unidades Vendidas",
                range=[0, max_unidades * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                #"staticPlot": True
            }
        )

    # =====================================================
    # TABLA
    # =====================================================
    with col2:
        st.subheader("📋 Resumen")

        df_tabla = df_base[
            [
                "Producto",
                "Unid."
            ]
        ].copy()

        df_tabla.loc[
            len(df_tabla)
        ] = [
            "Total",
            df_tabla["Unid."].sum()
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Unid.": "{:,.0f}"
                },

                cmap="Greens",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            (
                                "background-color",
                                "#1E3A8A"
                            ),
                            (
                                "color",
                                "white"
                            ),
                            (
                                "font-weight",
                                "bold"
                            )
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=altura_grafico
        )

    render_divider()


# ======================================================================================
# ======================= PRODUCTOS MÁS RENTABLES =====================================
# ======================================================================================
def graph_productos_rentables(df_ventas, df_productos, date1, date2, tipo_documento):

    # ======== FILTRO VENTAS ==========
    df_filtrado = aplicar_filtros(df_ventas, date1, date2, tipo_documento)

    # ======= MERGE CON PRODUCTOS ==========
    df_merge = df_filtrado.merge(
        df_productos[
            [
                "NOMBRE",
                "PRECIO DE COMPRA"
            ]
        ],
        left_on="DESCRIPCIÓN (ITEM)",
        right_on="NOMBRE",
        how="left"
    )

    # ========== UTILIDAD REAL ===========
    df_merge["VENTA_TOTAL"] = (
        df_merge["PRECIO UNITARIO (ITEM)"]
        *
        df_merge["CANTIDAD (ITEM)"]
    )

    df_merge["COSTO_TOTAL"] = (
        df_merge["PRECIO DE COMPRA"]
        *
        df_merge["CANTIDAD (ITEM)"]
    )

    df_merge["UTILIDAD"] = (
        df_merge["VENTA_TOTAL"]
        -
        df_merge["COSTO_TOTAL"]
    )

    # ============ AGRUPAR ===========
    df_base = (
        df_merge
        .groupby("DESCRIPCIÓN (ITEM)")
        .agg(
            Utilidad=("UTILIDAD", "sum"),
            Ventas=("VENTA_TOTAL", "sum"),
            Costo=("COSTO_TOTAL", "sum"),
            Unidades=("CANTIDAD (ITEM)", "sum")
        )
        .reset_index()
    )

    # ======= MARGEN % ===========
    df_base["Margen %"] = np.where(
        df_base["Ventas"] > 0,
        (df_base["Utilidad"] / df_base["Ventas"]) * 100,
        0
    )

    # ============NOMBRE CORTO (UI) ================
    df_base["Producto"] = np.where(
        df_base["DESCRIPCIÓN (ITEM)"].str.len() > 50,
        df_base["DESCRIPCIÓN (ITEM)"].str.slice(0, 50).str.upper() + "...",
        df_base["DESCRIPCIÓN (ITEM)"].str.upper()
    )

    # ======= ELIMINAMOS UTILIDAD NEGATIVA ========
    df_base = df_base[
        df_base["Utilidad"] > 0
    ]

    # ============ORDENAR Y TOP 10 ============
    df_base = (
        df_base
        .sort_values("Utilidad", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    # =========== LAYOUT ============
    st.subheader("🥇 Productos Más Rentables")

    max_ventas = (df_base["Utilidad"].max())

    col1, col2 = st.columns([1.6, 1])

    # ========== GRÁFICO =============
    with col1:
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_base["Utilidad"],
                y=df_base["Producto"],

                orientation="h",

                marker=dict(
                    color="#8B5CF6"
                ),

                text=[
                    f"S/ {x:,.0f}"
                    for x in df_base["Utilidad"]
                ],

                textposition="outside",

                customdata=df_base[
                    [
                        "Ventas",
                        "Unidades"
                    ]
                ],

                hovertemplate=
                "<b>%{y}</b><br>"
                "Utilidad: S/ %{x:,.2f}<br>"
                "Ventas: S/ %{customdata[0]:,.2f}<br>"
                "Unidades: %{customdata[1]:,.0f}"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=10, b=10),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            xaxis=dict(
                title="Utilidad (S/)",
                range=[0, max_ventas * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

    # ========== TABLA ==========
    with col2:
        df_tabla = df_base[
            [
                "Producto",
                "Utilidad",
                "Margen %",
                "Ventas",
                "Unidades"
            ]
        ].copy()

        # ========== TOTAL ===========
        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Utilidad"].sum(),

            (
                df_tabla["Utilidad"].sum()
                /
                df_tabla["Ventas"].sum()
            ) * 100,

            df_tabla["Ventas"].sum(),
            df_tabla["Unidades"].sum()
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Utilidad": "S/ {:,.2f}",
                    "Margen %": " {:,.2f}%",
                    "Ventas": "S/ {:,.2f}",
                    "Unidades": "{:,.0f}"
                },

                cmap="Purples",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            use_container_width=True,
            hide_index=True,
            height=450
        )

    # ============ PDF ===========
    df_pdf = df_base[
        [
            "DESCRIPCIÓN (ITEM)",
            "Utilidad",
            "Margen %",
            "Ventas",
            "Unidades"
        ]
    ].copy()

    df_pdf.rename(
        columns={
            "DESCRIPCIÓN (ITEM)": "Producto"
        },
        inplace=True
    )

    # ========= TOTAL PDF ===========
    df_pdf.loc[len(df_pdf)] = [
        "Total",
        df_pdf["Utilidad"].sum(),

        (
            df_pdf["Utilidad"].sum()
            /
            df_pdf["Ventas"].sum()
        ) * 100,

        df_pdf["Ventas"].sum(),
        df_pdf["Unidades"].sum()
    ]

    pdf_bytes = generar_pdf_productos(
        df=df_pdf,
        titulo="PRODUCTOS MAS RENTABLES",
        columnas=[
            "Producto",
            "Utilidad",
            "Margen %",
            "Ventas",
            "Unidades"
        ],
        alineacion_columnas=[
            "LEFT",
            "RIGHT",
            "RIGHT",
            "RIGHT",
            "CENTER"
        ],
        format_dict=[
            None,
            "{:,.2f}",
            "S/ {:,.2f}%",
            "S/ {:,.2f}",
            "{:,.0f}"
        ],
        empresa="El Mundo del Celular",
        fecha_inicio=date1,
        fecha_final=date2,
        documento=tipo_documento,
        nombre_archivo="productos_mas_rentables"
    )

    st.download_button(
        label="📄 Exportar PDF",
        data=pdf_bytes,
        file_name="productos_mas_rentables.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    render_divider()



# ======================================================================================
# ========================== VALOR DEL INVENTARIO ======================================
# ======================================================================================
def graph_valor_inventario(df_productos, date1, date2, tipo_documento):

    # ======= PRODUCTOS CON STOCK ========
    df_base = df_productos[
        df_productos["CANTIDAD"] > 0
    ].copy()

    if df_base.empty:
        st.success(
            "✅ No existen productos con stock."
        )
        render_divider()
        return

    # ======= NOMBRE COMPLETO ========
    df_base["Producto Completo"] = (
        df_base["NOMBRE"]
        .astype(str)
        .str.upper()
    )

    # ======== NOMBRE CORTO ============
    df_base["Producto"] = np.where(
        df_base["NOMBRE"].str.len() > 55,
        df_base["NOMBRE"].str.slice(0, 55).str.upper()+ "...",
        df_base["NOMBRE"].str.upper()
    )

    # ======== COSTO UNITARIO ========
    df_base["Costo Unitario"] = (
        df_base["PRECIO DE COMPRA"]
    )

    # ======= VALOR INVENTARIO ========
    df_base["Valor Inventario"] = (
        df_base["CANTIDAD"]
        *
        df_base["PRECIO DE COMPRA"]
    )

    # ======== VALOR TOTAL ===========
    valor_total = (
        df_base["Valor Inventario"].sum()
    )

    # ======== PORCENTAJE DEL INVENTARIO =========
    df_base["% Inventario"] = np.where(
        valor_total > 0,
        (
            df_base["Valor Inventario"]
            /
            valor_total
        ) * 100,
        0
    )

    # ========= ORDENAR =========
    df_base = (
        df_base
        .sort_values("Valor Inventario", ascending=False)
        .reset_index(drop=True)
    )

    # ============ TOP 10 ==============
    df_top10 = (
        df_base
        .head(10)
        .copy()
    )

    df_top10["Texto"] = (
        "S/ "
        + df_top10["Valor Inventario"]
        .map("{:,.0f}".format)
    )

    # =========== LAYOUT ============
    #st.subheader("💰 Valor del Inventario")
    st.markdown("""<div class="graph-title">💰 Valor del Inventario</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([1.6, 1])

    # ========== GRÁFICO ===========
    with col1:
        max_valor_inventario = (df_base["Valor Inventario"].max())

        cantidad = 10 #len(df_base)
        altura_grafico = obtener_altura_grafico(cantidad)

        fig = px.bar(
            df_top10,

            x="Valor Inventario",
            y="Producto",

            orientation="h",

            color="Valor Inventario",
            color_continuous_scale="Blues",

            text="Texto"
        )

        fig.update_traces(
            width=0.55,
            textposition="outside",

            customdata=df_base[
                [
                    "CANTIDAD",
                    "% Inventario",
                ]
            ],

            hovertemplate=
            "<b>%{y}</b><br>"
            "Valor Inventario: S/ %{x:,.2f}<br>"
            "Cantidad: %{customdata[0]:,.0f}<br>"
            "% Inventario: %{customdata[1]:,.2f}%"
            "<extra></extra>"
        )

        fig.update_layout(
            template="plotly_dark",
            height=altura_grafico, #450,
            margin=dict(l=10, r=10, t=10, b=10),

            bargap=0.35,

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False,

            coloraxis_showscale=False,

            xaxis=dict(
                title="Valor del Inventario (S/)",
                range=[0, max_valor_inventario * 1.20],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                zeroline=False
            ),

            yaxis=dict(
                title="",
                categoryorder="total ascending"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "staticPlot": True
            }
        )

    # =========== TABLA ===========
    with col2:
        df_tabla = (
            df_base[
                [
                    "Producto",
                    "CANTIDAD",
                    "Costo Unitario",
                    "Valor Inventario",
                    "% Inventario"
                ]
            ]
            .copy()
        )

        df_tabla.rename(
            columns={
                "CANTIDAD": "Stock",
                "Costo Unitario": "Costo Unit.",
                "% Inventario": "% Invent."
            },
            inplace=True
        )

        # ======= TOTAL PARA LA TABLA ==========
        porcentaje_total = (
            df_tabla["% Invent."].sum()
        )

        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Stock"].sum(),
            np.nan,
            df_tabla["Valor Inventario"].sum(),
            porcentaje_total
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Stock": "{:,.0f}",
                    "Costo Unit.": "S/ {:,.2f}",
                    "Valor Inventario": "S/ {:,.2f}",
                    "% Invent.": "{:,.2f}%"
                },

                cmap="Blues",

                table_styles=[
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1E3A8A"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    }
                ]
            ),

            column_config={
                "Producto": st.column_config.TextColumn("Producto", width="large"),
                "Stock": st.column_config.NumberColumn("Stock", width="small"),
                "Costo Unit.": st.column_config.NumberColumn("Costo Unit.", width="small"),
                "Valor Inventario": st.column_config.NumberColumn("Valor Inventario", width="medium"),
                "% Invent.": st.column_config.NumberColumn("% Invent.", width="small")
            },

            use_container_width=True,
            hide_index=True,
            height=altura_grafico - 40
        )

    # ========== TABLA PDF =======
    df_pdf = (
        df_base[
            [
                "Producto Completo",
                "CANTIDAD",
                "Costo Unitario",
                "Valor Inventario",
                "% Inventario"
            ]
        ]
        .copy()
    )

    df_pdf.rename(
        columns={
            "Producto Completo": "Producto",
            "CANTIDAD": "Stock",
            "Costo Unitario": "Costo Unit.",
            "Valor Inventario": "Valor Invent.",
            "% Inventario": "% Invent."
        },
        inplace=True
    )

    # ========== TOTAL PARA EL PDF =========
    porcentaje_total = (
        df_pdf["% Invent."].sum()
    )

    df_pdf.loc[len(df_pdf)] = [
        "Total",
        df_pdf["Stock"].sum(),
        np.nan,
        df_pdf["Valor Invent."].sum(),
        porcentaje_total
    ]

    # ========= GENERAR PDF ==========
    pdf_bytes = generar_pdf_productos(
        df=df_pdf,
        titulo="VALOR DEL INVENTARIO",
        columnas=[
            "Producto",
            "Stock",
            "Costo Unit.",
            "Valor Invent.",
            "% Invent."
        ],
        alineacion_columnas=[
            "LEFT",
            "CENTER",
            "RIGHT",
            "RIGHT",
            "RIGHT"
        ],
        format_dict={
            "Stock": "{:,.0f}",
            "Costo Unit.": "S/ {:,.2f}",
            "Valor Invent.": "S/ {:,.2f}",
            "% Invent.": "{:,.2f}%"
        },
        empresa="El Mundo del Celular",
        fecha_inicio=date1,
        fecha_final=date2,
        documento=tipo_documento,
        nombre_archivo="valor_inventario",
    )

    # ========== BOTÓN PDF =======
    st.download_button(
        label="📄 Exportar PDF",
        data=pdf_bytes,
        file_name="valor_inventario.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    render_divider()



