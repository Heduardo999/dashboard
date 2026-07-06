import sqlite3
import bcrypt


DB_NAME = "database/usuarios.db"


def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def crear_tabla_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def crear_usuario(usuario, nombre, password, rol):
    conn = conectar()
    cursor = conn.cursor()
    password_hash = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO usuarios
            (usuario, nombre, password, rol)
            VALUES (?, ?, ?, ?)
            """, (usuario, nombre, password_hash, rol)
        )

        conn.commit()

        print(f"✅ Usuario {usuario} creado")
    except Exception as e:

        print("❌ Error:", e)

    finally:
        conn.close()

if __name__ == "__main__":
    crear_tabla_usuarios()
    crear_usuario(
        usuario="admin",
        nombre="Eduardo",
        password="admin123",
        rol="Admin"
    )
