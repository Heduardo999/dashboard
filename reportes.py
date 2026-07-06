from io import BytesIO
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import A4, landscape

import os
import pandas as pd


def crear_pdf_reporte(
    nombre_pdf,
    ventas_total,
    total_items,
    total_transacciones,
    graficos=[]
):

    pdf = SimpleDocTemplate(
        nombre_pdf,
        pagesize=letter
    )

    elementos = []

    estilos = getSampleStyleSheet()

    titulo = Paragraph(
        "Reporte Ejecutivo de Ventas",
        estilos['Title']
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    # ================= TABLA RESUMEN =================

    datos = [
        ["Métrica", "Valor"],
        ["Ventas Totales", f"S/ {ventas_total:,.2f}"],
        ["Items Vendidos", f"{total_items:,}"],
        ["Transacciones", f"{total_transacciones:,}"]
    ]

    tabla = Table(datos, colWidths=[220, 220])

    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke)
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 20))

    # ================= GRÁFICOS =================
    for grafico in graficos:

        if os.path.exists(grafico):

            img = Image(grafico)

            img.drawHeight = 250
            img.drawWidth = 500

            elementos.append(img)
            elementos.append(Spacer(1, 20))

    pdf.build(elementos)

    return nombre_pdf


# =====================================================
# GENERAR PDF TABLA PRODUCTOS
# =====================================================
def generar_pdf_productos(df, titulo, columnas, empresa, fecha_inicio, fecha_final, documento, nombre_archivo=None, alineacion_columnas=None, format_dict=None):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elementos = []

    titulo_style = ParagraphStyle(
        "TituloPDF",
        parent=styles["Title"],
        fontSize=18,
        leading=16,
        spaceAfter=2
    )

    # ======= PRE PROCESAR ========
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")

    fecha_ini_txt = fecha_inicio.strftime("%d/%m/%Y")
    fecha_fin_txt = fecha_final.strftime("%d/%m/%Y")

    if len(documento) == 3:
        documento_txt = "Todos"
    elif documento:
        documento_txt = ", ".join(documento)
    else:
        documento_txt = "Todos"

    # ======= TITULO ========
    header = Table(
        [
            [
                Paragraph(
                    f"""
                    <b>{titulo}</b><br/>
                    <font size="10">
                    Periodo: {fecha_ini_txt} - {fecha_fin_txt}<br/>
                    Tipo de Documento: {documento_txt}
                    </font>
                    """,
                    titulo_style
                ),

                Paragraph(
                    f"""
                    <b>{empresa}</b><br/>
                    Fecha: {fecha}<br/>
                    Hora: {hora}
                    """,
                    styles["BodyText"]
                )
            ]
        ],
        colWidths=[700, 130]
    )

    header.setStyle(
        TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ALIGN", (1,0), (1,0), "RIGHT")
        ])
    )

    elementos.append(header)
    elementos.append(Spacer(1, 12))

    # ========== TABLA ==========
    data = [columnas]

    for _, row in df.iterrows():
        fila = []
      
        for col in columnas:

            valor = row[col]

            # Celda vacía
            if pd.isna(valor):
                fila.append("")
                continue

            # Si existe un formato definido para esa columna
            if (
                format_dict is not None
                and col in format_dict
                and isinstance(valor, (int, float))
            ):
                fila.append(
                    format_dict[col].format(valor)
                )

            # Si es numérico pero no tiene formato específico
            elif isinstance(valor, (int, float)):
                fila.append(f"{valor:,.2f}")

            # Texto
            else:
                fila.append(str(valor))
        data.append(fila)

    tabla = Table(data)

    # =========================
    # ALINEACIÓN DINÁMICA
    # =========================
    estilos = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),

        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.white, colors.whitesmoke]),

        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
    ]

    if alineacion_columnas:
        for indice, alineacion in enumerate(alineacion_columnas):
            estilos.append(
                ("ALIGN", (indice, 1), (indice, -1), alineacion)
            )
    
    tabla.setStyle(
        TableStyle(estilos)
    )
    elementos.append(tabla)

    # ======================
    # CREAR PDF
    # ======================
    doc.build(elementos)
    pdf = buffer.getvalue()
    buffer.close()

    if nombre_archivo:
        ruta_pdf = (
            r"D:/proyectos_dashboard/"
            r"proyecto_celular_final/"
            r"reportes_pdf/"
            f"{nombre_archivo}.pdf"
        )

        # aseguramos carpeta existe
        import os
        os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)

        with open(ruta_pdf, "wb") as f:
            f.write(pdf)

        return pdf