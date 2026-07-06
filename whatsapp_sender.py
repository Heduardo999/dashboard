from twilio.rest import Client


def enviar_whatsapp():

    sid = "ACa8cee18d997a80e01ce00e3ad3813d44"
    token = "3ed557e838bdde2b60262cb596d7b488"
    client = Client(sid, token)

    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body='Reporte generado correctamente',
        to='whatsapp:+51987477494'
    )

    print(message.sid)