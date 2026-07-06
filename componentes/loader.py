import streamlit as st

def show_overlay_loader(text="Cargando Dashboard..."):
    st.markdown(f"""
        <div class="overlay-loader">
            <div class="overlay-loader-box">
                <div class="overlay-spinner"></div>
                <div class="overlay-loader-text">
                    {text}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)