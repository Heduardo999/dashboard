import smtplib

from email.message import EmailMessage


def enviar_email(destino, archivo_pdf):

    remitente = "eduacev@gmail.com"

    password = "mlrrrglrxzbwtjpd"

    msg = EmailMessage()

    msg['Subject'] = "Reporte Automático"

    msg['From'] = remitente

    msg['To'] = destino

    msg.set_content("Adjunto reporte PDF")

    with open(archivo_pdf, "rb") as f:

        file_data = f.read()

    msg.add_attachment(
        file_data,
        maintype='application',
        subtype='pdf',
        filename='reporte.pdf'
    )

    with smtplib.SMTP_SSL(
        'smtp.gmail.com',
        465
    ) as smtp:

        smtp.login(remitente, password)

        smtp.send_message(msg)

        smtp.quit()
    