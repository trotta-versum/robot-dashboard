from datetime import datetime

EMAIL_NOTIFICATIONS_ENABLED = False
DEFAULT_ADMIN_EMAIL = "admin@example.com"


def send_completion_email(order_data, recipient_email):
    """
    Funzione placeholder.
    In demo non invia davvero l'email.
    Lo sviluppatore interno potrà collegarla a SMTP aziendale / Outlook / Microsoft 365.
    """

    order_code = order_data.get("COMMESSA", "N/D")
    article = order_data.get("ARTICOLO", "N/D")
    qty = order_data.get("QTA_PRODOTTA", "N/D")

    subject = f"Fine lavorazione ordine {order_code}"
    body = (
        f"Ordine completato.\n"
        f"Commessa: {order_code}\n"
        f"Articolo: {article}\n"
        f"Quantità prodotta: {qty}\n"
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if not EMAIL_NOTIFICATIONS_ENABLED:
        return {
            "sent": False,
            "subject": subject,
            "body": body,
            "message": f"Notifica email predisposta per {recipient_email}. In attesa di integrazione SMTP reale."
        }

    # Qui, in futuro, andrà il codice reale SMTP
    return {
        "sent": True,
        "subject": subject,
        "body": body,
        "message": f"Notifica email inviata a {recipient_email}."
    }
