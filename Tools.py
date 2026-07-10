import pandas as pd
import streamlit as st
from pandas.api.types import is_numeric_dtype


def aplicar_filtros(df_datos, date1, date2, tipo_documento=None, eliminar_anulados=True, eliminar_fechas=True):
    """Aplica filtros de fechas, anulados y tipos de documento al DataFrame."""
    df_temp = df_datos.copy()

    if eliminar_anulados and 'ESTADO' in df_temp.columns:
        df_temp = df_temp[df_temp['ESTADO'] != 'Anulado'].copy()

    if eliminar_fechas and 'FECHA' in df_temp.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_temp['FECHA']):
            #df_temp['FECHA'] = pd.to_datetime(df_temp['FECHA'])
            df_temp["FECHA"] = pd.to_datetime(df_temp["FECHA"], dayfirst=True, errors="coerce")

        df_temp = df_temp[(df_temp['FECHA'] >= date1) & (df_temp['FECHA'] <= date2)].copy()

    if tipo_documento and len(tipo_documento) > 0 and 'DOCUMENTOS' in df_temp.columns:
        df_temp = df_temp.reset_index(drop=True)
        mask = pd.Series([False] * len(df_temp)
                         , index=df_temp.index)

        doc_str = df_temp['DOCUMENTOS'].astype(str)

        if 'Factura' in tipo_documento:
            mask = mask | doc_str.str.startswith('F', na=False)
        if 'Boleta' in tipo_documento:
            mask = mask | doc_str.str.startswith('B', na=False)
        if 'Ticket' in tipo_documento:
            mask = mask | df_temp['DOCUMENTOS'].isna() | doc_str.str.strip().eq('') | doc_str.str.contains('^\\s*$', na=True)

        df_temp = df_temp[mask].copy()

    return df_temp.reset_index(drop=True)


def limpiar_nombre_vendedor(nombre):
    """Limpia y normaliza nombres de vendedor."""
    if pd.isna(nombre):
        return 'Sin asignar'

    nombre = str(nombre).strip()
    if not nombre or nombre.isspace():
        return 'Sin asignar'

    nombre_lower = nombre.lower()
    if nombre_lower == 'store' or nombre_lower == 'store.':
        return 'Admin'

    if 'store.' in nombre_lower:
        parte = nombre_lower.split('.')[-1]
        if parte and parte != 'store':
            nombre_limpio = parte.capitalize()
            return nombre_limpio[:6] + '.' if len(nombre_limpio) > 6 else nombre_limpio
        return 'Admin'

    if 'store' in nombre_lower and nombre_lower != 'store':
        parte = nombre_lower.replace('store', '').strip(' .')
        if parte:
            nombre_limpio = parte.capitalize()
            return nombre_limpio[:6] + '.' if len(nombre_limpio) > 6 else nombre_limpio

    nombre_limpio = nombre.capitalize()
    return nombre_limpio[:6] + '.' if len(nombre_limpio) > 6 else nombre_limpio


def agregar_fila_totales(df, label_column, label='TOTAL'):
    """Agrega una fila TOTAL a un DataFrame sumando las columnas numéricas."""
    df_totales = df.copy()
    fila_total = {label_column: label}

    for col in df.columns:
        if col == label_column:
            continue
        fila_total[col] = df[col].sum() if is_numeric_dtype(df[col]) else ''

    df_totales.loc['TOTAL'] = fila_total
    return df_totales


def styled_dataframe(df, format_dict=None, cmap=None, table_styles=None):
    """Crea un DataFrame estilizado con gradiente y formato de valores."""
    styled = df.style

    if format_dict:
        styled = styled.format(format_dict)

    if cmap:
        numeric_columns = [col for col in df.columns if is_numeric_dtype(df[col])]
        if numeric_columns:
            styled = styled.background_gradient(cmap=cmap, subset=numeric_columns)

    if table_styles:
        styled = styled.set_table_styles(table_styles)

    return styled


def download_csv_from_df(df, file_name, label, use_container_width=True):
    """Agrega un botón de descarga CSV para un DataFrame."""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label, data=csv, file_name=file_name, mime='text/csv', use_container_width=use_container_width)


def render_divider():
    """Renderiza un separador estándar de Streamlit."""
    st.markdown('---')


def obtener_altura_grafico(cantidad):
    if cantidad == 1:
        return 130
    elif cantidad == 2:
        return 220
    elif cantidad == 3:
        return 280
    elif cantidad == 4:
        return 340
    else:
        return min(500, 120 + cantidad * 55)
