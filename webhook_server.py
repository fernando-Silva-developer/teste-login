# webhook_server.py
from flask import Flask, request
import sqlite3
import stripe
import os

app = Flask(__name__)

# Pegando as variáveis de ambiente com segurança
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")           # chave da API da Stripe
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")      # segredo do webhook

# Caminho absoluto do banco para evitar erros no Render
DB_PATH = os.path.join(os.path.dirname(__file__), "usuarios.db")

# --- Atualiza status do usuário no banco ---
def marcar_como_pago(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET status_pagamento = 'pago' WHERE email = ?", (email,))
    conn.commit()
    conn.close()

# --- Rota do webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        print(f"[Webhook] Evento recebido: {event['type']}")  # Log para depuração
    except ValueError as e:
        return f"Invalid payload: {e}", 400
    except stripe.error.SignatureVerificationError as e:
        return f"Invalid signature: {e}", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        if email:
            marcar_como_pago(email)
            print(f"[Webhook] Pagamento confirmado para {email}")  # Log para depuração

    return "Webhook recebido", 200
#@app.route("/webhook", methods=["POST"])
# def webhook():
#     payload = request.data
#     sig_header = request.headers.get("stripe-signature")

#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
#     except ValueError as e:
#         return f"Invalid payload: {e}", 400
#     except stripe.error.SignatureVerificationError as e:
#         return f"Invalid signature: {e}", 400

    # Se pagamento confirmado, marcar como pago
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        if email:
            marcar_como_pago(email)
            print(f"[Webhook] Pagamento confirmado para {email}")

    return "Webhook recebido", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
