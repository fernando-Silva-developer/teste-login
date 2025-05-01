from flask import Flask, request
import sqlite3
import stripe

stripe.api_key = "SUA_SECRET_KEY"
endpoint_secret = "SEU_WEBHOOK_SECRET"

app = Flask(__name__)

def set_paid(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET is_paid = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("Webhook error:", e)
        return "Erro", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        username = session["metadata"]["username"]
        set_paid(username)
        print(f"Pagamento confirmado para {username}")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)