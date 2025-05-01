import streamlit as st
import sqlite3
import bcrypt
import stripe

stripe.api_key = "SUA_SECRET_KEY"

def get_conn():
    return sqlite3.connect("users.db", check_same_thread=False)

def create_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            is_paid INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    return c.fetchone()

def login():
    st.subheader("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        u = get_user(username)
        if not u:
            st.error("Usuário não encontrado")
        elif not bcrypt.checkpw(password.encode(), u[1].encode()):
            st.error("Senha incorreta")
        else:
            st.session_state.logged = True
            st.session_state.user = username
            st.success("Logado com sucesso")

def register():
    st.subheader("Cadastro")
    username = st.text_input("Novo usuário")
    password = st.text_input("Nova senha", type="password")
    if st.button("Cadastrar"):
        if get_user(username):
            st.warning("Usuário já existe")
        else:
            add_user(username, password)
            st.success("Usuário cadastrado!")

def payment():
    st.subheader("Pagamento")
    if st.button("Gerar link de pagamento"):
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'unit_amount': 990,
                    'product_data': {'name': 'Acesso ao sistema'}
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://SEU_DOMINIO_STREAMLIT.onrender.com',
            cancel_url='https://SEU_DOMINIO_STREAMLIT.onrender.com',
            metadata={'username': st.session_state.user}
        )
        st.markdown(f"[Clique aqui para pagar]({session.url})")

def main():
    st.title("MVP com Login e Stripe")

    create_table()

    if "logged" not in st.session_state:
        st.session_state.logged = False
        st.session_state.user = None

    if not st.session_state.logged:
        option = st.sidebar.selectbox("Menu", ["Login", "Cadastro"])
        if option == "Login":
            login()
        else:
            register()
    else:
        st.sidebar.success(f"Usuário: {st.session_state.user}")
        if st.sidebar.button("Sair"):
            st.session_state.logged = False
            st.session_state.user = None
            st.rerun()

        user = get_user(st.session_state.user)
        if user and not user[2]:
            payment()
        else:
            st.success("Acesso liberado! 🎉")

if __name__ == "__main__":
    main()