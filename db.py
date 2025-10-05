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


# --- FONCTIONS D'AUTHENTIFICATION ---
def signup(email, password):
    return supabase.auth.sign_up({"email": email, "password": password})

def login(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


# --- FONCTIONS DE GESTION DES PROFILS ---
def get_user_profile(user_id):
    """Récupère le profil complet d'un utilisateur."""
    try:
        data = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return data.data
    except Exception:
        return None

def get_all_profiles():
    """Récupère tous les profils utilisateurs (pour l'admin)."""
    try:
        data = supabase.table('profiles').select('id, email, role, subscription_status, expiry_date').execute()
        return data.data
    except Exception:
        return []

def update_user_role(user_id, new_role):
    """Met à jour le rôle d'un utilisateur."""
    try:
        supabase.table('profiles').update({'role': new_role}).eq('id', user_id).execute()
        return True
    except Exception:
        return False

def update_user_subscription(user_id):
    """Passe un utilisateur en premium pour 30 jours."""
    try:
        expiry = date.today() + timedelta(days=30)
        supabase.table('profiles').update({
            'subscription_status': 'premium',
            'expiry_date': str(expiry)
        }).eq('id', user_id).execute()
        return True
    except Exception:
        return False


# --- NOUVELLE FONCTION AUTOMATIQUE : vérification quotidienne ---
def check_expired_subscriptions():
    """
    Vérifie les abonnements premium expirés et les repasse en 'free'.
    Cette fonction peut être appelée au démarrage ou via un cron externe.
    """
    try:
        # On récupère tous les comptes premium
        data = supabase.table('profiles').select('id, expiry_date, subscription_status').eq('subscription_status', 'premium').execute()

        if not data.data:
            return 0  # aucun compte premium

        today = date.today()
        expired_users = [
            user['id']
            for user in data.data
            if user.get('expiry_date') and date.fromisoformat(user['expiry_date']) < today
        ]

        for user_id in expired_users:
            supabase.table('profiles').update({
                'subscription_status': 'free',
                'expiry_date': None
            }).eq('id', user_id).execute()

        return len(expired_users)

    except Exception as e:
        st.warning(f"Erreur lors de la vérification des abonnements : {e}")
        return 0


# --- FONCTIONS DE GESTION DES DONNÉES (CRUD) ---
def get_accounts(user_id):
    """Récupère tous les comptes financiers d'un utilisateur."""
    try:
        data = supabase.table('accounts').select('*').eq('user_id', user_id).execute()
        return data.data
    except Exception:
        return []

def add_account(user_id, name, balance, account_type):
    """Ajoute un nouveau compte financier."""
    try:
        supabase.table('accounts').insert({
            'user_id': user_id,
            'name': name,
            'balance': balance,
            'type': account_type
        }).execute()
        return True
    except Exception:
        return False
