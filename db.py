# db.py
import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta

# --- CONNEXION SUPABASE ---
@st.cache_resource
def init_supabase_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase: Client = init_supabase_connection()

# ============================================================
# 🧑‍💻 AUTHENTIFICATION
# ============================================================

def signup(email, password):
    """Créer un nouveau compte utilisateur"""
    return supabase.auth.sign_up({"email": email, "password": password})

def login(email, password):
    """Connexion utilisateur"""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def get_current_user():
    """Retourne l'utilisateur actuellement connecté"""
    session = supabase.auth.get_session()
    return session.user if session and session.user else None


# ============================================================
# 👤 PROFILS / ABONNEMENTS
# ============================================================

def get_user_profile(user_id):
    try:
        data = supabase.table('users').select('*').eq('id', user_id).single().execute()
        return data.data
    except Exception as e:
        st.error(f"Erreur profil : {e}")
        return None

def update_user_subscription(user_id):
    """Passe l'utilisateur en Premium pour 30 jours"""
    try:
        expiry = date.today() + timedelta(days=30)
        supabase.table('users').update({
            'subscription_status': 'premium',
            'expiry_date': expiry.isoformat()
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur abonnement : {e}")
        return False


# ============================================================
# 💰 COMPTES FINANCIERS
# ============================================================

def get_accounts(user_id):
    """Récupère tous les comptes financiers d'un utilisateur"""
    try:
        data = supabase.table('accounts').select('*').eq('user_id', user_id).execute()
        return data.data or []
    except Exception as e:
        st.error(f"Erreur comptes : {e}")
        return []

def add_account(user_id, name, balance, account_type):
    """Ajoute un compte financier"""
    try:
        supabase.table('accounts').insert({
            'user_id': user_id,
            'name': name,
            'balance': balance,
            'type': account_type
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erreur ajout compte : {e}")
        return False


# ============================================================
# 💳 TRANSACTIONS
# ============================================================

def add_transaction(user_id, account_id, trans_type, amount, category, description):
    """Ajoute une transaction"""
    try:
        supabase.table('transactions').insert({
            'user_id': user_id,
            'account_id': account_id,
            'type': trans_type,
            'amount': amount,
            'category': category,
            'description': description,
            'date': date.today()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erreur transaction : {e}")
        return False

def get_transactions(user_id):
    """Récupère toutes les transactions de l'utilisateur"""
    try:
        data = supabase.table('transactions').select('*').eq('user_id', user_id).order('date', desc=True).execute()
        return data.data or []
    except Exception as e:
        st.error(f"Erreur récupération transactions : {e}")
        return []


# ============================================================
# 🧾 FACTURES (SIR BUSINESS)
# ============================================================

def add_invoice(user_id, number, client, issue_date, status, total_amount, articles):
    """Crée une nouvelle facture"""
    try:
        supabase.table('invoices').insert({
            'user_id': user_id,
            'number': number,
            'client': client,
            'issue_date': issue_date,
            'status': status,
            'total_amount': total_amount,
            'articles': articles  # stockés en JSON
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erreur ajout facture : {e}")
        return False

def get_invoices(user_id):
    """Liste toutes les factures"""
    try:
        data = supabase.table('invoices').select('*').eq('user_id', user_id).order('issue_date', desc=True).execute()
        return data.data or []
    except Exception as e:
        st.error(f"Erreur récupération factures : {e}")
        return []


# ============================================================
# 📦 STOCKS / PRODUITS
# ============================================================

def add_stock_item(user_id, product_name, description, quantity, purchase_price, sale_price):
    """Ajoute un produit en stock"""
    try:
        supabase.table('stock').insert({
            'user_id': user_id,
            'product_name': product_name,
            'description': description,
            'quantity': quantity,
            'purchase_price': purchase_price,
            'sale_price': sale_price
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erreur ajout stock : {e}")
        return False

def get_stock(user_id):
    """Récupère la liste des produits en stock"""
    try:
        data = supabase.table('stock').select('*').eq('user_id', user_id).execute()
        return data.data or []
    except Exception as e:
        st.error(f"Erreur récupération stock : {e}")
        return []

def update_stock_quantity(item_id, new_quantity):
    """Met à jour la quantité d’un produit"""
    try:
        supabase.table('stock').update({'quantity': new_quantity}).eq('id', item_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur mise à jour stock : {e}")
        return False
