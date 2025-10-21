# --- IMPORTS ---
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, date
import io
import plotly.express as px
from fpdf import FPDF, XPos, YPos
import requests
import os
import base64
from supabase import create_client, Client
from db import (
    get_user_profile, check_expired_subscriptions, login, signup,
    get_all_users, update_user_role, update_user_subscription,
    get_transactions, add_transaction_to_db,
    get_accounts, add_account,
    get_employees, add_employee,
    get_invoices, add_invoice,
    get_stock, add_stock_item,
    update_stock_quantity,
    get_next_invoice_number,
    update_profile_settings,
    delete_stock_item,
    delete_invoice,
    delete_transaction_for_invoice,
    revert_to_free
)

# --- DÉFINITIONS DES FONCTIONS GLOBALES ---

def load_user_data(user_id):
    """Charge toutes les données brutes de l'utilisateur depuis la BDD."""
    st.session_state.transactions = pd.DataFrame(get_transactions(user_id) or [])
    st.session_state.comptes = pd.DataFrame(get_accounts(user_id) or [])
    st.session_state.salaries = pd.DataFrame(get_employees(user_id) or [])
    st.session_state.factures = get_invoices(user_id) or []
    st.session_state.stock = pd.DataFrame(get_stock(user_id) or [])
    
    profile = get_user_profile(user_id)
    if profile:
        st.session_state.company_name = profile.get('company_name', '')
        st.session_state.company_address = profile.get('company_address', '')
        st.session_state.company_contact = profile.get('company_contact', '')
        st.session_state.company_vat_rate = profile.get('company_vat_rate', 0.0)
        st.session_state.company_logo = profile.get('company_logo_url', None)
        st.session_state.company_signature = profile.get('company_signature_url', None)
        
def reset_invoice_form():
    """Vide et réinitialise les champs du formulaire de facturation."""
    keys_to_clear = [key for key in st.session_state if key.startswith("search_") or key.startswith("stock_select_") or key.startswith("desc_") or key.startswith("qty_") or key.startswith("price_")]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    if "invoice_client" in st.session_state:
        del st.session_state.invoice_client
    st.session_state.invoice_items = [{"quantite": 1, "prix_unitaire": 0.0}]

def log_out():
    """Déconnecte l'utilisateur et nettoie TOUTE la session."""
    supabase.auth.sign_out()
    keys_to_delete = list(st.session_state.keys())
    for key in keys_to_delete:
        del st.session_state[key]
    st.rerun()

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

@st.cache_resource
def init_supabase_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

@st.cache_data
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rapport')
    return output.getvalue()

def add_transaction(transaction_date, trans_type, amount, category, description):
    new_transaction_data = {
        "date": str(transaction_date), "type": trans_type,
        "amount": amount, "category": category, "description": description
    }
    success = add_transaction_to_db(st.session_state.user.id, new_transaction_data)
    if success:
        load_user_data(st.session_state.user.id) # Re-fetch all data to ensure consistency
        return True
    return False

# --- DICTIONNAIRE DE TRADUCTION COMPLET ---
TEXTS = {
    # General & Login/Signup
    "login": {"Français": "Connexion", "Anglais": "Login"},
    "signup": {"Français": "Inscription", "Anglais": "Sign Up"},
    "password": {"Français": "Mot de passe", "Anglais": "Password"},
    "email": {"Français": "Email", "Anglais": "Email"},
    "login_button": {"Français": "Se connecter", "Anglais": "Log In"},
    "signup_button": {"Français": "S'inscrire", "Anglais": "Sign Up"},
    "logout_button": {"Français": "Déconnexion", "Anglais": "Logout"},
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
    "revenues": {"Français": "Revenus", "Anglais": "Revenues"},
    "expenses": {"Français": "Dépenses", "Anglais": "Expenses"},
    "net_balance": {"Français": "Solde Net", "Anglais": "Net Balance"},
    "monthly_evolution": {"Français": "Évolution Mensuelle", "Anglais": "Monthly Evolution"},
    "no_data_for_graph": {"Français": "Aucune donnée pour afficher le graphique.", "Anglais": "No data to display for the chart."},
    "expense_distribution": {"Français": "Répartition des Dépenses", "Anglais": "Expense Distribution"},
    "no_expense_to_show": {"Français": "Aucune dépense à afficher.", "Anglais": "No expense to display."},
    
    # Accounts Page
    "accounts_title": {"Français": "Mes Comptes", "Anglais": "My Accounts"},
    "accounts_description": {"Français": "Gérez ici les différentes sources de vos finances.", "Anglais": "Manage your different financial sources here."},
    "accounts_list": {"Français": "Liste de vos comptes", "Anglais": "List of your accounts"},
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
    "planning": {"Français": "Planification", "Anglais": "Planning"},
    "salaries": {"Français": "Salaires", "Anglais": "Salaries"},
    
    # Settings Page
    "settings_title": {"Français": "Paramètres", "Anglais": "Settings"},
    "settings_general": {"Français": "Préférences Générales", "Anglais": "General Preferences"},
    "settings_language": {"Français": "Langue", "Anglais": "Language"},
    "settings_currency": {"Français": "Devise", "Anglais": "Currency"},
    "settings_invoice_info": {"Français": "Informations de Facturation", "Anglais": "Invoice Information"},
    "settings_invoice_desc": {"Français": "Ces informations apparaîtront sur vos factures PDF.", "Anglais": "This information will appear on your PDF invoices."},
    "settings_upload_logo": {"Français": "Télécharger votre logo", "Anglais": "Upload your logo"},
    "settings_upload_signature": {"Français": "Télécharger votre signature", "Anglais": "Upload your signature"},
    "settings_company_name": {"Français": "Nom de votre entreprise", "Anglais": "Your company's name"},
    "settings_address": {"Français": "Adresse", "Anglais": "Address"},
    "settings_contact": {"Français": "Contact (Téléphone / Email)", "Anglais": "Contact (Phone / Email)"},
    "settings_vat_rate": {"Français": "Taux de TVA (%)", "Anglais": "VAT Rate (%)"},
    "settings_save_info": {"Français": "Enregistrer les informations", "Anglais": "Save Information"},
    "settings_info_updated": {"Français": "Informations de facturation mises à jour.", "Anglais": "Invoice information updated."},
    "settings_current_logo": {"Français": "Logo actuel :", "Anglais": "Current logo:"},
    "settings_current_signature": {"Français": "Signature actuelle :", "Anglais": "Current signature:"},
}
# --- DÉMARRAGE DE L'APPLICATION ET GESTION DE LA SESSION ---

# 1. Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(page_title="Sir Comptable", page_icon="📊", layout="wide")

# 2. Initialisation de la connexion Supabase
supabase: Client = init_supabase_connection()
expired_count = check_expired_subscriptions()

# 3. Initialisation complète de la mémoire de la session (une seule fois)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.data_loaded = False
    st.session_state.page = "Tableau de Bord"
    st.session_state.currency = "FCFA"
    st.session_state.language = "Français"
    st.session_state.sarcasm_mode = True
    st.session_state.transactions = pd.DataFrame()
    st.session_state.comptes = pd.DataFrame()
    st.session_state.factures = []
    st.session_state.invoice_items = [{"quantite": 1, "prix_unitaire": 0.0}]
    st.session_state.salaries = pd.DataFrame()
    st.session_state.stock = pd.DataFrame()
    st.session_state.company_name = ""
    st.session_state.company_address = ""
    st.session_state.company_contact = ""
    st.session_state.company_vat_rate = 0.0
    st.session_state.company_logo = None
    st.session_state.company_signature = None

# 4. Tentative de restauration de session
if not st.session_state.get("logged_in"):
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.logged_in = True
            st.session_state.user = session.user
    except Exception:
        pass 

# 5. Chargement des données si nécessaire
if st.session_state.get("logged_in") and not st.session_state.get("data_loaded"):
    load_user_data(st.session_state.user.id)
    st.session_state.data_loaded = True
    if expired_count > 0:
        st.toast(f"🕓 {expired_count} abonnement(s) premium expiré(s) ont été réinitialisés.")

# --- Thème Visuel ---
st.markdown("""
<style>
    /* Thème Général SANS police personnalisée */
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3, .st-emotion-cache-16txtl3 { color: #343A40; }
    .stSidebar { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF; border: 1px solid #E0E0E0;
        border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        padding: 1rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"] { border: none !important; box-shadow: none !important; }
    .stButton>button {
        border-radius: 8px; border: 2px solid #FBCB0A; background-color: #FBCB0A;
        color: #343A40; font-weight: 600; transition: all 0.2s;
    }
    .stButton>button:hover { border: 2px solid #e2b708; background-color: #e2b708; color: #FFFFFF; }
    .stButton>button:active { background-color: #c9a307 !important; border-color: #c9a307 !important; }
    div[data-baseweb="input"], div[data-baseweb="select"] { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)
# --- ROUTEUR PRINCIPAL DE L'APPLICATION ---

if not st.session_state.get("logged_in"):
    # --- PAGE DE CONNEXION / INSCRIPTION ---
    st.title("Sir Comptable")
    choice = st.selectbox("Navigation", [_("login"), _("signup")])

    if choice == _("login"):
        with st.form("login_form"):
            email = st.text_input(_("email"))
            password = st.text_input(_("password"), type="password")
            submitted = st.form_submit_button(_("login_button"))
            if submitted:
                response = login(email, password)
                if response and response.user:
                    if 'data_loaded' in st.session_state:
                        del st.session_state['data_loaded']
                    st.session_state.logged_in = True
                    st.session_state.user = response.user
                    st.rerun()
                else:
                    st.error(_("invalid_credentials"))
    
    elif choice == _("signup"):
        with st.form("signup_form"):
            email = st.text_input(_("email"))
            password = st.text_input(_("password"), type="password")
            submitted = st.form_submit_button(_("signup_button"))
            if submitted:
                response = signup(email, password)
                if response.get("success"):
                    st.success(_("signup_success"))
                else:
                    error_message = response.get("error", _("signup_error"))
                    st.error(error_message)
else:
    with st.sidebar:
        if st.session_state.user:
            st.write(f"Connecté en tant que: {st.session_state.user.email}")

        if st.button(_("logout_button")):
            log_out()

        st.markdown("---")
        try:
            logo_image = Image.open("logo sir comptable.jpg")
            st.image(logo_image, width=180)
        except FileNotFoundError:
            st.error(_("logo_file_missing"))

        st.title("Sir Comptable")
        st.markdown("---")

        profile = get_user_profile(st.session_state.user.id) if st.session_state.user else None
        
        is_admin = (profile and str(profile.get("role", "")).lower() == "admin") or (st.session_state.user and st.session_state.user.email == "fmouhamadou13@gmail.com")
        is_premium = (profile and str(profile.get("subscription_status", "")).lower() == "premium") or is_admin

        if st.button(_("sidebar_dashboard"), use_container_width=True): st.session_state.page = "Tableau de Bord"
        if st.button(_("sidebar_accounts"), use_container_width=True): st.session_state.page = "Mes Comptes"
        if st.button(_("sidebar_transactions"), use_container_width=True): st.session_state.page = "Transactions"
        
        if st.button(_("sidebar_business"), use_container_width=True):
            if is_premium:
                st.session_state.page = "Sir Business"
            else:
                st.warning("🚫 Réservé aux abonnés Premium.")
                st.session_state.page = "Abonnement"
        
        if st.button(_("sidebar_reports"), use_container_width=True):
            if is_premium:
                st.session_state.page = "Rapports"
            else:
                st.warning("🚫 Réservé aux abonnés Premium.")
                st.session_state.page = "Abonnement"
        
        st.markdown("---")
        if st.button(_("sidebar_subscribe"), use_container_width=True): st.session_state.page = "Abonnement"
        if st.button(_("sidebar_settings"), use_container_width=True): st.session_state.page = "Paramètres"

        if is_admin:
            st.markdown("---")
            st.subheader("⚙️ Administration")
            if st.button("Panneau Admin", use_container_width=True):
                st.session_state.page = "Admin Panel"

# --- AFFICHAGE DES PAGES ---

    if st.session_state.page == "Tableau de Bord":
        st.title(_("dashboard_title"))
    
        col_toggle, col_button = st.columns([4, 1])
        with col_toggle:
            st.session_state.sarcasm_mode = st.toggle("Mode Sarcasme", value=st.session_state.sarcasm_mode)
        with col_button:
            refresh_comments = st.button("💬 Obtenir un commentaire")

        st.markdown("---")
        
        total_revenus, total_depenses, solde_net = 0, 0, 0
        if not st.session_state.transactions.empty and 'amount' in st.session_state.transactions.columns:
            st.session_state.transactions['amount'] = pd.to_numeric(st.session_state.transactions['amount'], errors='coerce').fillna(0)
            total_revenus = st.session_state.transactions[st.session_state.transactions['type'] == 'Revenu']['amount'].sum()
            total_depenses = st.session_state.transactions[st.session_state.transactions['type'] == 'Dépense']['amount'].sum()
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

        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            with col1: st.metric(_("revenues"), f"{total_revenus:,.0f} {st.session_state.currency}")
            with col2: st.metric(_("expenses"), f"{total_depenses:,.0f} {st.session_state.currency}")
            with col3: st.metric(_("net_balance"), f"{solde_net:,.0f} {st.session_state.currency}")

        st.markdown("---")
        
        col_graphs1, col_graphs2 = st.columns(2)
        with col_graphs1:
            st.subheader(_("monthly_evolution"))
            if not st.session_state.transactions.empty and 'date' in st.session_state.transactions.columns:
                df_copy = st.session_state.transactions.copy()
                df_copy['date'] = pd.to_datetime(df_copy['date'], utc=True)
                df_copy['Mois'] = df_copy['date'].dt.to_period('M')
                monthly_summary = df_copy.groupby(['Mois', 'type'])['amount'].sum().unstack(fill_value=0).reset_index()
                monthly_summary['Mois'] = monthly_summary['Mois'].astype(str)
                if 'Revenu' not in monthly_summary.columns: monthly_summary['Revenu'] = 0
                if 'Dépense' not in monthly_summary.columns: monthly_summary['Dépense'] = 0
                fig_line = px.line(monthly_summary, x='Mois', y=['Revenu', 'Dépense'], title=f"{_('revenues')} vs. {_('expenses')}")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info(_("no_data_for_graph"))
                
        with col_graphs2:
            st.subheader(_("expense_distribution"))
            if not st.session_state.transactions.empty and 'type' in st.session_state.transactions.columns:
                df_depenses = st.session_state.transactions[st.session_state.transactions['type'] == 'Dépense']
                if not df_depenses.empty:
                    fig_pie = px.pie(df_depenses, names='category', values='amount', title=_("expense_distribution"))
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info(_("no_expense_to_show"))
            else:
                st.info(_("no_expense_to_show"))
        # --- Section "Parler à Sir Comptable" ---
        st.subheader(_("talk_to_sir_comptable"))
        prompt = st.text_input("ask_your_question", label_visibility="collapsed", placeholder=_("ask_your_question"))
    
        if st.button("Envoyer"):
            if prompt:
                st.write(f"**{_('you')} :** {prompt}")
                with st.spinner(_("thinking")):
                    try:
                        API_URL = st.secrets["HF_API_URL"]
                        headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
                    
                        transactions_df = st.session_state.transactions
                        depenses_df = transactions_df[transactions_df['type'] == 'Dépense']
                        revenus = transactions_df[transactions_df['type'] == 'Revenu']['amount'].sum()
                        depenses = depenses_df['amount'].sum()
                        solde = revenus - depenses
                    
                        recents_articles_str = "Aucune facture récente."
                        if st.session_state.factures:
                            recents_articles = []
                            for facture in st.session_state.factures[-5:]:
                                for item in facture.get('Articles', []):
                                    description = item.get('description', 'N/A')
                                    montant = item.get('total', item.get('montant', 0))
                                    recents_articles.append(f"- {description} ({montant:,.0f} {st.session_state.currency})")
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

                    except KeyError as e:
                        if 'HF_TOKEN' in str(e) or 'HF_API_URL' in str(e):
                            st.error(_("error_hf_token_missing"))
                        else:
                            st.error(f"Erreur de structure dans vos données (probable facture) : Clé manquante -> {e}")
                            
                    except Exception as e:
                        st.error(f"Une erreur critique est survenue : {e}")
            else:
                st.warning(_("enter_a_question"))
 

    elif st.session_state.page == "Mes Comptes":
        st.title(_("accounts_title"))
        st.markdown(_("accounts_description"))
        
        st.subheader(_("accounts_list"))
        if not st.session_state.comptes.empty:
            display_comptes = st.session_state.comptes.rename(columns={'name': 'Nom du Compte', 'balance': 'Solde Actuel', 'type': 'Type'})
            st.dataframe(display_comptes[['Nom du Compte', 'Solde Actuel', 'Type']], use_container_width=True)
        else:
            st.info("Aucun compte n'a été ajouté.")
        
        with st.expander("Ajouter un nouveau compte"):
            with st.form("new_account_form", clear_on_submit=True):
                nom_compte = st.text_input(_("account_name"))
                type_compte = st.selectbox(_("account_type"), ["Banque", "Mobile Money", "Espèces"])
                solde_initial = st.number_input(f"{_('initial_balance')} ({st.session_state.currency})", min_value=0.0)
                if st.form_submit_button(_("add_button")):
                    if nom_compte:
                        if add_account(st.session_state.user.id, nom_compte, solde_initial, type_compte):
                            if add_transaction(date.today(), 'Revenu', solde_initial, 'Capital Initial', f"Création du compte '{nom_compte}'"):
                                st.success(_("account_added"))
                                st.rerun()
                    else:
                        st.error("Le nom du compte ne peut pas être vide.")

    elif st.session_state.page == "Transactions":
        st.title(_("transactions_title"))
        st.markdown(_("transactions_description"))
        if not st.session_state.transactions.empty:
            display_trans = st.session_state.transactions.rename(columns={'date':'Date', 'type':'Type', 'amount':'Montant', 'category':'Catégorie', 'description':'Description'})
            st.dataframe(display_trans[['Date','Type','Montant','Catégorie','Description']], use_container_width=True)
        else:
            st.info("Aucune transaction.")
    elif st.session_state.page == "Sir Business":
        st.title(_("business_title"))
        sub_page_options = [_("home"), _("invoicing"), "Gestion de Stock", _("op_expenses"), _("salaries"), _("planning")]
        sub_page = st.selectbox(_("choose_section"), sub_page_options)

        if sub_page == _("home"):
            st.header(_("welcome_business"))
            st.write(_("welcome_business_desc"))

        # --- Sous-page Facturation ---
        elif sub_page == _("invoicing"):
            st.subheader(_("invoicing"))
            with st.expander("Créer une nouvelle facture", expanded=True):
                type_facture = st.radio("Type de facture", ["Revenu", "Dépense"], key="invoice_type")
                c1, c2 = st.columns(2)
                with c1: nom_client = st.text_input("Nom du Tiers (Client/Fournisseur)", key="invoice_client")
                with c2: date_emission = st.date_input("Date d'émission", value=datetime.today())
                next_num = get_next_invoice_number(st.session_state.user.id)
                numero_facture = st.text_input("Numéro de Facture", value=f"FACT-{next_num:03d}")
                st.markdown("---"); st.subheader("Articles / Services")

                soustotal_ht = 0
                for i, item in enumerate(st.session_state.invoice_items):
                    cols = st.columns([3, 3, 1, 2, 1])
                    with cols[0]:
                        search_term = st.text_input(f"Rechercher un produit", key=f"search_{i}", label_visibility="collapsed", placeholder=f"Rechercher un produit #{i+1}")
                        if search_term:
                            filtered_products = st.session_state.stock[st.session_state.stock["product_name"].str.contains(search_term, case=False, na=False)]["product_name"].tolist()
                        else:
                            filtered_products = st.session_state.stock["product_name"].tolist()
                        product_list = ["--- Autre Produit/Service ---"] + filtered_products
                        selected_product = st.selectbox("Choisir du stock", product_list, key=f"stock_select_{i}", label_visibility="collapsed")
                    
                    is_custom = selected_product == "--- Autre Produit/Service ---"
                    description_value = selected_product if not is_custom else ""
                    
                    with cols[1]: item_description = st.text_input("Description", value=description_value, key=f"desc_{i}", label_visibility="collapsed", placeholder=f"Description #{i+1}", disabled=(not is_custom))
                    with cols[2]: item_quantity = st.number_input("Qté", min_value=1, step=1, value=item.get("quantite", 1), key=f"qty_{i}", label_visibility="collapsed")
                    with cols[3]:
                        suggested_price = 0.0
                        if not is_custom and selected_product:
                            match = st.session_state.stock[st.session_state.stock["product_name"] == selected_product]
                            if not match.empty: suggested_price = match["sale_price"].iloc[0]
                        item_price = st.number_input("Prix Unit.", min_value=0.0, value=float(suggested_price), format="%.2f", key=f"price_{i}", label_visibility="collapsed")
                        if suggested_price > 0: st.caption(f"Suggéré : {suggested_price:,.0f}")
                    with cols[4]:
                        item_total = item_quantity * item_price
                        soustotal_ht += item_total
                        st.metric("Total", f"{item_total:,.0f}")
                
                vat_rate = st.session_state.get('company_vat_rate', 0.0)
                vat_amount = soustotal_ht * (vat_rate / 100.0)
                total_ttc = soustotal_ht + vat_amount
                st.markdown("---")
                st.header(f"Total TTC : {total_ttc:,.2f} {st.session_state.currency}")

                c_btn1, c_btn2, _ = st.columns([2,3,5])
                if c_btn1.button("➕ Ajouter un article"):
                    st.session_state.invoice_items.append({"quantite": 1, "prix_unitaire": 0.0}); st.rerun()
                if c_btn2.button("✅ Enregistrer la facture"):
                    final_invoice_items = []
                    current_soustotal_ht = 0
                    for i in range(len(st.session_state.invoice_items)):
                        selected_prod = st.session_state[f"stock_select_{i}"]
                        description = selected_prod if selected_prod != "--- Autre Produit/Service ---" else st.session_state[f"desc_{i}"]
                        qty = st.session_state[f"qty_{i}"]
                        price = st.session_state[f"price_{i}"]
                        item_total = qty * price
                        current_soustotal_ht += item_total
                        final_invoice_items.append({
                            "nom_produit": selected_prod, "description": description,
                            "quantite": qty, "prix_unitaire": price, "total": item_total
                        })
                    
                    final_vat_amount = current_soustotal_ht * (vat_rate / 100.0)
                    final_total_ttc = current_soustotal_ht + final_vat_amount

                    invoice_data_to_save = {
                        "user_id": st.session_state.user.id, "number": numero_facture, "client": nom_client,
                        "issue_date": str(date_emission), "status": "Brouillon", "total_ht": current_soustotal_ht,
                        "tva": final_vat_amount, "total_ttc": final_total_ttc, "articles": final_invoice_items
                    }
                    
                    if add_invoice(invoice_data_to_save):
                        add_transaction(date_emission, type_facture, final_total_ttc, 'Facturation', f"Facture {numero_facture} pour {nom_client}")
                        if type_facture == 'Revenu':
                            for item in final_invoice_items:
                                product_name = item.get("nom_produit")
                                quantity_sold = item.get("quantite", 0)
                                if product_name and product_name != "--- Autre Produit/Service ---":
                                    update_success, message = update_stock_quantity(st.session_state.user.id, product_name, -quantity_sold)
                                    if update_success:
                                        # On met à jour l'affichage local du stock
                                        product_index = st.session_state.stock[st.session_state.stock['product_name'] == product_name].index
                                        if not product_index.empty:
                                            st.session_state.stock.loc[product_index, 'quantity'] -= quantity_sold
                                        st.toast(message, icon="✅") # Petite notification de succès
                                    else:
                                        st.warning(message) # Avertissement visible si ça échoue
                        reset_invoice_form()
                        st.success(f"Facture {numero_facture} enregistrée.")
                        st.rerun()

            st.subheader("Historique des Factures")
            if not st.session_state.factures:
                st.info("Aucune facture créée.")
            else:
                for facture in st.session_state.factures:
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
                    with col1:
                        st.write(f"**Facture {facture.get('number')}** - Client: {facture.get('client')}")
                    with col2:
                        st.write(f"**Total TTC : {facture.get('total_ttc', 0):,.2f} {st.session_state.currency}**")
            
                    # --- TOUTE LA LOGIQUE PDF VA DANS CETTE COLONNE ---
                    with col3:
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_auto_page_break(auto=True, margin=15)
            
                        if st.session_state.get('company_logo'):
                            try:
                                logo_base64_data = st.session_state.company_logo.split(',')[1]
                                logo_bytes = base64.b64decode(logo_base64_data)
                                logo_img_file = io.BytesIO(logo_bytes)
                                pil_logo = Image.open(logo_img_file)
                                temp_logo_path = "temp_logo.png"
                                pil_logo.save(temp_logo_path)
                                pdf.image(temp_logo_path, x=10, y=8, w=33)
                            except Exception as e:
                                print(f"Erreur image logo PDF: {e}")

                        current_y = pdf.get_y()
                        pdf.set_y(8)
                        pdf.set_x(110)
                        pdf.set_font("Helvetica", 'B', 12)
                        company_name_safe = safe_encode(st.session_state.company_name)
                        company_address_safe = safe_encode(st.session_state.company_address)
                        company_contact_safe = safe_encode(st.session_state.company_contact)
                        pdf.multi_cell(90, 7, f"{company_name_safe}\n{company_address_safe}\n{company_contact_safe}", 0, 'R')
                        pdf.set_y(current_y + 30)

                        facture_num_safe = safe_encode(facture.get('number'))
                        client_safe = safe_encode(facture.get('client'))
                        date_emission_safe = "" # On définit une valeur par défaut (chaîne vide)
                        issue_date_val = facture.get('issue_date')

                        # On ne formate la date que si elle n'est pas vide
                        if pd.notna(issue_date_val):
                            date_obj = pd.to_datetime(issue_date_val)
                            date_emission_safe = safe_encode(date_obj.strftime('%d/%m/%Y'))

                        pdf.set_font("Helvetica", 'B', 14)
                        pdf.cell(0, 10, text=f"Facture N {facture_num_safe}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                        pdf.ln(5)
                        pdf.set_font("Helvetica", '', 12)
                        pdf.cell(0, 8, text=f"Client: {client_safe}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        pdf.cell(0, 8, text=f"Date: {date_emission_safe}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        pdf.ln(10)

                        pdf.set_font("Helvetica", 'B', 12)
                        pdf.cell(150, 10, "Description", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
                        pdf.cell(40, 10, "Montant", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                        pdf.set_font("Helvetica", '', 12)

                        articles_list = facture.get("articles", [])
                        if isinstance(articles_list, list):
                            for item in articles_list:
                                safe_description = safe_encode(item.get('description'))
                                montant = item.get("total", item.get("montant", 0.0))
                                pdf.cell(150, 10, text=safe_description, border=1)
                                pdf.cell(40, 10, text=f"{montant:,.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

                        pdf.set_font("Helvetica", '', 12)
                        pdf.cell(150, 10, text="Sous-total HT", border=1, align='R')
                        pdf.cell(40, 10, text=f"{facture.get('total_ht', 0):,.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
                        pdf.cell(150, 10, text=f"TVA ({facture.get('tva', 0)}%)", border=1, align='R') # Assurez-vous que les noms de clés sont bons
                        pdf.cell(40, 10, text=f"{facture.get('tva', 0):,.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
                        pdf.set_font("Helvetica", 'B', 12)
                        pdf.cell(150, 10, text="TOTAL TTC", border=1, align='R')
                        pdf.cell(40, 10, text=f"{facture.get('total_ttc', 0):,.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            
                        if st.session_state.get('company_signature'):
                            try:
                                sig_base64_data = st.session_state.company_signature.split(',')[1]
                                sig_bytes = base64.b64decode(sig_base64_data)
                                sig_img_file = io.BytesIO(sig_bytes)
                                pil_sig = Image.open(sig_img_file)
                                temp_sig_path = "temp_signature.png"
                                pil_sig.save(temp_sig_path)
                                pdf.image(temp_sig_path, x=150, y=pdf.get_y() + 10, w=50)
                            except Exception as e:
                                print(f"Erreur image signature PDF: {e}")

                        pdf_output = pdf.output()
                        st.download_button(
                            label="📄",
                            data=bytes(pdf_output),
                            file_name=f"Facture_{facture.get('number')}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{facture.get('id')}"
                        )
                
                        if os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
                        if os.path.exists("temp_signature.png"): os.remove("temp_signature.png")

                    # --- La colonne pour le bouton Supprimer ---
                    with col4:
                        if st.button("🗑️", key=f"del_invoice_{facture.get('id')}"):
                            invoice_id_to_delete = facture.get('id')
                            invoice_number_to_delete = facture.get('number')
                    
                            if delete_invoice(st.session_state.user.id, invoice_id_to_delete):
                                delete_transaction_for_invoice(st.session_state.user.id, invoice_number_to_delete)
                                load_user_data(st.session_state.user.id)
                                st.toast("Facture et transaction associée supprimées !")
                                st.rerun()
        # --- Sous-page Gestion de Stock ---
        elif sub_page == "Gestion de Stock":
            st.subheader("Gestion de Stock")
            with st.expander("Ajouter un nouveau produit"):
                with st.form("new_product_form", clear_on_submit=True):
                    nom_produit = st.text_input("Nom du Produit")
                    description = st.text_area("Description")
                    col1, col2, col3 = st.columns(3)
                    with col1: quantite = st.number_input("Quantité en Stock", min_value=0, step=1)
                    with col2: prix_achat = st.number_input("Prix d'Achat", min_value=0.0, format="%.2f")
                    with col3: prix_vente = st.number_input("Prix de Vente", min_value=0.0, format="%.2f")
                    if st.form_submit_button("Ajouter le produit"):
                        if nom_produit:
                            item_data = {
                                "user_id": st.session_state.user.id, "product_name": nom_produit,
                                "description": description, "quantity": quantite,
                                "purchase_price": prix_achat, "sale_price": prix_vente
                            }
                            if add_stock_item(item_data):
                                load_user_data(st.session_state.user.id)
                                st.success(f"Produit '{nom_produit}' ajouté au stock.")
                                st.rerun()
                        else:
                            st.error("Le nom du produit ne peut pas être vide.")
            
            st.markdown("---"); st.subheader("Inventaire Actuel")
            if not st.session_state.stock.empty:
                display_stock = st.session_state.stock.rename(columns={'product_name': 'Nom du Produit', 'description': 'Description', 'quantity': 'Quantité', 'purchase_price': "Prix d'Achat", 'sale_price': 'Prix de Vente'})
                st.dataframe(display_stock[['Nom du Produit', 'Description', 'Quantité', "Prix d'Achat", 'Prix de Vente']], use_container_width=True)
            else:
                st.info("Votre inventaire est vide.")

            st.markdown("---"); st.subheader("Enregistrer un Achat de Stock")
            if not st.session_state.stock.empty:
                with st.form("purchase_stock_form", clear_on_submit=True):
                    product_to_purchase = st.selectbox("Produit Acheté", options=st.session_state.stock["product_name"])
                    quantity_purchased = st.number_input("Quantité Achetée", min_value=1, step=1)
                    if st.form_submit_button("Ajouter au Stock"):
                        success, message = update_stock_quantity(st.session_state.user.id, product_to_purchase, quantity_purchased)
                        if success:
                            load_user_data(st.session_state.user.id)
                            st.toast(message, icon="✅")
                            st.rerun()
                        else:
                            st.warning(message)
            else:
                st.info("Ajoutez d'abord des produits à votre inventaire.")
        # --- CODE AJOUTÉ : Dépenses de fonctionnement ---
        elif sub_page == _("op_expenses"):
            st.subheader(_("op_expenses"))
            with st.form("operating_expenses_form", clear_on_submit=True):
                categorie = st.selectbox("Catégorie de dépense", ["Loyer", "Facture électricité", "Facture Eau", "Facture téléphone et connexion", "Réparation", "Autre"])
                montant = st.number_input("Montant", min_value=0.0, format="%.2f")
                description = st.text_area("Description (obligatoire si 'Réparation' ou 'Autre')")
                if st.form_submit_button("Enregistrer la dépense"):
                    if add_transaction(date.today(), 'Dépense', montant, categorie, description):
                        st.success(f"Dépense de '{categorie}' enregistrée.")
                        st.rerun()
        # --- Sous-page Salaires ---
        elif sub_page == _("salaries"):
            st.subheader(_("salaries"))
            with st.expander("Ajouter un employé"):
                with st.form("new_employee_form", clear_on_submit=True):
                    nom_employe = st.text_input("Nom de l'employé")
                    poste_employe = st.text_input("Poste occupé")
                    salaire_brut = st.number_input(f"Salaire Brut Mensuel ({st.session_state.currency})", min_value=0.0)
                    if st.form_submit_button("Ajouter"):
                        if add_employee(st.session_state.user.id, nom_employe, poste_employe, salaire_brut):
                            load_user_data(st.session_state.user.id)
                            st.success(f"{nom_employe} a été ajouté.")
                            st.rerun()
            st.subheader("Liste des Salaires")
            if not st.session_state.salaries.empty:
                display_salaries = st.session_state.salaries.rename(columns={'nom_employe':"Nom de l'employé", 'poste':'Poste', 'salaire_brut':'Salaire Brut'})
                st.dataframe(display_salaries[["Nom de l'employé", 'Poste', 'Salaire Brut']], use_container_width=True)
                total_salaires = display_salaries['Salaire Brut'].sum()
                st.metric("Masse Salariale Totale", f"{total_salaires:,.0f} {st.session_state.currency}")
                with st.form("pay_salaries_form"):
                    st.write("Ceci enregistrera la masse salariale totale comme une dépense.")
                    if st.form_submit_button("Payer les Salaires"):
                        if add_transaction(date.today(), 'Dépense', total_salaires, 'Salaires', 'Paiement des salaires du mois'):
                            st.success("Paiement des salaires enregistré comme dépense.")
                            st.rerun()
        # --- CODE AJOUTÉ : Planification ---
        elif sub_page == _("planning"):
            st.subheader(_("planning"))
            st.markdown("Un entretien stratégique avec Sir Comptable pour construire votre business plan étape par étape.")

            # Logique du Business Plan en plusieurs étapes
            if 'bp_step' not in st.session_state: st.session_state.bp_step = 0
            if 'bp_data' not in st.session_state: st.session_state.bp_data = {}

            if st.session_state.bp_step == 0:
                with st.form("bp_form_step0"):
                    st.write("**Étape 1 : Votre Idée**")
                    nom_projet = st.text_input("Nom du projet ou de l'entreprise")
                    description_projet = st.text_area("Description détaillée du projet (activité, cible, objectifs)")
                    if st.form_submit_button("Soumettre et passer à l'analyse"):
                        if nom_projet and description_projet:
                            st.session_state.bp_data['nom'] = nom_projet
                            st.session_state.bp_data['description'] = description_projet
                            st.session_state.bp_step = 1
                            st.rerun()
                        else:
                            st.error("Veuillez renseigner le nom et la description.")
        
            elif st.session_state.bp_step == 1:
                st.info(f"**Projet :** {st.session_state.bp_data['nom']}\n\n**Description :** {st.session_state.bp_data['description']}")
                st.write("**Étape 2 : Analyse et Stratégie**")
                with st.form("bp_form_step1"):
                    analyse_marche = st.text_area("Qui sont vos clients cibles et vos concurrents ?", height=150)
                    strategie_marketing = st.text_area("Comment comptez-vous atteindre vos clients ?", height=150)
                    submitted = st.form_submit_button("Générer le Business Plan")
                    if submitted:
                        st.session_state.bp_data['analyse_marche'] = analyse_marche
                        st.session_state.bp_data['strategie_marketing'] = strategie_marketing
                        st.session_state.bp_step = 2
                        st.rerun()

            elif st.session_state.bp_step == 2:
                st.subheader("Proposition de Business Plan par Sir Comptable")
                with st.spinner("Sir Comptable rédige le plan..."):
                    # Simuler une génération de texte pour l'exemple
                    # (Ici, vous mettriez votre appel à l'API Hugging Face si nécessaire)
                    plan_genere = f"""
                    ### 1. Résumé Exécutif
                    Le projet **{st.session_state.bp_data.get('nom')}** vise à {st.session_state.bp_data.get('description')}.
                
                    ### 2. Analyse du Marché
                    {st.session_state.bp_data.get('analyse_marche')}
                
                    ### 3. Stratégie Marketing et Commerciale
                    {st.session_state.bp_data.get('strategie_marketing')}
                
                    ### 4. Prochaines Étapes
                    - Valider l'offre avec des clients potentiels.
                    - Établir un prévisionnel financier détaillé.
                    - Définir les statuts de l'entreprise.
                    """
                    st.markdown(plan_genere)

                if st.button("Créer un nouveau plan"):
                    st.session_state.bp_step = 0
                    st.session_state.bp_data = {}
                    st.rerun()  
            
    # --- PAGE RAPPORTS ---
    elif st.session_state.page == "Rapports":
        st.title("Rapports Financiers")
        st.markdown("Analysez vos performances avec des rapports personnalisés.")
        
        st.subheader("Filtres")
        col1, col2 = st.columns(2)
        with col1:
            type_donnees = st.selectbox("Type de données", ["Dépenses et Revenus", "Dépenses seulement", "Revenus seulement"])
        with col2:
            period_options = ["Année en cours", "Semestre en cours", "Trimestre en cours", "Mois en cours"] + [date(2000, m, 1).strftime('%B') for m in range(1, 13)]
            periode = st.selectbox("Période", period_options)

        st.markdown("---")
        df_filtered = st.session_state.transactions.copy()

        if not df_filtered.empty:
            df_filtered['date'] = pd.to_datetime(df_filtered['date'], utc=True)
            today = datetime.utcnow().date()
            start_date, end_date = None, today

            if periode == "Mois en cours": start_date = today.replace(day=1)
            elif periode == "Trimestre en cours":
                q = (today.month - 1) // 3 + 1
                start_date = today.replace(month=(q - 1) * 3 + 1, day=1)
            elif periode == "Semestre en cours":
                start_month = 1 if today.month <= 6 else 7
                start_date = today.replace(month=start_month, day=1)
            elif periode == "Année en cours":
                start_date = today.replace(month=1, day=1)
            else:
                try:
                    month_number = period_options.index(periode) - 3
                    df_filtered = df_filtered[df_filtered['date'].dt.month == month_number]
                    start_date = None
                except (ValueError, IndexError): pass
            
            if start_date:
                start_date_aware = pd.Timestamp(start_date, tz='UTC')
                end_date_aware = pd.Timestamp(end_date, tz='UTC').replace(hour=23, minute=59, second=59)
                df_filtered = df_filtered[df_filtered['date'].between(start_date_aware, end_date_aware)]
            
            if type_donnees == "Dépenses seulement":
                df_filtered = df_filtered[df_filtered['type'] == 'Dépense']
            elif type_donnees == "Revenus seulement":
                df_filtered = df_filtered[df_filtered['type'] == 'Revenu']

        st.subheader(f"Résultats pour : {periode}")
        if df_filtered.empty:
            st.warning("Aucune donnée à afficher pour les filtres sélectionnés.")
        else:
            display_df_filtered = df_filtered.rename(columns={'date':'Date', 'type':'Type', 'amount':'Montant', 'category':'Catégorie', 'description':'Description'})
            st.dataframe(display_df_filtered[['Date','Type','Montant','Catégorie','Description']], use_container_width=True)

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
        lang_idx = lang_options.index(st.session_state.language) if st.session_state.language in lang_options else 0
        if st.selectbox(_("settings_language"), options=lang_options, index=lang_idx) != st.session_state.language:
            st.session_state.language = lang_options[1-lang_idx]
            st.rerun()

        devises = ["FCFA", "EUR", "USD"]
        devise_idx = devises.index(st.session_state.currency) if st.session_state.currency in devises else 0
        if st.selectbox(_("settings_currency"), devises, index=devise_idx) != st.session_state.currency:
            st.session_state.currency = devises[1-devise_idx] # This logic might be buggy, simpler is better
            st.rerun()

        st.markdown("---")
        st.subheader(_("settings_invoice_info"))
        st.markdown(_("settings_invoice_desc"))

        with st.form("invoice_info_form"):
            logo_file = st.file_uploader(_("settings_upload_logo"), type=['png', 'jpg', 'jpeg'])
            signature_file = st.file_uploader(_("settings_upload_signature"), type=['png', 'jpg', 'jpeg'])
            company_name = st.text_input(_("settings_company_name"), value=st.session_state.get('company_name', ''))
            company_address = st.text_area(_("settings_address"), value=st.session_state.get('company_address', ''))
            company_contact = st.text_input(_("settings_contact"), value=st.session_state.get('company_contact', ''))
            company_vat_rate = st.number_input(_("settings_vat_rate"), value=float(st.session_state.get('company_vat_rate', 0.0) or 0.0), min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
            
            if st.form_submit_button(_("settings_save_info")):
                user_id = st.session_state.user.id
                settings_to_update = {
                    "company_name": company_name, "company_address": company_address,
                    "company_contact": company_contact, "company_vat_rate": company_vat_rate
                }
                if logo_file is not None:
                    logo_bytes = logo_file.getvalue()
                    logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
                    settings_to_update["company_logo_url"] = f"data:image/png;base64,{logo_base64}"
                if signature_file is not None:
                    signature_bytes = signature_file.getvalue()
                    signature_base64 = base64.b64encode(signature_bytes).decode('utf-8')
                    settings_to_update["company_signature_url"] = f"data:image/png;base64,{signature_base64}"
                
                if update_profile_settings(user_id, settings_to_update):
                    load_user_data(user_id)
                    st.success(_("settings_info_updated"))
                    st.rerun()
        
        if st.session_state.get('company_logo'):
            st.write(_("settings_current_logo"))
            st.image(st.session_state.company_logo, width=100)
        if st.session_state.get('company_signature'):
            st.write(_("settings_current_signature"))
            st.image(st.session_state.company_signature, width=150)

    # --- PAGE ADMIN PANEL ---
    elif st.session_state.page == "Admin Panel":
        st.title("👑 Panneau d'administration")
        if st.session_state.user.email != "fmouhamadou13@gmail.com":
            st.error("⛔ Accès refusé."); st.stop()
        
        users = get_all_users()
        if not users:
            st.warning("Aucun utilisateur trouvé.")
        else:
            st.subheader("Liste des utilisateurs")
            for user in users:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    with col1: st.write(f"**{user['email']}**")
                    with col2:
                        new_role = st.selectbox("Rôle", ["user", "admin"], index=0 if user.get("role") == "user" else 1, key=f"role_{user['id']}")
                    with col3:
                        new_status = st.selectbox("Abonnement", ["free", "premium"], index=0 if user.get("subscription_status") == "free" else 1, key=f"sub_{user['id']}")
                    with col4:
                        if st.button("Mettre à jour", key=f"update_{user['id']}"):
                            update_user_role(user['id'], new_role)
                            update_user_subscription(user['id'], new_status)
                            st.success(f"Profil de {user['email']} mis à jour.")
                            st.rerun()













