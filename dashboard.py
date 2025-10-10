# --- IMPORTS AND SUPABASE CONNECTION ---
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, date
import io
import plotly.express as px
from fpdf import FPDF
import requests
import os
from supabase import create_client, Client
from db import (
    get_user_profile, check_expired_subscriptions, login, signup, 
    get_all_users, update_user_role, update_user_subscription,
    get_transactions, add_transaction_to_db,
    get_accounts, add_account,
    get_accounts, add_account,
    get_employees, add_employee
)
# dashboard.py

def load_user_data(user_id):
    """Charge TOUTES les données de l'utilisateur depuis la BDD vers st.session_state."""
    # --- CHARGEMENT DES TRANSACTIONS ---
    transactions_data = get_transactions(user_id)
    if transactions_data:
        st.session_state.transactions = pd.DataFrame(transactions_data)
        st.session_state.transactions.rename(columns={
            'date': 'Date',
            'type': 'Type',
            'amount': 'Montant',      # <-- CORRECTION N°1
            'category': 'Catégorie',   # <-- CORRECTION N°2
            'description': 'Description'
        }, inplace=True)
        st.session_state.transactions['Date'] = pd.to_datetime(st.session_state.transactions['Date'])
        st.session_state.transactions['Montant'] = pd.to_numeric(st.session_state.transactions['Montant'])
    else:
        st.session_state.transactions = pd.DataFrame(columns=[
            'Date', 'Type', 'Montant', 'Catégorie', 'Description'
        ])
        
    # --- NOUVEAU : CHARGEMENT DES COMPTES ---
    accounts_data = get_accounts(user_id)
    if accounts_data:
        st.session_state.comptes = pd.DataFrame(accounts_data)
        # Attention aux noms des colonnes, adaptez si besoin !
        st.session_state.comptes.rename(columns={
            'name': 'Nom du Compte',
            'balance': 'Solde Actuel',
            'type': 'Type'
        }, inplace=True)
    else:
        st.session_state.comptes = pd.DataFrame(columns=[
            'Nom du Compte', 'Solde Actuel', 'Type'
        ])
    # --- CHARGEMENT DES SALAIRES ---
    employees_data = get_employees(user_id)
    if employees_data:
        st.session_state.salaries = pd.DataFrame(employees_data)
        # On renomme les colonnes pour correspondre à l'affichage
        st.session_state.salaries.rename(columns={
            'nom_employe': "Nom de l'employé",
            'poste': 'Poste',
            'salaire_brut': 'Salaire Brut'
        }, inplace=True)
    else:
        st.session_state.salaries = pd.DataFrame(columns=[
            "Nom de l'employé", 'Poste', 'Salaire Brut'
        ])
        
# Vérifie les abonnements expirés à chaque lancement
expired_count = check_expired_subscriptions()
if expired_count > 0:
    st.info(f"🕓 {expired_count} abonnement(s) premium expiré(s) ont été réinitialisés.")

# --- DICTIONNAIRE DE TRADUCTION COMPLET ---
TEXTS = {
    # General & Login/Signup
    "login": {"Français": "Connexion", "Anglais": "Login"},
    "signup": {"Français": "Inscription", "Anglais": "Sign Up"},
    "username": {"Français": "Nom d'utilisateur", "Anglais": "Username"},
    "password": {"Français": "Mot de passe", "Anglais": "Password"},
    "email": {"Français": "Email", "Anglais": "Email"},
    "login_button": {"Français": "Se connecter", "Anglais": "Log In"},
    "signup_button": {"Français": "S'inscrire", "Anglais": "Sign Up"},
    "logout_button": {"Français": "Déconnexion", "Anglais": "Logout"},
    "welcome_back": {"Français": "Bon retour", "Anglais": "Welcome back"},
    "invalid_credentials": {"Français": "Identifiants de connexion invalides.", "Anglais": "Invalid login credentials."},
    "signup_success": {"Français": "Inscription réussie ! Veuillez vérifier votre email pour confirmer.", "Anglais": "Signup successful! Please check your email to confirm."},
    "signup_error": {"Français": "Impossible de s'inscrire. L'utilisateur existe peut-être déjà.", "Anglais": "Could not sign up. The user may already exist."},

    # Sidebar
    "sidebar_dashboard": {"Français": "Tableau de Bord", "Anglais": "Dashboard"},
    "sidebar_accounts": {"Français": "Mes Comptes", "Anglais": "My Accounts"},
    "sidebar_transactions": {"Français": "Transactions", "Anglais": "Transactions"},
    "sidebar_business": {"Français": "Sir Business", "Anglais": "Sir Business"},
    "sidebar_reports": {"Français": "Rapports", "Anglais": "Reports"},
    "sidebar_subscribe": {"Français": "S'abonner", "Anglais": "Subscribe"},
    "sidebar_settings": {"Français": "Paramètres", "Anglais": "Settings"},
    "logo_file_missing": {"Français": "Le fichier 'logo sir comptable.jpg' est manquant.", "Anglais": "The file 'logo sir comptable.jpg' is missing."},

    # Dashboard Page
    "dashboard_title": {"Français": "Tableau de Bord", "Anglais": "Dashboard"},
    "sarcasm_mode": {"Français": "Mode Sarcasme", "Anglais": "Sarcasm Mode"},
    "revenues": {"Français": "Revenus", "Anglais": "Revenues"},
    "expenses": {"Français": "Dépenses", "Anglais": "Expenses"},
    "net_balance": {"Français": "Solde Net", "Anglais": "Net Balance"},
    "monthly_evolution": {"Français": "Évolution Mensuelle", "Anglais": "Monthly Evolution"},
    "no_data_for_graph": {"Français": "Aucune donnée pour afficher le graphique.", "Anglais": "No data to display for the chart."},
    "expense_distribution": {"Français": "Répartition des Dépenses", "Anglais": "Expense Distribution"},
    "no_expense_to_show": {"Français": "Aucune dépense à afficher.", "Anglais": "No expense to display."},
    "talk_to_sir_comptable": {"Français": "Parler à Sir Comptable", "Anglais": "Talk to Sir Comptable"},
    "thinking": {"Français": "Sir Comptable est en train de réfléchir...", "Anglais": "Sir Comptable is thinking..."},
    "enter_a_question": {"Français": "Veuillez entrer une question.", "Anglais": "Please enter a question."},
    "error_ai_contact": {"Français": "Impossible de contacter Sir Comptable pour un commentaire.", "Anglais": "Could not contact Sir Comptable for a comment."},
    "error_ai_speechless": {"Français": "Sir Comptable est momentanément sans voix.", "Anglais": "Sir Comptable is momentarily speechless."},
    "error_ai_response": {"Français": "L'IA a rencontré une erreur", "Anglais": "The AI encountered an error"},
    "error_ai_unexpected": {"Français": "Réponse inattendue de l'IA", "Anglais": "Unexpected response from the AI"},
    "error_hf_token_missing": {"Français": "Erreur : Le token Hugging Face (HF_TOKEN) n'est pas trouvé.", "Anglais": "Error: Hugging Face token (HF_TOKEN) not found."},

    # Accounts Page
    "accounts_title": {"Français": "Mes Comptes", "Anglais": "My Accounts"},
    "accounts_description": {"Français": "Gérez ici les différentes sources de vos finances.", "Anglais": "Manage your different financial sources here."},
    "accounts_list": {"Français": "Liste de vos comptes", "Anglais": "List of your accounts"},
    "download_excel": {"Français": "📥 Télécharger en Excel (.xlsx)", "Anglais": "📥 Download as Excel (.xlsx)"},
    "manage_accounts": {"Français": "Gérer les comptes", "Anglais": "Manage accounts"},
    "select_account": {"Français": "Sélectionnez un compte", "Anglais": "Select an account"},
    "choose": {"Français": "<Choisir>", "Anglais": "<Choose>"},
    "edit": {"Français": "Modification", "Anglais": "Editing"},
    "name": {"Français": "Nom", "Anglais": "Name"},
    "balance": {"Français": "Solde", "Anglais": "Balance"},
    "modify_button": {"Français": "Modifier", "Anglais": "Modify"},
    "delete_button": {"Français": "Supprimer", "Anglais": "Delete"},
    "account_updated": {"Français": "Compte mis à jour.", "Anglais": "Account updated."},
    "account_deleted": {"Français": "Compte supprimé.", "Anglais": "Account deleted."},
    "add_new_account": {"Français": "Ajouter un nouveau compte", "Anglais": "Add a new account"},
    "account_name": {"Français": "Nom du Compte", "Anglais": "Account Name"},
    "account_type": {"Français": "Type", "Anglais": "Type"},
    "initial_balance": {"Français": "Solde Initial", "Anglais": "Initial Balance"},
    "add_button": {"Français": "Ajouter", "Anglais": "Add"},
    "account_added": {"Français": "Compte ajouté et solde initial enregistré comme revenu.", "Anglais": "Account added and initial balance recorded as revenue."},
    
    # Transactions Page
    "transactions_title": {"Français": "Historique des Transactions", "Anglais": "Transaction History"},
    "transactions_description": {"Français": "Voici la liste de toutes les opérations enregistrées.", "Anglais": "Here is the list of all recorded operations."},

    # Sir Business Page
    "business_title": {"Français": "Sir Business", "Anglais": "Sir Business"},
    "choose_section": {"Français": "Choisissez une section", "Anglais": "Choose a section"},
    "home": {"Français": "Accueil", "Anglais": "Home"},
    "invoicing": {"Français": "Facturation", "Anglais": "Invoicing"},
    "op_expenses": {"Français": "Dépenses de fonctionnement", "Anglais": "Operating Expenses"},
    "salaries": {"Français": "Salaires", "Anglais": "Salaries"},
    "planning": {"Français": "Planification", "Anglais": "Planning"},
    "welcome_business": {"Français": "Bienvenue dans Sir Business", "Anglais": "Welcome to Sir Business"},
    "welcome_business_desc": {"Français": "Veuillez choisir une section dans le menu déroulant ci-dessus.", "Anglais": "Please choose a section from the dropdown menu above."},

    # Settings Page
    "settings_title": {"Français": "Paramètres", "Anglais": "Settings"},
    "settings_general": {"Français": "Préférences Générales", "Anglais": "General Preferences"},
    "settings_language": {"Français": "Langue", "Anglais": "Language"},
    "settings_language_changed": {"Français": "Langue changée en", "Anglais": "Language changed to"},
    "settings_currency": {"Français": "Devise", "Anglais": "Currency"},
    "settings_currency_changed": {"Français": "Devise changée en", "Anglais": "Currency changed to"},
    "settings_invoice_info": {"Français": "Informations de Facturation", "Anglais": "Invoice Information"},
    "settings_invoice_desc": {"Français": "Ces informations apparaîtront sur vos factures PDF.", "Anglais": "This information will appear on your PDF invoices."},
    "settings_upload_logo": {"Français": "Télécharger votre logo (laisser vide pour ne pas changer)", "Anglais": "Upload your logo (leave empty to keep current)"},
    "settings_upload_signature": {"Français": "Télécharger votre signature (laisser vide pour ne pas changer)", "Anglais": "Upload your signature (leave empty to keep current)"},
    "settings_company_name": {"Français": "Nom de votre entreprise", "Anglais": "Your company's name"},
    "settings_address": {"Français": "Adresse", "Anglais": "Address"},
    "settings_contact": {"Français": "Contact (Téléphone / Email)", "Anglais": "Contact (Phone / Email)"},
    "settings_vat_rate": {"Français": "Taux de TVA (%)", "Anglais": "VAT Rate (%)"},
    "settings_save_info": {"Français": "Enregistrer les informations", "Anglais": "Save Information"},
    "settings_info_updated": {"Français": "Informations de facturation mises à jour.", "Anglais": "Invoice information updated."},
    "settings_current_logo": {"Français": "Logo actuel :", "Anglais": "Current logo:"},
    "settings_current_signature": {"Français": "Signature actuelle :", "Anglais": "Current signature:"},
    
    # AI Prompts
    "ai_persona": {
        "Français": "Tu es Sir Comptable, un majordome financier sarcastique et très compétent. Ta mission est de répondre à la question de l'utilisateur en français en te basant STRICTEMENT sur les faits du contexte financier fourni. N'invente jamais de données.",
        "Anglais": "You are Sir Comptable, a sarcastic and highly competent financial butler. Your mission is to answer the user's question in English, relying STRICTLY on the facts from the provided financial context. Never invent data."
    },
    "ai_context_label": {"Français": "Contexte", "Anglais": "Context"},
    "ai_question_label": {"Français": "Question de l'utilisateur", "Anglais": "User's question"}
}

def _(key):
    lang = st.session_state.get("language", "Français")
    return TEXTS.get(key, {}).get(lang, f"[{key}]")
def safe_encode(text):
    if not text:
        return ""
    try:
        return str(text).encode("latin-1", "replace").decode("latin-1")
    except Exception:
        return str(text)
# --- CONNEXION SUPABASE ET NOUVELLES FONCTIONS UTILISATEURS ---
@st.cache_resource
def init_supabase_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase: Client = init_supabase_connection()

# --- Initialisation de la mémoire ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "page" not in st.session_state: st.session_state.page = "Tableau de Bord"
if "currency" not in st.session_state: st.session_state.currency = "FCFA"
if "language" not in st.session_state: st.session_state.language = "Français"
if "sarcasm_mode" not in st.session_state: st.session_state.sarcasm_mode = True
if "transactions" not in st.session_state: st.session_state.transactions = pd.DataFrame(columns=["Date", "Type", "Montant", "Catégorie", "Description"])
if "comptes" not in st.session_state: st.session_state.comptes = pd.DataFrame(columns=["Nom du Compte", "Solde Actuel", "Type"])
if "factures" not in st.session_state: st.session_state.factures = []
if 'invoice_items' not in st.session_state: st.session_state.invoice_items = [{"description": "", "montant": 0.0}]
if 'salaries' not in st.session_state: st.session_state.salaries = pd.DataFrame(columns=["Nom de l'employé", "Poste", "Salaire Brut"])
if 'company_logo' not in st.session_state: st.session_state.company_logo = None
if 'company_name' not in st.session_state: st.session_state.company_name = ""
if 'company_address' not in st.session_state: st.session_state.company_address = ""
if 'company_contact' not in st.session_state: st.session_state.company_contact = ""
if 'company_signature' not in st.session_state: st.session_state.company_signature = None
if 'company_vat_rate' not in st.session_state: st.session_state.company_vat_rate = 0.0
# ... (après les autres initialisations)
if 'bp_step' not in st.session_state:
    st.session_state.bp_step = 0
if 'bp_data' not in st.session_state:
    st.session_state.bp_data = {}
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Nom du Produit", "Description", "Quantité", "Prix d'Achat", "Prix de Vente"])

# --- Configuration de la page ---
st.set_page_config(page_title=_("app_title"), page_icon="📊", layout="wide")

# --- Thème Visuel ---
st.markdown("""
<style>
    .stApp { background-color: #F0EAD6; }
    body, .st-emotion-cache-1jicfl2, .st-emotion-cache-98r73h, .st-emotion-cache-1629p8f span, .st-emotion-cache-16txtl3, div[data-baseweb="select"] > div { color: #3D405B; }
    h1, h2, h3 { color: #3D405B; }
    .stSidebar { background-color: #FFFFFF; }
    .stButton>button { border: 2px solid #3D405B; background-color: #FFFFFF; color: #3D405B; border-radius: 50px; font-weight: bold; margin-bottom: 10px; }
    .stButton>button:hover { border: 2px solid #81B29A; background-color: #81B29A; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# --- Fonctions Utilitaires ---
@st.cache_data
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rapport')
    return output.getvalue()

def add_transaction(transaction_date, trans_type, amount, category, description):
    # Prépare les données pour la base de données
    new_transaction_data = {
        "date": str(transaction_date),
        "type": trans_type,
        "montant": amount,
        "category": category,
        "description": description
    }
    
    # Envoie à Supabase
    user_id = st.session_state.user.id
    success = add_transaction_to_db(user_id, new_transaction_data)

    # Met à jour l'affichage local si la sauvegarde a réussi
    if success:
        # --- LA CORRECTION EST ICI ---
        # On s'assure que la nouvelle date a bien un fuseau horaire (UTC)
        # pour correspondre aux données chargées depuis la BDD.
        aware_date = pd.to_datetime(transaction_date).tz_localize('UTC')
        
        new_row_df = pd.DataFrame([{
            "Date": aware_date, # On utilise la nouvelle date "aware"
            "Type": trans_type, 
            "Montant": amount, 
            "Catégorie": category, 
            "Description": description
        }])
        st.session_state.transactions = pd.concat([st.session_state.transactions, new_row_df], ignore_index=True)
        return True
    
    return False

# --- UPDATED LOGIN/SIGNUP PAGE ---
if not st.session_state.get("logged_in"):
    st.title("Sir Comptable")
    choice = st.selectbox("Navigation", ["Login", "Sign Up"])

    if choice == "Login":
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                response = login(email, password)
                if response.user:
                    st.session_state.logged_in = True
                    st.session_state.user = response.user
                    st.rerun()
                else:
                    st.error("Invalid login credentials.")
    
    elif choice == "Sign Up":
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                response = signup(email, password)
                # LE CODE CORRIGÉ
                if response.get("success"):
                    st.success("Signup successful! Please check your email to confirm your account.")
                else:
                    # On peut même afficher l'erreur précise renvoyée par la fonction
                    error_message = response.get("error", "Could not sign up. The user may already exist or the password may be too weak.")
                    st.error(error_message)
else:
    # On ajoute une vérification pour ne charger les données qu'une seule fois
    if 'data_loaded' not in st.session_state:
        load_user_data(st.session_state.user.id)
        st.session_state.data_loaded = True
    # --- LOGIQUE DE LA BARRE LATÉRALE MISE À JOUR ---
    with st.sidebar:
        st.write(f"Connecté en tant que : {st.session_state.user.email}")

        if st.button("Déconnexion"):
            supabase.auth.sign_out()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

        st.markdown("---")
        try:
            logo_image = Image.open("logo sir comptable.jpg")
            st.image(logo_image, width=180)
        except FileNotFoundError:
            st.error(_("logo_file_missing"))

        st.title("Sir Comptable")
        st.markdown("---")

        # --- Récupération du profil utilisateur ---
        user_id = st.session_state.user.id
        profile = get_user_profile(user_id) if "user" in st.session_state and st.session_state.user else None

        # --- Vérification des accès ---
        user_email = (st.session_state.user.email or "").lower()
        is_admin = (
            (profile and str(profile.get("role", "")).lower() == "admin")
            or user_email == "fmouhamadou13@gmail.com"
        )

        is_premium = (
            (profile and str(profile.get("subscription_status", "")).lower() == "premium")
            or is_admin  # les admins sont toujours premium
        )

        # --- Logique de navigation principale ---
        if st.button(_("sidebar_dashboard"), use_container_width=True):
            st.session_state.page = "Tableau de Bord"

        if st.button(_("sidebar_accounts"), use_container_width=True):
            st.session_state.page = "Mes Comptes"

        if st.button(_("sidebar_transactions"), use_container_width=True):
            st.session_state.page = "Transactions"

        # --- Section Sir Business ---
        if st.button(_("sidebar_business"), use_container_width=True):
            if is_admin or is_premium:
                st.session_state.page = "Sir Business"
            else:
                st.warning("🚫 Cette section est réservée aux abonnés Premium.")
                st.session_state.page = "Abonnement"

        # --- Section Rapports ---
        if st.button(_("sidebar_reports"), use_container_width=True):
            if is_admin or is_premium:
                st.session_state.page = "Rapports"
            else:
                st.warning("🚫 Cette section est réservée aux abonnés Premium.")
                st.session_state.page = "Abonnement"

        st.markdown("---")

        if st.button(_("sidebar_subscribe"), use_container_width=True):
            st.session_state.page = "Abonnement"

        if st.button(_("sidebar_settings"), use_container_width=True):
            st.session_state.page = "Paramètres"

        # --- Section Admin réservée ---
        if is_admin:
            st.markdown("---")
            st.subheader("⚙️ Administration")
            if st.button("Panneau Admin", use_container_width=True):
                st.session_state.page = "Admin Panel"
   
    # --- PAGE TABLEAU DE BORD (VERSION CORRIGÉE POUR LA FACTURATION) ---
    if st.session_state.page == "Tableau de Bord":
        st.title(_("dashboard_title"))
    
        col_toggle, col_button = st.columns([4, 1])
        with col_toggle:
            st.session_state.sarcasm_mode = st.toggle(_("sarcasm_mode"), value=st.session_state.sarcasm_mode)
    
        # Le bouton de rafraîchissement est maintenant le seul déclencheur de l'IA
        with col_button:
            refresh_comments = st.button("Rafraîchir 💬")

        st.markdown("---")

        if not st.session_state.transactions.empty:
            st.session_state.transactions['Montant'] = pd.to_numeric(st.session_state.transactions['Montant'], errors='coerce').fillna(0)

        total_revenus = st.session_state.transactions[st.session_state.transactions['Type'] == 'Revenu']['Montant'].sum()
        total_depenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Dépense']['Montant'].sum()
        solde_net = total_revenus - total_depenses

        # La logique de l'IA n'est exécutée que si l'on clique sur le bouton
        if refresh_comments and st.session_state.sarcasm_mode:
            with st.spinner(_("thinking")):
                try:
                    API_URL = st.secrets["HF_API_URL"]
                    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

                    def query_ai_comment(prompt_text):
                        formatted_prompt = f"<s>[INST] {prompt_text} [/INST]"
                        response = requests.post(API_URL, headers=headers, json={"inputs": formatted_prompt, "parameters": {"max_new_tokens": 50, "return_full_text": False, "do_sample": True, "temperature": 0.7}})
                        output = response.json()
                        if isinstance(output, list) and 'generated_text' in output[0]:
                            return output[0]['generated_text'].strip()
                        return _("error_ai_unexpected")

                    lang = st.session_state.language
                    prompt_revenu = f"Tu es Sir Comptable, un majordome sarcastique. En une seule phrase très courte et percutante, commente un revenu total de {total_revenus:,.0f} {st.session_state.currency}. Réponds en {lang}."
                    st.session_state.revenue_comment = query_ai_comment(prompt_revenu)
                
                    prompt_solde = f"Tu es Sir Comptable, un majordome sarcastique. En une seule phrase très courte et percutante, commente un solde net de {solde_net:,.0f} {st.session_state.currency}. Réponds en {lang}."
                    st.session_state.balance_comment = query_ai_comment(prompt_solde)
                    st.rerun()
                except Exception as e:
                    st.error(f"{_('error_critical')}: {e}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(_("revenues"), f"{total_revenus:,.0f} {st.session_state.currency}")
            if st.session_state.sarcasm_mode:
                st.caption(f"*{st.session_state.get('revenue_comment', '...')}*")
        with col2:
            st.metric(_("expenses"), f"{total_depenses:,.0f} {st.session_state.currency}")
        with col3:
            st.metric(_("net_balance"), f"{solde_net:,.0f} {st.session_state.currency}")
            if st.session_state.sarcasm_mode:
                st.caption(f"*{st.session_state.get('balance_comment', '...')}*")

        st.markdown("---")
    
        col_graphs1, col_graphs2 = st.columns(2)
        with col_graphs1:
            st.subheader(_("monthly_evolution"))
            if not st.session_state.transactions.empty:
                df_copy = st.session_state.transactions.copy()
        
                df_copy['Date'] = pd.to_datetime(df_copy['Date'], utc=True)
                df_copy['Mois'] = df_copy['Date'].dt.to_period('M')
        
                monthly_summary = df_copy.groupby(['Mois', 'Type'])['Montant'].sum().unstack(fill_value=0).reset_index()
                monthly_summary['Mois'] = monthly_summary['Mois'].astype(str)
            
                monthly_summary = df_copy.groupby(['Mois', 'Type'])['Montant'].sum().unstack(fill_value=0).reset_index()
                monthly_summary['Mois'] = monthly_summary['Mois'].astype(str)
                monthly_summary.sort_values(by='Mois', inplace=True)
            
                if 'Revenu' not in monthly_summary.columns: monthly_summary['Revenu'] = 0
                if 'Dépense' not in monthly_summary.columns: monthly_summary['Dépense'] = 0

                fig_line = px.line(
                    monthly_summary,
                    x='Mois',
                    y=['Revenu', 'Dépense'],  # ✅ Noms exacts des colonnes
                    labels={'value': _('amount'), 'variable': _('type'), 'Mois': _('month')},
                    title=f"{_('revenues')} vs. {_('expenses')}"
                )
                st.plotly_chart(fig_line, use_container_width=True)

            else:
                st.info(_("no_data_for_graph"))
            
        with col_graphs2:
            st.subheader(_("expense_distribution"))
            df_depenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Dépense']
            if not df_depenses.empty:
                fig_pie = px.pie(df_depenses, names='Catégorie', values='Montant', title=_("expense_distribution"))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info(_("no_expense_to_show"))
            
        st.markdown("---")
        st.subheader(_("talk_to_sir_comptable"))
        prompt = st.text_input("ask_your_question", label_visibility="collapsed", placeholder=_("ask_your_question"))
    
        if st.button(_("send")):
            if prompt:
                st.write(f"**{_('you')} :** {prompt}")
                with st.spinner(_("thinking")):
                    try:
                        API_URL = st.secrets["HF_API_URL"]
                        headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
                    
                        transactions_df = st.session_state.transactions
                        depenses_df = transactions_df[transactions_df['Type'] == 'Dépense']
                        revenus = transactions_df[transactions_df['Type'] == 'Revenu']['Montant'].sum()
                        depenses = depenses_df['Montant'].sum()
                        solde = revenus - depenses
                    
                        recents_articles_str = "Aucune facture récente."
                        if st.session_state.factures:
                            recents_articles = []
                            for facture in st.session_state.factures[-5:]:
                                for item in facture['Articles']:
                                    recents_articles.append(f"- {item['description']} ({item['montant']:,.0f} {st.session_state.currency})")
                            recents_articles_str = "\n".join(recents_articles)

                        contexte_financier = (
                            f"Résumé financier : Solde net = {solde:,.0f} {st.session_state.currency}. "
                            f"Voici le détail des articles des dernières factures pour analyse :\n{recents_articles_str}"
                        )
                    
                        prompt_final = (
                            f"<s>[INST] {_('ai_persona')} "
                            f"{_('ai_context_label')} : {contexte_financier} "
                            f"{_('ai_question_label')} : '{prompt}' [/INST]"
                        )

                        def query(payload):
                            response = requests.post(API_URL, headers=headers, json=payload)
                            return response.json()

                        output = query({"inputs": prompt_final, "parameters": {"max_new_tokens": 512, "return_full_text": False, "do_sample": True, "top_p": 0.9, "temperature": 0.7}})
                    
                        if isinstance(output, list) and 'generated_text' in output[0]:
                            st.success(f"**Sir Comptable :** {output[0]['generated_text'].strip()}")
                        elif 'error' in output:
                            st.error(f"{_('error_ai_response')} : {output['error']}")
                        else:
                            st.warning(f"{_('error_ai_unexpected')} : {output}")

                    except KeyError:
                        st.error(_("error_hf_token_missing"))
                    except Exception as e:
                        st.error(f"{_('error_critical')} : {e}")
            else:
                st.warning(_("enter_a_question"))
    # --- PAGE MES COMPTES ---
    elif st.session_state.page == "Mes Comptes":
        st.title(_("accounts_title"))
        st.markdown(_("accounts_description"))
        st.subheader(_("accounts_list"))
    
        if not st.session_state.comptes.empty:
            excel_data = convert_df_to_excel(st.session_state.comptes)
            st.download_button(label=_("download_excel"), data=excel_data, file_name='mes_comptes.xlsx')
    
        st.dataframe(st.session_state.comptes, use_container_width=True)

        with st.expander(_("manage_accounts")):
            if not st.session_state.comptes.empty:
                account_options = [_("choose")] + list(st.session_state.comptes["Nom du Compte"])
                account_to_manage = st.selectbox(_("select_account"), options=account_options)
            
                if account_to_manage != _("choose"):
                    account_index = st.session_state.comptes[st.session_state.comptes["Nom du Compte"] == account_to_manage].index[0]
                
                    with st.form(f"edit_{account_index}"):
                        st.write(f"{_('edit')} : **{account_to_manage}**")
                        new_name = st.text_input(_("name"), value=account_to_manage)
                        new_balance = st.number_input(_("balance"), value=float(st.session_state.comptes.loc[account_index, "Solde Actuel"]))
                    
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button(_("modify_button")):
                                st.session_state.comptes.loc[account_index, "Nom du Compte"] = new_name
                                st.session_state.comptes.loc[account_index, "Solde Actuel"] = new_balance
                                st.success(_("account_updated"))
                                st.rerun()
                        with col2:
                            if st.form_submit_button(_("delete_button")):
                                st.session_state.comptes = st.session_state.comptes.drop(index=account_index).reset_index(drop=True)
                                st.warning(_("account_deleted"))
                                st.rerun()
                            
            with st.form("new_account_form", clear_on_submit=True):
                st.write(_("add_new_account"))
                nom_compte = st.text_input(_("account_name"))
                type_compte = st.selectbox(_("account_type"), ["Banque", "Mobile Money", "Espèces"])
                solde_initial = st.number_input(f"{_('initial_balance')} ({st.session_state.currency})", min_value=0.0)
            
                if st.form_submit_button(_("add_button")):
                    if nom_compte:
                        # 1. On appelle la fonction de db.py pour sauvegarder dans la base de données
                        user_id = st.session_state.user.id
                        st.warning(f"DEBUG (ID envoyé) : {user_id}")
                        success = add_account(user_id, nom_compte, solde_initial, type_compte)

                        if success:
                            # 2. Si la sauvegarde a réussi, on met à jour l'affichage et on ajoute la transaction initiale
                            new_account_df = pd.DataFrame([{"Nom du Compte": nom_compte, "Solde Actuel": solde_initial, "Type": type_compte}])
                            st.session_state.comptes = pd.concat([st.session_state.comptes, new_account_df], ignore_index=True)
            
                            add_transaction(date.today(), 'Revenu', solde_initial, 'Capital Initial', f"Création du compte '{nom_compte}'")
                            st.success(_("account_added"))
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout du compte à la base de données.")
                    else:
                        st.error("Le nom du compte ne peut pas être vide.")
    # --- PAGE TRANSACTIONS ---
    elif st.session_state.page == "Transactions":
        st.title(_("transactions_title"))
        st.markdown(_("transactions_description"))
        st.dataframe(st.session_state.transactions, use_container_width=True)
    # --- PAGE SIR BUSINESS ---
    elif st.session_state.page == "Sir Business":
        st.title(_("business_title"))
        sub_page_options = [_("home"), _("invoicing"), "Gestion de Stock", _("op_expenses"), _("salaries"), _("planning")]
        sub_page = st.selectbox(_("choose_section"), sub_page_options)

        if sub_page == _("home"):
            st.header(_("welcome_business"))
            st.write(_("welcome_business_desc"))

        elif sub_page == _("invoicing"):
            st.subheader(_("invoicing"))
            with st.expander("Créer une nouvelle facture"):
                with st.form("new_invoice_form"):
                    type_facture = st.radio("Type de facture", ["Revenu", "Dépense"])
                    col1, col2 = st.columns(2)
                    with col1:
                        nom_client = st.text_input("Nom du Tiers (Client/Fournisseur)")
                        date_emission = st.date_input("Date d'émission", value=datetime.today())
                    with col2:
                        numero_facture = st.text_input("Numéro de Facture", value=f"FACT-{len(st.session_state.factures) + 1:03d}")
                
                    st.markdown("---")
                    st.subheader("Articles / Services")
                
                    # Boucle mise à jour pour les articles de la facture
                    for i, item in enumerate(st.session_state.invoice_items):
                        cols = st.columns([2, 2, 1, 1, 1])
                    
                        # Colonne 1: Sélection depuis le stock
                        product_list = ["--- Autre Produit/Service ---"] + list(st.session_state.stock["Nom du Produit"])
                        selected_product = cols[0].selectbox(f"Choisir du stock #{i+1}", product_list, key=f"stock_select_{i}")

                        is_custom_item = (selected_product == "--- Autre Produit/Service ---")
                    
                        if not is_custom_item and selected_product:
                            # Remplir automatiquement si un produit du stock est choisi
                            item_description = selected_product
                            default_price = float(st.session_state.stock[st.session_state.stock["Nom du Produit"] == selected_product]["Prix de Vente"].iloc[0])
                            is_disabled = True
                        else:
                            # Permettre la saisie manuelle
                            item_description = item.get("description", "")
                            default_price = item.get("prix_unitaire", 0.0)
                            is_disabled = False

                        # Colonne 2: Champ de description
                        item["description"] = cols[1].text_input(f"Description #{i+1}", value=item_description, key=f"desc_{i}", disabled=is_disabled)
                    
                        # Colonnes restantes
                        item["quantite"] = cols[2].number_input("Qté", min_value=1, step=1, value=item.get("quantite", 1), key=f"qty_{i}")
                        item["prix_unitaire"] = cols[3].number_input("Prix Unit.", min_value=0.0, value=default_price, format="%.2f", key=f"price_{i}")
                        item["total"] = item["quantite"] * item["prix_unitaire"]
                        cols[4].metric("Total", f"{item['total']:,.2f}")

                    soustotal_ht = sum(item['total'] for item in st.session_state.invoice_items)
                    vat_rate = st.session_state.get('company_vat_rate', 0.0)
                    vat_amount = soustotal_ht * (vat_rate / 100.0)
                    total_ttc = soustotal_ht + vat_amount
                
                    st.markdown("---")
                    st.metric("Sous-total HT", f"{soustotal_ht:,.2f} {st.session_state.currency}")
                    st.text(f"TVA ({vat_rate}%) : {vat_amount:,.2f} {st.session_state.currency}")
                    st.header(f"Total TTC : {total_ttc:,.2f} {st.session_state.currency}")
                
                    submit_col1, submit_col2 = st.columns(2)
                    with submit_col1:
                        if st.form_submit_button("Ajouter un article"):
                            st.session_state.invoice_items.append({"description": "", "quantite": 1, "prix_unitaire": 0.0, "total": 0.0}); st.rerun()
                    with submit_col2:
                        if st.form_submit_button("Enregistrer la facture"):
                            new_invoice_data = {
                                "Numéro": numero_facture, "Client": nom_client, 
                                "Date Émission": date_emission, "Statut": "Enregistrée", "Type": type_facture, 
                                "Articles": st.session_state.invoice_items.copy(),
                                "Sous-total": soustotal_ht, "TVA %": vat_rate,
                                "Montant TVA": vat_amount, "Montant": total_ttc
                            }
                            st.session_state.factures.append(new_invoice_data)
                            add_transaction(date_emission, type_facture, total_ttc, 'Facturation', f"Facture {numero_facture} pour {nom_client}")
                            if type_facture == 'Revenu':
                                for item in st.session_state.invoice_items:
                                    product_name = item.get("description")
                                    quantity_sold = item.get("quantite")
                                    if product_name and product_name in st.session_state.stock["Nom du Produit"].values:
                                        # Trouver l'index du produit dans le stock
                                        idx = st.session_state.stock[st.session_state.stock["Nom du Produit"] == product_name].index[0]
                                        # Réduire la quantité
                                        st.session_state.stock.loc[idx, "Quantité"] -= quantity_sold
                                st.success("Stock mis à jour.")
                            st.session_state.invoice_items = [{"description": "", "quantite": 1, "prix_unitaire": 0.0, "total": 0.0}]
                            st.success(f"Facture enregistrée."); st.rerun()
        
            st.subheader("Historique des Factures")
            if not st.session_state.factures:
                st.info("Aucune facture créée.")
            else:
                for facture in st.session_state.factures:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        col1.write(f"**Facture {facture['Numéro']}** - Client: {facture['Client']}")
                        col2.write(f"**Total TTC : {facture['Montant']:,.2f} {st.session_state.currency}**")
                    
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_auto_page_break(auto=True, margin=15)
                    
                        if st.session_state.company_logo:
                            try:
                                logo_bytes = io.BytesIO(st.session_state.company_logo)
                                pil_logo = Image.open(logo_bytes)
                                temp_logo_path = "temp_logo.png"
                                pil_logo.save(temp_logo_path)
                                pdf.image(temp_logo_path, x=10, y=8, w=33)
                            except Exception: pass
                    
                        current_y = pdf.get_y()
                        pdf.set_y(8)
                        pdf.set_x(110)
                        pdf.set_font("Helvetica", 'B', 12)
                        company_name_safe = safe_encode(st.session_state.company_name)
                        company_address_safe = safe_encode(st.session_state.company_address)
                        company_contact_safe = safe_encode(st.session_state.company_contact)
                        pdf.multi_cell(90, 7, f"{company_name_safe}\n{company_address_safe}\n{company_contact_safe}", 0, 'R')
                        pdf.set_y(current_y + 30)
                    
                        facture_num_safe = safe_encode(facture['Numéro'])
                        client_safe = safe_encode(facture['Client'])
                        date_emission_safe = safe_encode(facture['Date Émission'].strftime('%d/%m/%Y'))

                        pdf.set_font("Helvetica", 'B', 14)
                        pdf.cell(0, 10, text=f"Facture N {facture_num_safe}", border=0, ln=1, align='C')
                        pdf.ln(5)
                        pdf.set_font("Helvetica", '', 12)
                        pdf.cell(0, 8, text=f"Client: {client_safe}", ln=1)
                        pdf.cell(0, 8, text=f"Date: {date_emission_safe}", ln=1)
                        pdf.ln(10)
                    
                        pdf.set_font("Helvetica", 'B', 12)
                        pdf.cell(150, 10, "Description", 1, 0, 'C')
                        pdf.cell(40, 10, "Montant", 1, 1, 'C')
                        pdf.set_font("Helvetica", '', 12)
                    
                        for item in facture["Articles"]:
                            safe_description = safe_encode(item['description'])
                            montant = item.get("total", item.get("montant", 0.0))  # compatibilité
                            pdf.cell(150, 10, text=safe_description, border=1)
                            pdf.cell(40, 10, text=f"{montant:,.2f}", border=1, ln=1, align='R')

                        pdf.set_font("Helvetica", '', 12)
                        pdf.cell(150, 10, text="Sous-total HT", border=1, align='R')
                        pdf.cell(40, 10, text=f"{facture.get('Sous-total', 0):,.2f}", border=1, ln=1, align='R')
                        pdf.cell(150, 10, text=f"TVA ({facture.get('TVA %', 0)}%)", border=1, align='R')
                        pdf.cell(40, 10, text=f"{facture.get('Montant TVA', 0):,.2f}", border=1, ln=1, align='R')
                        pdf.set_font("Helvetica", 'B', 12)
                        pdf.cell(150, 10, text="TOTAL TTC", border=1, align='R')
                        pdf.cell(40, 10, text=f"{facture['Montant']:,.2f}", border=1, ln=1, align='R')
                    
                        if st.session_state.company_signature:
                            try:
                                sig_bytes = io.BytesIO(st.session_state.company_signature)
                                pil_sig = Image.open(sig_bytes)
                                temp_sig_path = "temp_signature.png"
                                pil_sig.save(temp_sig_path)
                                pdf.image(temp_sig_path, x=150, y=pdf.get_y() + 10, w=50)
                            except Exception: pass

                        pdf_output = bytes(pdf.output(dest='S'))
                        col3.download_button(label="📄 Télécharger en PDF", data=pdf_output, file_name=f"Facture_{facture['Numéro']}.pdf", mime="application/pdf")
                    
                        if os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
                        if os.path.exists("temp_signature.png"): os.remove("temp_signature.png")
                        pdf_output = bytes(pdf.output(dest='S'))
                        col3.download_button(label="📄 PDF", data=pdf_output, file_name=f"Facture_{facture['Numéro']}.pdf", mime="application/pdf")

        elif sub_page == "Gestion de Stock":
            st.subheader("Gestion de Stock")
            with st.expander("Ajouter un nouveau produit"):
                with st.form("new_product_form", clear_on_submit=True):
                    nom_produit = st.text_input("Nom du Produit")
                    description = st.text_area("Description")
                
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        quantite = st.number_input("Quantité en Stock", min_value=0, step=1)
                    with col2:
                        prix_achat = st.number_input("Prix d'Achat", min_value=0.0, format="%.2f")
                    with col3:
                        prix_vente = st.number_input("Prix de Vente", min_value=0.0, format="%.2f")

                    if st.form_submit_button("Ajouter le produit"):
                        new_product = pd.DataFrame([{
                            "Nom du Produit": nom_produit, 
                            "Description": description, 
                            "Quantité": quantite, 
                            "Prix d'Achat": prix_achat, 
                            "Prix de Vente": prix_vente
                        }])
                        st.session_state.stock = pd.concat([st.session_state.stock, new_product], ignore_index=True)
                        st.success(f"Produit '{nom_produit}' ajouté au stock.")

            st.markdown("---")
            st.subheader("Inventaire Actuel")
            st.dataframe(st.session_state.stock, use_container_width=True)
        elif sub_page == _("op_expenses"):
            st.subheader(_("op_expenses"))
            with st.form("operating_expenses_form", clear_on_submit=True):
                categorie = st.selectbox("Catégorie de dépense", ["Loyer", "Facture électricité", "Facture Eau", "Facture téléphone et connexion", "Réparation"])
                montant = st.number_input("Montant", min_value=0.0, format="%.2f")
                description = st.text_area("Description (obligatoire si 'Réparation')")
                if st.form_submit_button("Enregistrer la dépense"):
                    add_transaction(date.today(), 'Dépense', montant, categorie, description)
                    st.success(f"Dépense de '{categorie}' enregistrée.")

        elif sub_page == _("salaries"):
            st.subheader(_("salaries"))
            with st.expander("Ajouter un employé"):
                with st.form("new_employee_form", clear_on_submit=True):
                    nom_employe = st.text_input("Nom de l'employé")
                    poste_employe = st.text_input("Poste occupé")
                    salaire_brut = st.number_input(f"Salaire Brut Mensuel ({st.session_state.currency})", min_value=0.0)
                    if st.form_submit_button("Ajouter"):
                        user_id = st.session_state.user.id
                        # On sauvegarde dans la base de données
                        success = add_employee(user_id, nom_employe, poste_employe, salaire_brut)

                        if success:
                            # On met à jour l'affichage local
                            new_employee_df = pd.DataFrame([{"Nom de l'employé": nom_employe, "Poste": poste_employe, "Salaire Brut": salaire_brut}])
                            st.session_state.salaries = pd.concat([st.session_state.salaries, new_employee_df], ignore_index=True)
                            st.success(f"{nom_employe} a été ajouté.")
                            st.rerun()
                        # L'erreur est déjà gérée par la fonction dans db.py
        
            st.subheader("Liste des Salaires")
            if not st.session_state.salaries.empty:
                st.dataframe(st.session_state.salaries, use_container_width=True)
                total_salaires = st.session_state.salaries['Salaire Brut'].sum()
                st.metric("Masse Salariale Totale", f"{total_salaires:,.0f} {st.session_state.currency}")
                with st.form("pay_salaries_form"):
                    st.write("Ceci enregistrera la masse salariale totale comme une dépense.")
                    if st.form_submit_button("Payer les Salaires"):
                        add_transaction(date.today(), 'Dépense', total_salaires, 'Salaires', 'Paiement des salaires du mois')
                        st.success("Paiement des salaires enregistré comme dépense.")

        elif sub_page == _("planning"):
            st.subheader(_("planning"))
            st.markdown("Un entretien stratégique avec Sir Comptable pour construire votre business plan étape par étape.")

            # --- ÉTAPE 0 : IDÉE INITIALE ---
            if st.session_state.bp_step == 0:
                with st.form("bp_form_step0"):
                    st.write("**Étape 1 : Votre Idée**")
                    nom_projet = st.text_input("Nom du projet ou de l'entreprise")
                    description_projet = st.text_area("Description détaillée du projet (activité, cible, objectifs)")
                    budget_disponible = st.number_input(f"Budget de départ disponible ({st.session_state.currency})", min_value=0)
                
                    submitted = st.form_submit_button("Soumettre et passer à l'analyse du marché")

                    if submitted:
                        if not nom_projet or not description_projet:
                            st.error("Veuillez renseigner au moins le nom et la description.")
                        else:
                            st.session_state.bp_data['nom'] = nom_projet
                            st.session_state.bp_data['description'] = description_projet
                            st.session_state.bp_data['budget'] = budget_disponible
                            st.session_state.bp_step = 1
                            st.rerun()

            # --- ÉTAPE 1 : GÉNÉRATION DES QUESTIONS SUR LE MARCHÉ ---
            elif st.session_state.bp_step == 1:
                with st.spinner("Sir Comptable analyse votre idée et prépare ses questions..."):
                    try:
                        # On affiche un résumé de l'idée
                        st.info(f"**Projet :** {st.session_state.bp_data['nom']}\n\n**Description :** {st.session_state.bp_data['description']}")
                    
                        if 'market_questions' not in st.session_state.bp_data:
                            API_URL = st.secrets["HF_API_URL"]
                            headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
                        
                            prompt_questions = f"<s>[INST] Tu es un consultant en stratégie. Basé sur cette idée d'entreprise (Nom: {st.session_state.bp_data['nom']}, Description: {st.session_state.bp_data['description']}), pose exactement 3 questions courtes et numérotées pour analyser le marché (clientèle cible, concurrents, avantage unique). [/INST]"
                        
                            response = requests.post(API_URL, headers=headers, json={
                                "inputs": prompt_questions, 
                                "parameters": {
                                    "max_new_tokens": 200,
                                    "return_full_text": False, # L'instruction de discrétion
                                    "do_sample": True,
                                    "temperature": 0.7
                                }
                            }).json()
                            questions = response[0]['generated_text']
                            st.session_state.bp_data['market_questions'] = questions

                        st.markdown("---")
                        st.write("**Étape 2 : Analyse du Marché**")
                        st.write(st.session_state.bp_data['market_questions'])
                    
                        with st.form("bp_form_step1"):
                            market_answers = st.text_area("Vos réponses aux questions ci-dessus :", height=200)
                            submitted = st.form_submit_button("Soumettre et passer à la stratégie")
                            if submitted:
                                st.session_state.bp_data['market_answers'] = market_answers
                                st.session_state.bp_step = 2
                                st.rerun()

                    except Exception as e:
                        st.error(f"Une erreur est survenue : {e}")
                        if st.button("Recommencer"):
                            st.session_state.bp_step = 0
                            st.session_state.bp_data = {}
                            st.rerun()

            # --- ÉTAPE 2 : GÉNÉRATION DU BUSINESS PLAN FINAL ---
            elif st.session_state.bp_step == 2:
                with st.spinner("Sir Comptable compile toutes les informations et rédige le plan final..."):
                    try:
                        if 'final_plan' not in st.session_state.bp_data:
                            API_URL = st.secrets["HF_API_URL"]
                            headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

                            final_prompt = (
                                f"<s>[INST] Tu es Sir Comptable, un consultant expert. Rédige un business plan structuré et détaillé en te basant sur les informations suivantes. Adopte un ton professionnel et sarcastique. "
                                f"\n\n**IDÉE DE BASE :**\nNom: {st.session_state.bp_data['nom']}\nDescription: {st.session_state.bp_data['description']}\nBudget: {st.session_state.bp_data['budget']} {st.session_state.currency}"
                                f"\n\n**ANALYSE DU MARCHÉ (fournie par l'utilisateur) :**\n{st.session_state.bp_data['market_answers']}"
                                f"\n\n**STRUCTURE REQUISE :**\n"
                                f"1. **Résumé Exécutif**\n"
                                f"2. **Analyse du Marché** (basée sur les réponses de l'utilisateur)\n"
                                f"3. **Stratégie Marketing et Commerciale**\n"
                                f"4. **Prévisions Financières Simples**\n"
                                f"5. **Risques et Recommandations** (avec un ton sarcastique mais pertinent) [/INST]"
                            )
                        
                            response = requests.post(API_URL, headers=headers, json={
                                "inputs": final_prompt, 
                                "parameters": {
                                    "max_new_tokens": 1500,
                                    "return_full_text": False, # Pour la discrétion
                                    "do_sample": True,         # Pour la créativité
                                    "top_p": 0.9,
                                    "temperature": 0.7,
                                    "repetition_penalty": 1.15 # Pour éviter le bégaiement
                                }
                            }).json()
                            st.session_state.bp_data['final_plan'] = response[0]['generated_text']

                        st.markdown("---")
                        st.subheader("Proposition de Business Plan par Sir Comptable")
                        st.markdown(st.session_state.bp_data['final_plan'])
                    
                        if st.button("Créer un nouveau plan"):
                            st.session_state.bp_step = 0
                            st.session_state.bp_data = {}
                            st.rerun()

                    except Exception as e:
                        st.error(f"Une erreur est survenue : {e}")
                        if st.button("Recommencer"):
                            st.session_state.bp_step = 0
                            st.session_state.bp_data = {}
                            st.rerun()
    # --- PAGE RAPPORTS ---
    elif st.session_state.page == "Rapports":
        st.title("Rapports Financiers") # Title should be translated
        st.markdown("Analysez vos performances avec des rapports personnalisés.") # Desc should be translated

        st.subheader("Filtres") # Subheader should be translated
        col1, col2 = st.columns(2)
        with col1:
            type_donnees = st.selectbox("Type de données", ["Dépenses et Revenus", "Dépenses seulement", "Revenus seulement"])
        with col2:
            # This part needs to be made dynamic based on language
            period_options = ["Année en cours", "Semestre en cours", "Trimestre en cours", "Mois en cours"] + [date(2024, m, 1).strftime('%B') for m in range(1, 13)]
            periode = st.selectbox("Période", period_options)

        df_filtered = st.session_state.transactions.copy()
        if not df_filtered.empty:
            # On s'assure que la colonne Date est propre et en UTC.
            df_filtered['Date'] = pd.to_datetime(df_filtered['Date'], utc=True)
    
    today = datetime.utcnow().date() # On utilise une date naive pour les calculs simples
    start_date, end_date = None, today
    if periode == "Mois en cours": start_date = today.replace(day=1)
    elif periode == "Trimestre en cours":
                current_quarter = (today.month - 1) // 3 + 1
                start_month = (current_quarter - 1) * 3 + 1
                start_date = today.replace(month=start_month, day=1)
    elif periode == "Semestre en cours":
                start_month = 1 if today.month <= 6 else 7
                start_date = today.replace(month=start_month, day=1)
    elif periode == "Année en cours": start_date = today.replace(month=1, day=1)
    else:
                try:
                    month_number = [date(2000, m, 1).strftime('%B') for m in range(1, 13)].index(periode) + 1
                    df_filtered = df_filtered[df_filtered['Date'].dt.month == month_number]
                except ValueError: pass
        
            # LE NOUVEAU CODE
    if start_date:
                # On convertit les bornes en datetime pour la comparaison
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)

                    # Maintenant, on peut comparer deux dates qui "parlent la même langue"
        df_filtered = df_filtered[df_filtered['Date'].dt.date.between(start_date.date(), end_date.date())]
    
                except Exception as e:
                    st.error(f"Erreur lors du filtrage des dates : {e}")
        
    if type_donnees == "Dépenses seulement": df_filtered = df_filtered[df_filtered['Type'] == 'Dépense']
    elif type_donnees == "Revenus seulement": df_filtered = df_filtered[df_filtered['Type'] == 'Revenu']

        st.markdown("---")
        st.subheader(f"Résultats pour : {periode}") # Text should be translated
        if df_filtered.empty:
            st.warning("Aucune donnée à afficher pour la période sélectionnée.") # Text should be translated
        else:
            st.dataframe(df_filtered, use_container_width=True)
    # --- PAGE ABONNEMENT ---
    elif st.session_state.page == "Abonnement":
        st.title("Abonnement Premium")
        st.markdown("Passez à la version Premium pour débloquer toutes les fonctionnalités.")
        st.metric("Prix", f"10,000 {st.session_state.currency}/mois")

        st.markdown("---")
        st.subheader("Payer avec Wave")
    
        try:
            wave_link = st.secrets["WAVE_PAYMENT_LINK"]
            st.markdown(f'<a href="{wave_link}" target="_blank"><button>Payer 10,000 {st.session_state.currency} avec Wave</button></a>', unsafe_allow_html=True)
            st.info("Après avoir payé, le statut de votre compte sera mis à jour manuellement par l'administrateur.")
        except KeyError:
            st.warning("Le service de paiement Wave n'est pas encore configuré par l'administrateur.")
    # --- PAGE PARAMÈTRES ---
    elif st.session_state.page == "Paramètres":
        st.title(_("settings_title"))
        st.subheader(_("settings_general"))
    
        lang_options = ["Français", "Anglais"]
        langue_choisie = st.selectbox(
            _("settings_language"), 
            options=lang_options, 
            index=lang_options.index(st.session_state.language)
        )
        if langue_choisie != st.session_state.language:
            st.session_state.language = langue_choisie
            st.rerun()

        devises = ["FCFA", "EUR", "USD"]
        devise_actuelle_index = devises.index(st.session_state.currency)
        new_curr = st.selectbox(_("settings_currency"), devises, index=devise_actuelle_index)
        if new_curr != st.session_state.currency:
            st.session_state.currency = new_curr
            st.success(f"{_('settings_currency_changed')} {new_curr}.")
            st.rerun()
    
        st.markdown("---")
        st.subheader(_("settings_invoice_info"))
        st.markdown(_("settings_invoice_desc"))

        with st.form("invoice_info_form"):
            logo_file = st.file_uploader(_("settings_upload_logo"), type=['png', 'jpg', 'jpeg'])
            signature_file = st.file_uploader(_("settings_upload_signature"), type=['png', 'jpg', 'jpeg'])

            company_name = st.text_input(_("settings_company_name"), value=st.session_state.company_name)
            company_address = st.text_area(_("settings_address"), value=st.session_state.company_address)
            company_contact = st.text_input(_("settings_contact"), value=st.session_state.company_contact)
            company_vat_rate = st.number_input(_("settings_vat_rate"), value=float(st.session_state.company_vat_rate), min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
            
        
            submitted = st.form_submit_button(_("settings_save_info"))
            if submitted:
                if logo_file is not None:
                    st.session_state.company_logo = logo_file.getvalue()
                if signature_file is not None:
                    st.session_state.company_signature = signature_file.getvalue()
                st.session_state.company_name = company_name
                st.session_state.company_address = company_address
                st.session_state.company_contact = company_contact
                st.session_state.company_vat_rate = company_vat_rate
                st.success(_("settings_info_updated"))
    
        if st.session_state.company_logo:
            st.write(_("settings_current_logo"))
            st.image(st.session_state.company_logo, width=100)
        if st.session_state.company_signature:
            st.write(_("settings_current_signature"))
            st.image(st.session_state.company_signature, width=150)
        
    # --- PAGE ADMIN PANEL (VISIBLE UNIQUEMENT POUR TOI) ---
    if st.session_state.page == "Admin Panel":
        st.title("👑 Panneau d'administration")

        # Vérifie que seul ton email accède à cette page
        if st.session_state.user.email != "fmouhamadou13@gmail.com":
            st.error("⛔ Accès refusé. Vous n'êtes pas autorisé à consulter cette page.")
            st.stop()

        # Vérifie les abonnements expirés avant affichage
        expired_count = check_expired_subscriptions()
        if expired_count > 0:
            st.info(f"{expired_count} abonnement(s) premium expiré(s) ont été repassé(s) en 'free'.")

        users = get_all_users()

        if not users:
            st.warning("Aucun utilisateur trouvé.")
        else:
            st.subheader("Liste des utilisateurs")

            for user in users:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.write(f"**{user['email']}**")
                with col2:
                    new_role = st.selectbox(
                        "Rôle",
                        ["user", "admin"],
                        index=0 if user["role"] == "user" else 1,
                        key=f"role_{user['email']}"
                    )
                with col3:
                    new_status = st.selectbox(
                        "Abonnement",
                        ["free", "premium"],
                        index=0 if user["subscription_status"] == "free" else 1,
                        key=f"sub_{user['email']}"
                    )
                with col4:
                    if st.button("Mettre à jour", key=f"update_{user['email']}"):
                        try:
                            # Récupération du user_id
                            user_id_data = supabase.table("profiles").select("id").eq("email", user["email"]).execute()
                            if not user_id_data.data:
                                st.error("Utilisateur introuvable.")
                            else:
                                user_id = user_id_data.data[0]["id"]

                                # Mise à jour du rôle
                                update_user_role(user_id, new_role)

                                # Mise à jour du statut d'abonnement
                                update_user_subscription_status(user_id, new_status)

                                st.success(f"✅ Profil de {user['email']} mis à jour avec succès.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la mise à jour : {e}")

























