import streamlit as st
import stripe
import sqlite3
import bcrypt
import os

# --- CONFIGURAR A CHAVE DA STRIPE USANDO VARIÁVEL DE AMBIENTE ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Defina no painel do Render

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect("usuarios.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        senha_hash TEXT,
        status_pagamento TEXT DEFAULT 'pendente'
    )
    """)
    conn.commit()
    conn.close()

def cadastrar_usuario(email, senha):
    conn = sqlite3.connect("usuarios.db")
    c = conn.cursor()
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO usuarios (email, senha_hash) VALUES (?, ?)", (email, senha_hash))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def verificar_login(email, senha):
    conn = sqlite3.connect("usuarios.db")
    c = conn.cursor()
    c.execute("SELECT senha_hash FROM usuarios WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row and bcrypt.checkpw(senha.encode(), row[0]):
        return True
    return False

def obter_status_pagamento(email):
    conn = sqlite3.connect("usuarios.db")
    c = conn.cursor()
    c.execute("SELECT status_pagamento FROM usuarios WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# --- PAGAMENTO COM STRIPE ---
def criar_checkout(email):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "brl",
                "product_data": {"name": "Acesso Premium"},
                "unit_amount": 500,  # R$5,00
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://SEU_DOMINIO.onrender.com?status=sucesso",  # altere para seu domínio Render
        cancel_url="https://SEU_DOMINIO.onrender.com?status=cancelado",
        customer_email=email
    )
    return session.url

# --- INTERFACE STREAMLIT ---
init_db()
st.set_page_config(page_title="Sistema com Pagamento")
st.title("Acesso ao Sistema")

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

aba = st.sidebar.radio("Menu", ["Login", "Cadastro", "Conteúdo"])

if aba == "Cadastro":
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Cadastrar"):
        if cadastrar_usuario(email, senha):
            st.success("Cadastro realizado! Faça login.")
        else:
            st.error("Usuário já existe.")

elif aba == "Login":
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(email, senha):
            st.session_state.logado = True
            st.session_state.email = email
            st.success("Login realizado!")
        else:
            st.error("Login inválido.")

elif aba == "Conteúdo":
    if not st.session_state.logado:
        st.warning("Faça login primeiro.")
        st.stop()

    status = obter_status_pagamento(st.session_state.email)
    if status == "pago":
        st.success("Acesso liberado ao conteúdo premium!")
        st.markdown("Aqui está seu conteúdo protegido. 🎉")
    else:
        st.warning("Você precisa realizar o pagamento.")
        if st.button("Pagar R$5,00"):
            url = criar_checkout(st.session_state.email)
            st.markdown(f"[Clique aqui para pagar]({url})")
