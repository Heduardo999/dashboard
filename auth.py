import bcrypt
import streamlit as st

from db import conectar


def verificar_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )


def login(usuario, password):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE usuario = ?
        AND activo = 1
        """, (usuario,)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        if verificar_password(password, user["password"]):
            st.session_state["logged_in"] = True
            st.session_state["usuario"] = user["usuario"]
            st.session_state["nombre"] = user["nombre"]
            st.session_state["rol"] = user["rol"]
            return True
    return False


def logout():
    keys = [
        #"logged_in",
        "usuario",
        "nombre",
        "rol"
    ]

    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def show_login_error(message):
    st.markdown(f"""
        <div style="
            width:100%;
            margin-top:10px;
            padding:12px 14px;
            border-radius:12px;
            background:#fef2f2;
            border:1px solid #fecaca;
            color:#b91c1c;
            font-size:14px;
            font-weight:600;
            text-align:center;
            box-sizing:border-box;
            animation:fadeIn 0.25s ease-in-out;
        ">
            ❌ {message}
        </div>

        <style>
        @keyframes fadeIn {{
            from {{
                opacity:0;
                transform:translateY(-4px);
            }}
            to {{
                opacity:1;
                transform:translateY(0);
            }}
        }}
        </style>
    """, unsafe_allow_html=True)


def show_login_success(message):
    st.markdown(f"""
        <div style="
            width:100%;
            margin-top:10px;
            padding:12px 14px;
            border-radius:12px;
            background:#ecfdf3;
            border:1px solid #bbf7d0;
            color:#166534;
            font-size:14px;
            font-weight:600;
            text-align:center;
            box-sizing:border-box;
            animation:fadeIn 0.25s ease-in-out;
        ">
            ✅ {message}
        </div>

        <style>
        @keyframes fadeIn {{
            from {{
                opacity:0;
                transform:translateY(-4px);
            }}
            to {{
                opacity:1;
                transform:translateY(0);
            }}
        }}
        </style>
    """, unsafe_allow_html=True)