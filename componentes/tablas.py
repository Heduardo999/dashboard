import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from Tools import aplicar_filtros, styled_dataframe, render_divider
from reportes import generar_pdf_productos
from streamlit_js_eval import streamlit_js_eval

# ======================================================================================
# ======================= EXPANDER ANÁLISIS DE PRODUCTOS ================================
# ======================================================================================
def tabla_productos(df_filtrado):

    with st.expander(
        "📦 Análisis de Productos",
        expanded=False
    ):

        # ==================================================
        # CÁLCULO
        # ==================================================
        df_productos = (
            df_filtrado
            .groupby("DESCRIPCIÓN (ITEM)")
            .agg(
                {
                    "CANTIDAD (ITEM)": "sum",
                    "TOTAL (ITEM)": "sum"
                }
            )
            .reset_index()
        )

        df_productos.rename(
            columns={
                "DESCRIPCIÓN (ITEM)": "Producto",
                "CANTIDAD (ITEM)": "Cant.",
                "TOTAL (ITEM)": "Ventas"
            },
            inplace=True
        )

        # ================= MÁS VENDIDOS =================
        top_productos = (
            df_productos
            .sort_values(
                "Cant.",
                ascending=False
            )
            .head(10)
            .reset_index(drop=True)
        )

        # ================= MENOS VENDIDOS =================
        bottom_productos = (
            df_productos
            .sort_values(
                "Cant.",
                ascending=True
            )
            .head(10)
            .reset_index(drop=True)
        )

        # ==================================================
        # LAYOUT
        # ==================================================
        col1, col2 = st.columns(2)

        # ==================================================
        # TOP PRODUCTOS
        # ==================================================
        with col1:

            st.subheader("🏆 Top 10 Más Vendidos")

            st.dataframe(
                styled_dataframe(
                    top_productos,
                    format_dict={
                        "Cantidad": "{:,.0f}",
                        "Ventas": "S/ {:,.2f}"
                    },
                    cmap="YlGn",
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
                height=390
            )

        # ==================================================
        # BOTTOM PRODUCTOS
        # ==================================================
        with col2:
            st.subheader("📉 Top 10 Menos Vendidos")
            st.dataframe(
                styled_dataframe(
                    bottom_productos,
                    format_dict={
                        "Cant.": "{:,.0f}",
                        "Ventas": "S/ {:,.2f}"
                    },
                    cmap="OrRd",
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
                height=390
            )


# ======================================================================================
# ===================== EXPANDER PRODUCTOS DE BAJA ROTACIÓN ============================
# ======================================================================================
def tabla_baja_rotacion(df, date1, date2, tipo_documento):

    df_filtrado = aplicar_filtros(df, date1, date2, tipo_documento)

    # ====== PRODUCTOS =======
    df_base = (
        df_filtrado
        .groupby("DESCRIPCIÓN (ITEM)")
        .agg(
            Unidades=("CANTIDAD (ITEM)", "sum"),
            Ventas=("TOTAL (ITEM)", "sum")
        )
        .reset_index()
    )

    # ======== PRODUCTOS CON STOCK = 1 ========
    df_base = df_base[
        df_base["Unidades"] == 1
    ]

    if df_base.empty:
        st.success(
            "✅ No existen productos de baja rotación."
        )

        render_divider()
        return
    
    # ====== NOMBRE COMPLETO ========
    df_base["Producto Completo"] = (
        df_base["DESCRIPCIÓN (ITEM)"].str.upper()
    )

    # ====== NOMBRE CORTO =========
    df_base["Producto"] = np.where(
        df_base["DESCRIPCIÓN (ITEM)"].str.len() > 55,
        df_base["DESCRIPCIÓN (ITEM)"].str.slice(0, 55).str.upper()+ "...",
        df_base["DESCRIPCIÓN (ITEM)"].str.upper()
    )

    # ========== ORDENAR ==========
    df_base = (
        df_base
        .sort_values(
            "Ventas",
            ascending=True
        )
        .reset_index(drop=True)
    )

    st.subheader("🐢 Baja Rotación")

    # ========== EXPANDER ==============
    with st.expander(
        f"Ver productos de baja rotación ({len(df_base):,.0f})",
        expanded=False
    ):
        st.caption(
            "Productos con menor cantidad de unidades vendidas en el período."
        )

        df_tabla = (
            df_base[
                [
                    "Producto",
                    "Unidades",
                    "Ventas"
                ]
            ]
            .copy()
        )

        df_pdf = (
            df_base[
                [
                    "Producto Completo",
                    "Unidades",
                    "Ventas"
                ]
            ]
            .copy()
        )

        df_pdf.rename(
            columns={
                "Producto Completo": "Producto"
            },
            inplace=True
        )

        # ========= FILA TOTAL =========
        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Unidades"].sum(),
            df_tabla["Ventas"].sum()
        ]

        df_pdf.loc[len(df_pdf)] = [
            "TOTAL",
            df_pdf["Unidades"].sum(),
            df_pdf["Ventas"].sum()
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Unidades": "{:,.0f}",
                    "Ventas": "S/ {:,.2f}"
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

            column_config={
                "Producto": st.column_config.TextColumn(
                    "Producto",
                    width="large"
                ),
                "Unidades": st.column_config.NumberColumn(
                    "Unidades",
                    width="small"
                ),
                "Ventas": st.column_config.NumberColumn(
                    "Ventas",
                    width="small"
                )
            },

            use_container_width=True,
            hide_index=True,
        )

        # ========== GENERA PDF ============
        pdf_bytes = generar_pdf_productos(
            df=df_pdf,
            titulo="PRODUCTOS DE BAJA ROTACION",
            columnas=[
                "Producto",
                "Unidades",
                "Ventas"
            ],
            alineacion_columnas=[
                "LEFT",
                "CENTER",
                "RIGHT",
            ],
            empresa="El Mundo del Celular",
            fecha_inicio=date1,
            fecha_final=date2,
            documento=tipo_documento,
            nombre_archivo="productos_baja_rotacion"
        )

        # =========== EXPORTA PDF ===========
        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name="productos_baja_rotacion.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    render_divider()



# ======================================================================================
# ====================== EXPANDER PRODUCTOS STOCK CRÍTICO ==============================
# ======================================================================================
def tabla_stock_critico(df_productos, date1, date2, tipo_documento):

    # ========== STOCK CRÍTICO ==========
    df_base = df_productos[
        (
            df_productos["CANTIDAD"] > 0
        )
        &
        (
            df_productos["CANTIDAD"]
            <=
            df_productos["STOCK MÍNIMO"]
        )
    ].copy()

    if df_base.empty:
        st.success(
            "✅ No existen productos en stock crítico."
        )

        render_divider()
        return

    # =========== MÉTRICAS =============
    df_base["FALTANTE"] = (
        df_base["STOCK MÍNIMO"]
        -
        df_base["CANTIDAD"]
    )

    # ========= PRIORIDAD ==============
    df_base["PRIORIDAD"] = np.select(
        [
            df_base["FALTANTE"] >= 5,
            df_base["FALTANTE"] >= 2
        ],
        [
            "🔴 ALTA",
            "🟡 MEDIA"
        ],
        default="🟢 BAJA"
    )

    # ========= NOMBRE COMPLETO ===========
    df_base["Producto Completo"] = (
        df_base["NOMBRE"]
        .astype(str)
        .str.upper()
    )

    # =========== NOMBRE CORTO =============
    df_base["Producto"] = np.where(
        df_base["NOMBRE"].str.len() > 55,
        df_base["NOMBRE"]
        .str.slice(0, 55)
        .str.upper()
        + "...",
        df_base["NOMBRE"]
        .str.upper()
    )

    # ======== ORDENAR ==========
    df_base = (
        df_base
        .sort_values(
            [
                "FALTANTE",
                "STOCK MÍNIMO"
            ],
            ascending=False
        )
        .reset_index(drop=True)
    )

    # ============= ALERTAS =============
    if len(df_base) >= 20:
        st.error(
            f"🚨 Existen {len(df_base):,.0f} productos en stock crítico."
        )
    elif len(df_base) >= 10:
        st.warning(
            f"⚠️ Existen {len(df_base):,.0f} productos en stock crítico."
        )
    else:
        st.info(
            f"ℹ️ Existen {len(df_base):,.0f} productos en stock crítico."
        )

    st.subheader("⚠️ Stock Crítico")

    # =========== EXPANDER ============
    with st.expander(
        f"Ver productos con stock crítico ({len(df_base):,.0f})",
        expanded=False
    ):
        st.caption(
            "Productos cuyo stock actual se encuentra por debajo o igual al stock mínimo."
        )

        # ========== TABLA STREAMLIT ===========
        df_tabla = (
            df_base[
                [
                    "Producto",
                    "CANTIDAD",
                    "STOCK MÍNIMO",
                    "FALTANTE",
                    "PRIORIDAD"
                ]
            ]
            .copy()
        )

        df_tabla.rename(
            columns={
                "CANTIDAD": "Stock",
                "STOCK MÍNIMO": "Stock Min.",
                "FALTANTE": "Faltante",
                "PRIORIDAD": "Prioridad"
            },
            inplace=True
        )

        # ========= TABLA PARA EL PDF ==============
        df_pdf = (
            df_base[
                [
                    "Producto Completo",
                    "CANTIDAD",
                    "STOCK MÍNIMO",
                    "FALTANTE",
                    "PRIORIDAD"
                ]
            ]
            .copy()
        )

        df_pdf.rename(
            columns={
                "Producto Completo": "Producto",
                "CANTIDAD": "Stock",
                "STOCK MÍNIMO": "Stock Min.",
                "FALTANTE": "Faltante",
                "PRIORIDAD": "Prioridad"
            },
            inplace=True
        )

        # ======== FILA TOTAL =============
        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Stock"].sum(),
            df_tabla["Stock Min."].sum(),
            df_tabla["Faltante"].sum(),
            ""
        ]

        df_pdf.loc[len(df_pdf)] = [
            "Total",
            df_pdf["Stock"].sum(),
            df_pdf["Stock Min."].sum(),
            df_pdf["Faltante"].sum(),
            ""
        ]

        # ============== TABLA ==============
        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Stock": "{:,.0f}",
                    "Stock Min.": "{:,.0f}",
                    "FALTANTE": "{:,.0f}"
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
            hide_index=True
        )

        # =========== PDF ================
        pdf_bytes = generar_pdf_productos(
            df=df_pdf,
            titulo="PRODUCTOS EN STOCK CRITICO",
            columnas=[
                "Producto",
                "Stock",
                "Stock Min.",
                "Faltante",
                "Prioridad"
            ],
            alineacion_columnas=[
                "LEFT",
                "CENTER",
                "CENTER",
                "CENTER",
                "CENTER"
            ],
            empresa="El Mundo del Celular",
            fecha_inicio=date1,
            fecha_final=date2,
            documento=tipo_documento,
            nombre_archivo="productos_stock_critico"
        )

        # =========== EXPORTAR PDF ============
        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name="productos_stock_critico.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    render_divider()



# ======================================================================================
# ======================== EXPANDER PRODUCTOS SIN STOCK ================================
# ======================================================================================
def tabla_sin_stock(df_productos, date1, date2, tipo_documento):

    # ========== SIN STOCK ============
    df_base = df_productos[
        df_productos["CANTIDAD"] == 0
    ].copy()

    # ======== CANTIDAD A REPONER =========
    df_base["REPONER"] = (
        df_base["STOCK MÍNIMO"]
    ).fillna(0).astype(int)

    # ========= PRIORIDAD ============
    df_base["PRIORIDAD"] = np.select(
        [
            df_base["REPONER"] >= 10,
            df_base["REPONER"] >= 5
        ],
        [
            "🔴 ALTA",
            "🟡 MEDIA"
        ],
        default="🟢 BAJA"
    )

    # =======================================
    if df_base.empty:
        st.success(
            "✅ No existen productos agotados."
        )
        render_divider()
        return

    # ========= NOMBRE COMPLETO ==============
    df_base["Producto Completo"] = (
        df_base["NOMBRE"]
        .astype(str)
        .str.upper()
    )

    # ========== NOMBRE CORTO ============
    df_base["Producto"] = np.where(
        df_base["NOMBRE"].str.len() > 55,
        df_base["NOMBRE"]
        .str.slice(0, 55)
        .str.upper()
        + "...",
        df_base["NOMBRE"]
        .str.upper()
    )

    # ========== ORDENAR ============
    df_base = (
        df_base
        .sort_values(
            "STOCK MÍNIMO",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # ========== ALERTAS ============
    if len(df_base) >= 20:
        st.error(
            f"🚨 Existen {len(df_base):,.0f} productos sin stock."
        )
    elif len(df_base) >= 10:
        st.warning(
            f"⚠️ Existen {len(df_base):,.0f} productos sin stock."
        )
    else:
        st.info(
            f"ℹ️ Existen {len(df_base):,.0f} productos sin stock."
        )

    # =============== TITULO =============
    st.subheader("❌ Sin Stock")

    # =============== EXPANDER ==============
    with st.expander(
        f"Ver productos sin stock ({len(df_base):,.0f})",
        expanded=False
    ):
        st.caption(
            "Productos agotados que requieren reposición."
        )

        # =========== TABLA STREAMLIT ============
        df_tabla = (
            df_base[
                [
                    "Producto",
                    "REPONER",
                    "PRIORIDAD"
                ]
            ]
            .copy()
        )

        df_tabla.rename(
            columns={
                "REPONER": "Reponer",
                "PRIORIDAD": "Prioridad"
            },
            inplace=True
        )

        # =========== TABLA PDF =============
        df_pdf = (
            df_base[
                [
                    "Producto Completo",
                    "REPONER",
                    "PRIORIDAD"
                ]
            ]
            .copy()
        )

        df_pdf.rename(
            columns={
                "Producto Completo": "Producto",
                "REPONER": "Reponer",
                "PRIORIDAD": "Prioridad"
            },
            inplace=True
        )

        # =========== TOTAL ============
        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Reponer"].sum(),
            ""
        ]

        df_pdf.loc[len(df_pdf)] = [
            "Total",
            df_pdf["Reponer"].sum(),
            ""
        ]

        # ============ TABLA ==============
        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Stock Min.": "{:,.0f}"
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
            hide_index=True
        )

        # =========== PDF ==============
        pdf_bytes = generar_pdf_productos(
            df=df_pdf,
            titulo="PRODUCTOS SIN STOCK",
            columnas=[
                "Producto",
                "Reponer",
                "Prioridad"
            ],
            alineacion_columnas=[
                "LEFT",
                "CENTER",
                "CENTER"
            ],
            empresa="El Mundo del Celular",
            fecha_inicio=date1,
            fecha_final=date2,
            documento=tipo_documento,
            nombre_archivo="productos_sin_stock"
        )

        # ============= EXPORTAR PDF ==========
        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name="productos_sin_stock.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    render_divider()


# ======================================================================================
# ===================== EXPANDER PRODUCTOS SIN MOVIMIENTO ==============================
# ======================================================================================
def tabla_sin_movimiento(df_ventas, df_productos, date1, date2, tipo_documento):


    # ======== VENTAS FILTRADAS ==========
    df_filtrado = aplicar_filtros(df_ventas, date1, date2, tipo_documento)

    # ======== PRODUCTOS VENDIDOS ========
    productos_vendidos = (
        df_filtrado["CÓDIGO (ITEM)"]
        .astype(str)
        .unique()
    )

    # ======== STOCK DISPONIBLE =========
    df_base = df_productos.copy()

    df_base["CODIGO"] = (
        df_base["CÓDIGO"]
        .astype(str)
    )

    # ========= STOCK > 0 =========
    df_base = df_base[
        df_base["CANTIDAD"] > 0
    ]

    # ========= SIN MOVIMIENTO =============
    df_base = df_base[
        ~df_base["CODIGO"]
        .isin(productos_vendidos)
    ]

    if df_base.empty:
        st.success(
            "✅ No existen productos sin movimiento."
        )
        render_divider()
        return

    # ======= VALOR INMOVILIZADO ========
    df_base["VALOR INMOVILIZADO"] = (
        df_base["CANTIDAD"]
        *
        df_base["PRECIO DE COMPRA"]
    )

    # ========= PRIORIDAD ================
    df_base["PRIORIDAD"] = np.select(
        [
            df_base["VALOR INMOVILIZADO"] >= 5000,
            df_base["VALOR INMOVILIZADO"] >= 1000
        ],
        [
            "🔴 ALTA",
            "🟡 MEDIA"
        ],
        default="🟢 BAJA"
    )

    # ========= ALERTAS ===========
    total_inmovilizado = (
        df_base["VALOR INMOVILIZADO"]
        .sum()
    )

    st.error(
        f"💰 Inventario inmovilizado: S/ {total_inmovilizado:,.2f}"
    )

    # ========= NOMBRE COMPLETO ===========
    df_base["Producto Completo"] = (
        df_base["NOMBRE"]
        .astype(str)
        .str.upper()
    )

    df_base["Producto"] = np.where(
        df_base["NOMBRE"].str.len() > 55,
        df_base["NOMBRE"].str.slice(0, 55).str.upper()+ "...",

        df_base["NOMBRE"]
        .str.upper()
    )

    # ========== ORDENAR ===========
    df_base = (
        df_base
        .sort_values(
            "VALOR INMOVILIZADO",
            ascending=False
        )
        .reset_index(drop=True)
    )

    st.subheader("💤 Sin Movimiento")

    # ============== EXPANDER =====================
    with st.expander(
        f"Ver productos sin movimiento ({len(df_base):,.0f})",
        expanded=False
    ):
        st.caption(
            "Productos con stock disponible pero sin ventas en el período."
        )

        # ============= TABLA ==============
        df_tabla = (
            df_base[
                [
                    "Producto",
                    "CANTIDAD",
                    "VALOR INMOVILIZADO",
                    "PRIORIDAD"
                ]
            ]
            .copy()
        )

        df_tabla.rename(
            columns={
                "CANTIDAD": "Stock",
                "VALOR INMOVILIZADO": "Valor",
                "PRIORIDAD": "Prioridad"
            },
            inplace=True
        )

        # ============ PDF =============
        df_pdf = (
            df_base[
                [
                    "Producto Completo",
                    "CANTIDAD",
                    "VALOR INMOVILIZADO",
                    "PRIORIDAD"
                ]
            ]
            .copy()
        )

        df_pdf.rename(
            columns={
                "Producto Completo": "Producto",
                "CANTIDAD": "Stock",
                "VALOR INMOVILIZADO": "Valor",
                "PRIORIDAD": "Prioridad"
            },
            inplace=True
        )

        # TOTAL
        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Stock"].sum(),
            df_tabla["Valor"].sum(),
            ""
        ]

        df_pdf.loc[len(df_pdf)] = [
            "TOTAL",
            df_pdf["Stock"].sum(),
            df_pdf["Valor"].sum(),
            ""
        ]

        # =============== TABLA ==============
        st.dataframe(
            styled_dataframe(
                df_tabla,

                format_dict={
                    "Stock": "{:,.0f}",
                    "Valor": "S/ {:,.2f}"
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
            hide_index=True
        )

        # ============ PDF =============
        pdf_bytes = generar_pdf_productos(
            df=df_pdf,
            titulo="PRODUCTOS SIN MOVIMIENTO",
            columnas=[
                "Producto",
                "Stock",
                "Valor",
                "Prioridad"
            ],
                alineacion_columnas=[
                "LEFT",
                "CENTER",
                "RIGHT",
                "CENTER"
            ],
            empresa="El Mundo del Celular",
            fecha_inicio=date1,
            fecha_final=date2,
            documento=tipo_documento,
            nombre_archivo="productos_sin_movimiento"
        )

        # ============= EXPORTAR ==============
        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name="productos_sin_movimiento.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    render_divider()


# ======================================================================================
# =========================== EXPANDER MARGEN BAJO =====================================
# ======================================================================================
def tabla_margen_bajo(df_ventas, df_productos, date1, date2, tipo_documento):

    # ======== FILTRO DE VENTAS ============
    df_filtrado = aplicar_filtros(df_ventas, date1, date2, tipo_documento)

    # =========== MERGE CON PRODUCTOS (PARA COSTO) ==========
    df_base = df_filtrado.merge(
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

    df_base = df_base.dropna(subset=["PRECIO DE COMPRA"])

    if df_base.empty:
        st.success("✅ No existen productos para análisis de margen.")
        render_divider()
        return

    # ============ 🔥 PASO CLAVE: TOTALES POR LÍNEA ===============
    df_base["VENTA_TOTAL"] = (
        df_base["PRECIO UNITARIO (ITEM)"]
        * df_base["CANTIDAD (ITEM)"]
    )

    df_base["COSTO_TOTAL"] = (
        df_base["PRECIO DE COMPRA"]
        * df_base["CANTIDAD (ITEM)"]
    )

    # ========= 🔥 GROUPBY CORRECTO (NIVEL PRODUCTO) ===========
    df_base = (
        df_base
        .groupby("DESCRIPCIÓN (ITEM)")
        .agg(
            Unidades=("CANTIDAD (ITEM)", "sum"),
            VENTA_TOTAL=("VENTA_TOTAL", "sum"),
            COSTO_TOTAL=("COSTO_TOTAL", "sum")
        )
        .reset_index()
    )

    # ========== MÉTRICAS ==========
    df_base["UTILIDAD"] = (
        df_base["VENTA_TOTAL"] - df_base["COSTO_TOTAL"]
    )

    df_base["MARGEN"] = np.where(
        df_base["VENTA_TOTAL"] > 0,
        (df_base["UTILIDAD"] / df_base["VENTA_TOTAL"]) * 100,
        0
    )

    # ============ ALERTAS MARGEN =========
    df_base["ALERTA"] = np.select(
        [
            df_base["MARGEN"] <= 10,
            df_base["MARGEN"] <= 25
        ],
        [
            "🔴 CRÍTICO",
            "🟡 BAJO"
        ],
        default="🟢 OK"
    )

    # ========== SOLO PRODUCTOS CON MARGEN BAJO ==========
    df_base = df_base[
        df_base["MARGEN"] <= 40
    ].copy()

    if df_base.empty:
        st.success("✅ No existen productos con margen bajo en el período.")
        render_divider()
        return

    # ========== ORDENAR (PEOR MARGEN PRIMERO) ============
    df_base = (
        df_base
        .sort_values("MARGEN", ascending=True)
        .reset_index(drop=True)
    )

    # ========== ALERTA GENERAL ===========
    if len(df_base) >= 20:
        st.error(f"🚨 {len(df_base)} productos con margen bajo")
    elif len(df_base) >= 10:
        st.warning(f"⚠️ {len(df_base)} productos con margen bajo")
    else:
        st.info(f"ℹ️ {len(df_base)} productos con margen bajo")

    st.subheader("📉 Margen Bajo")

    # =========== EXPANDER =========
    with st.expander(
        f"Ver productos con margen <= 40% ({len(df_base):,.0f})",
        expanded=False
    ):
        st.caption(
            "Productos consolidados con menor rentabilidad en el período."
        )

        # =========== TABLA STREAMLIT ==========
        df_tabla = df_base[
            [
                "DESCRIPCIÓN (ITEM)",
                "Unidades",
                "VENTA_TOTAL",
                "COSTO_TOTAL",
                "MARGEN",
                "ALERTA"
            ]
        ].copy()

        df_tabla.rename(
            columns={
                "DESCRIPCIÓN (ITEM)": "Producto",
                "VENTA_TOTAL": "Ventas",
                "COSTO_TOTAL": "Costo",
                "MARGEN": "Margen %",
                "ALERTA": "Alerta"
            },
            inplace=True
        )

        # ========= TOTAL GENERAL ===========
        df_tabla.loc[len(df_tabla)] = [
            "Total",
            df_tabla["Unidades"].sum(),
            df_tabla["Ventas"].sum(),
            df_tabla["Costo"].sum(),
            (
                (df_base["VENTA_TOTAL"].sum() - df_base["COSTO_TOTAL"].sum())
                / df_base["VENTA_TOTAL"].sum()
            ) * 100,
            ""
        ]

        st.dataframe(
            styled_dataframe(
                df_tabla,
                format_dict={
                    "Unidades": "{:,.0f}",
                    "Ventas": "S/ {:,.2f}",
                    "Costo": "S/ {:,.2f}",
                    "Margen %": "{:,.2f}%"
                },
                cmap="RdYlGn_r",
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
            hide_index=True
        )

        # ============= PDF ==========
        df_pdf = df_base[
            [
                "DESCRIPCIÓN (ITEM)",
                "Unidades",
                "VENTA_TOTAL",
                "COSTO_TOTAL",
                "MARGEN",
                "ALERTA"
            ]
        ].copy()

        df_pdf.rename(
            columns={
                "DESCRIPCIÓN (ITEM)": "Producto",
                "VENTA_TOTAL": "Ventas",
                "COSTO_TOTAL": "Costo",
                "MARGEN": "Margen %",
                "ALERTA": "Alerta"
            },
            inplace=True
        )

        # ========= TOTAL PDF ===========
        df_pdf.loc[len(df_pdf)] = [
            "Total",
            df_pdf["Unidades"].sum(),
            f"S/ {df_pdf['Ventas'].sum():,.2f}",
            f"S/ {df_pdf['Costo'].sum():,.2f}",
            f"{(
                (df_base['VENTA_TOTAL'].sum() - df_base['COSTO_TOTAL'].sum())
                / df_base['VENTA_TOTAL'].sum()
            ) * 100:,.2f}%",
            ""
        ]

        pdf_bytes = generar_pdf_productos(
            df=df_pdf,
            titulo="PRODUCTOS CON MARGEN BAJO",
            columnas=[
                "Producto",
                "Unidades",
                "Ventas",
                "Costo",
                "Margen %",
                "Alerta"
            ],
            alineacion_columnas=[
                "LEFT",
                "CENTER",
                "RIGHT",
                "RIGHT",
                "RIGHT",
                "CENTER"
            ],
            empresa="El Mundo del Celular",
            fecha_inicio=date1,
            fecha_final=date2,
            documento=tipo_documento,
            nombre_archivo="productos_margen_bajo"
        )

        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name="productos_margen_bajo.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    render_divider()


