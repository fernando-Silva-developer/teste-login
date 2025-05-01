# webhook_server.py
from flask import Flask, request
import sqlite3
import stripe
import os

app = Flask(__name__)

stripe.api_key = SUA_SECRET_KEY
endpoint_secret = SEU_ENDPOINT

# --- Atualiza status do usuário no banco ---
def marcar_como_pago(email):
    conn = sqlite3.connect("usuarios.db")
    c = conn.cursor()
    c.execute("UPDATE usuarios SET status_pagamento = 'pago' WHERE email = ?", (email,))
    conn.commit()
    conn.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return f"Invalid payload: {e}", 400
    except stripe.error.SignatureVerificationError as e:
        return f"Invalid signature: {e}", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        if email:
            marcar_como_pago(email)
            print(f"Pagamento confirmado para {email}")

    return "Webhook recebido", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
