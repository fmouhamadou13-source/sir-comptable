# db.py
from datetime import date, timedelta
import streamlit as st
from supabase import create_client, Client

# --- CONNEXION SUPABASE ---
@st.cache_resource
def init_supabase_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase_connection()

def get_user_profile(user_id):
    """Récupère toutes les infos du profil (rôle + abonnement)."""
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        else:
            return {}
    except Exception as e:
        print(f"Erreur get_user_profile: {e}")
        return {}
# --- FONCTIONS D'AUTHENTIFICATION ---
def signup(email, password):
    """Inscription + création automatique du profil."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        user = response.user

        if not user:
            return {"error": "Inscription échouée"}

        # Création automatique du profil utilisateur
        supabase.table("profiles").insert({
            "id": user.id,
            "email": email,
            "role": "user",
            "subscription_status": "free",
            "expiry_date": None
        }).execute()

        return {"success": True, "user": user}

    except Exception as e:
        return {"error": str(e)}

def login(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


# --- FONCTIONS DE GESTION DES PROFILS ---

def get_all_users():
    """Récupère tous les profils utilisateurs (pour l'admin)."""
    try:
        data = supabase.table('profiles').select('id, email, role, subscription_status, expiry_date').execute()
        return data.data
    except Exception as e:
        st.error(f"Erreur récupération utilisateurs : {e}")
        return []


def update_user_role(user_id, new_role):
    """Met à jour le rôle d'un utilisateur."""
    try:
        supabase.table('profiles').update({'role': new_role}).eq('id', user_id).execute()
        return True
    except Exception:
        return False

def update_user_subscription(user_id, new_status):
    """Passe un utilisateur en premium ou en free."""
    from datetime import date, timedelta
    try:
        if new_status == 'premium':
            expiry = date.today() + timedelta(days=30)
            update_data = {'subscription_status': 'premium', 'expiry_date': str(expiry)}
        else: # free
            update_data = {'subscription_status': 'free', 'expiry_date': None}
            
        supabase.table('profiles').update(update_data).eq('id', user_id).execute()
        return True
    except Exception:
        return False
# ✅ Fonction propre pour repasser un utilisateur en Free
def revert_to_free(user_id):
    """Reclasse un utilisateur Premium en Free."""
    try:
        supabase.table('profiles').update({
            'subscription_status': 'free',
            'expiry_date': None
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur retour à Free : {e}")
        return False

# --- Vérification automatique des abonnements expirés ---
def check_expired_subscriptions():
    """
    Vérifie les abonnements premium expirés et les repasse en 'free'.
    Peut être appelée au démarrage ou via un cron externe.
    """
    try:
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
