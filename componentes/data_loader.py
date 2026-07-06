import pandas as pd
import streamlit as st


# ================= CARGAR VENTAS =================
@st.cache_data(show_spinner=False)
def cargar_ventas():
    df = pd.read_excel(
        "data/ventas.xlsx",
        skiprows=8
    )
    return df


# ================= CARGAR PAGOS =================
@st.cache_data(show_spinner=False)
def cargar_pagos():
    df = pd.read_excel(
        "data/pagos.xlsx",
        skiprows=4
    )
    return df


# =============== CARGAR PRODUCTOS =================
@st.cache_data(show_spinner=False)
def cargar_productos():
    df = pd.read_excel(
        "data/productos.xlsx",
        skiprows=4
    )
    return df