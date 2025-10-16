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
# --- NOUVEAU : CONNEXION ADMIN (ignore les RLS) ---
@st.cache_resource
def init_supabase_admin_connection():
    url = st.secrets["supabase"]["url"]
    service_key = st.secrets["supabase"]["service_key"]
    return create_client(url, service_key)

supabase_admin = init_supabase_admin_connection()

def get_user_profile(user_id):
    """Récupère toutes les infos du profil (rôle + abonnement)."""
    try:
        # CORRECTION : On utilise le client admin pour garantir la lecture du profil
        response = supabase_admin.table("profiles").select("*").eq("id", user_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Erreur get_user_profile: {e}")
        return {}

def update_profile_settings(user_id, settings_data):
    """Met à jour les paramètres de facturation dans le profil d'un utilisateur."""
    try:
        supabase_admin.table('profiles').update(settings_data).eq('id', user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour des paramètres : {e}")
        return False
        
# --- FONCTIONS D'AUTHENTIFICATION ---
def signup(email, password):
    """Inscription de l'utilisateur ET création de son profil."""
    try:
        # Étape A : Inscription auprès de Supabase Auth
        response = supabase.auth.sign_up({"email": email, "password": password})
        user = response.user

        if user:
            # Étape B : Création du profil avec le client ADMIN
            supabase_admin.table("profiles").insert({
                "id": user.id,
                "email": email,
                "role": "user",  # CORRECTION : Valeur par défaut correcte
                "subscription_status": "free" # CORRECTION : Valeur par défaut correcte
            }).execute()
            
            return {"success": True, "user": user}
        else:
            return {"error": "L'utilisateur n'a pas pu être créé dans Supabase Auth."}

    except Exception as e:
        return {"error": str(e)}

def login(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


# --- FONCTIONS DE GESTION DES PROFILS ---

def get_all_users():
    """Récupère tous les profils utilisateurs (pour l'admin)."""
    try:
        data = supabase_admin.table('profiles').select('id, email, role, subscription_status, expiry_date').execute()
        return data.data
    except Exception as e:
        st.error(f"Erreur récupération utilisateurs : {e}")
        return []

def update_user_role(user_id, new_role):
    """Met à jour le rôle d'un utilisateur."""
    try:
        # CORRECTION : On utilise le client admin pour modifier les autres utilisateurs
        supabase_admin.table('profiles').update({'role': new_role}).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Erreur update_user_role: {e}")
        return False

def update_user_subscription(user_id, new_status):
    """Passe un utilisateur en premium ou en free."""
    from datetime import date, timedelta
    try:
        if new_status == 'premium':
            expiry = date.today() + timedelta(days=30)
            update_data = {'subscription_status': new_status, 'expiry_date': str(expiry)}
        else: # free
            update_data = {'subscription_status': new_status, 'expiry_date': None}
            
        # CORRECTION : On utilise le client admin pour modifier les autres utilisateurs
        supabase_admin.table('profiles').update(update_data).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Erreur update_user_subscription: {e}")
        return False
# ✅ Fonction propre pour repasser un utilisateur en Free
def revert_to_free(user_id):
    """Reclasse un utilisateur Premium en Free."""
    try:
        supabase_admin.table('profiles').update({
            'subscription_status': 'free',
            'expiry_date': None
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        # Pour une tâche de fond, il est souvent mieux d'afficher dans la console
        print(f"Erreur retour à Free : {e}")
        return False
        
# --- FONCTIONS DE GESTION DES TRANSACTIONS ---

def get_transactions(user_id):
    """Récupère toutes les transactions pour un utilisateur donné."""
    try:
        response = supabase.table('transactions').select('*').eq('user_id', user_id).order('date', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur lors de la récupération des transactions : {e}")
        return []

def add_transaction_to_db(user_id, data):
    """Ajoute une seule transaction à la base de données."""
    try:
        # On s'assure que user_id est bien dans les données à insérer
        data['user_id'] = user_id
        supabase.table('transactions').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'ajout de la transaction : {e}")
        return False
# --- MODIFICATION DE LA FONCTION CHECK_EXPIRED_SUBSCRIPTIONS ---
def check_expired_subscriptions():
    """
    Vérifie les abonnements premium expirés et les repasse en 'free'.
    """
    try:
        # ON UTILISE LE CLIENT ADMIN ICI
        response = supabase_admin.table('profiles').select('id, expiry_date, subscription_status').eq('subscription_status', 'premium').execute()
        
        if not response.data:
            return 0

        today = date.today()
        expired_users = [
            user['id']
            for user in response.data
            if user.get('expiry_date') and date.fromisoformat(user['expiry_date']) < today
        ]

        for user_id in expired_users:
            # ON UTILISE AUSSI LE CLIENT ADMIN POUR METTRE À JOUR
            supabase_admin.table('profiles').update({
                'subscription_status': 'free',
                'expiry_date': None
            }).eq('id', user_id).execute()

        return len(expired_users)

    except Exception as e:
        # On affiche l'erreur dans la console de Streamlit pour le débogage
        print(f"Erreur lors de la vérification des abonnements : {e}")
        return 0

# --- FONCTIONS DE GESTION DES DONNÉES (CRUD) ---
def get_accounts(user_id):
    """Récupère tous les comptes financiers d'un utilisateur."""
    try:
        data = supabase.table('accounts').select('*').eq('user_id', user_id).execute()
        return data.data
    except Exception:
        return []

# db.py

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
    except Exception as e:
        # CETTE LIGNE EST LA PLUS IMPORTANTE !
        # Elle affichera l'erreur technique exacte dans l'application.
        st.error(f"DÉTAIL DE L'ERREUR SUPABASE : {e}") 
        return False
# --- FONCTIONS DE GESTION DES SALAIRES ---

def get_employees(user_id):
    """Récupère tous les employés d'un utilisateur."""
    try:
        # CORRECTION : Utilisation de 'Employees' avec une majuscule
        response = supabase.table('Employees').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur DB (get_employees): {e}")
        return []

def add_employee(user_id, nom, poste, salaire):
    """Ajoute un nouvel employé à la base de données."""
    try:
        # CORRECTION : Utilisation de 'Employees' avec une majuscule
        supabase.table('Employees').insert({
            'user_id': user_id,
            'nom_employe': nom,
            'poste': poste,
            'salaire_brut': salaire
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erreur DB (add_employee): {e}")
        return False
        
# --- FONCTIONS DE GESTION DES FACTURES ---

def get_invoices(user_id):
    """Récupère toutes les factures d'un utilisateur."""
    try:
        response = supabase.table('invoices').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur DB (get_invoices): {e}")
        return []

def add_invoice(invoice_data):
    """Ajoute une nouvelle facture à la base de données."""
    try:
        # Le user_id est déjà dans le dictionnaire, on peut donc insérer directement
        supabase.table('invoices').insert(invoice_data).execute()
        return True
    except Exception as e:
        st.error(f"Erreur DB (add_invoice): {e}")
        return False
        
# --- FONCTIONS DE GESTION DU STOCK ---

def get_stock(user_id):
    """Récupère tout le stock d'un utilisateur."""
    try:
        # Assurez-vous que le nom de la table est 'stock' (en minuscules)
        response = supabase.table('stock').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur DB (get_stock): {e}")
        return []

def add_stock_item(item_data):
    """Ajoute un nouvel article au stock."""
    try:
        supabase.table('stock').insert(item_data).execute()
        return True
    except Exception as e:
        st.error(f"Erreur DB (add_stock_item): {e}")
        return False

def update_stock_quantity(user_id, product_name, change_in_quantity):
    """Modifie la quantité d'un produit. Renvoie un tuple (succès, message)."""
    try:
        # Assurez-vous que les noms de table ('stock') et de colonne ('product_name', 'quantity') sont corrects
        product = supabase.table('stock').select('id, quantity').eq('user_id', user_id).eq('product_name', product_name).single().execute()

        if product.data:
            current_quantity = product.data.get('quantity', 0)
            new_quantity = current_quantity + change_in_quantity
            
            supabase.table('stock').update({'quantity': new_quantity}).eq('id', product.data['id']).execute()
            return (True, f"Stock de '{product_name}' mis à jour.")
        else:
            # C'est la cause la plus probable de l'échec : le produit n'est pas trouvé
            return (False, f"AVERTISSEMENT : Le produit '{product_name}' n'a pas été trouvé dans le stock. La quantité n'a pas été mise à jour.")
            
    except Exception as e:
        # Affiche l'erreur technique si quelque chose d'autre se passe (ex: problème de RLS)
        return (False, f"Erreur technique lors de la mise à jour du stock : {e}")

def get_next_invoice_number(user_id):
    """Trouve le prochain numéro de facture séquentiel pour un utilisateur."""
    try:
        # On utilise le client admin pour être sûr de pouvoir lire toutes les factures de l'utilisateur
        response = supabase_admin.table('invoices').select('number').eq('user_id', user_id).execute()
        
        if not response.data:
            return 1 # C'est la toute première facture

        max_num = 0
        for item in response.data:
            try:
                # On extrait le nombre après le tiret (ex: de "FACT-007", on extrait 7)
                num_part = int(item['number'].split('-')[1])
                if num_part > max_num:
                    max_num = num_part
            except (ValueError, IndexError):
                # Ignore les numéros de facture mal formatés
                continue
                
        return max_num + 1
    except Exception as e:
        print(f"Erreur get_next_invoice_number: {e}")
        # En cas d'erreur, on se rabat sur une méthode moins fiable pour éviter de bloquer l'utilisateur
        return len(response.data) + 1 if 'response' in locals() and response.data else 1
        
def delete_stock_item(user_id, item_id):
    """Supprime un article du stock en utilisant son ID."""
    try:
        supabase.table('stock').delete().eq('user_id', user_id).eq('id', item_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur DB (delete_stock_item): {e}")
        return False
