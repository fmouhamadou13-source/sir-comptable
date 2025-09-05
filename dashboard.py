# dashboard.py
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, date
import io
import plotly.express as px
from fpdf import FPDF
import requests
import os

# --- DICTIONNAIRE DE TRADUCTION COMPLET ---
TEXTS = {
    # General
    "send": {"Français": "Envoyer", "Anglais": "Send"},
    "error_critical": {"Français": "Une erreur critique est survenue", "Anglais": "A critical error occurred"},
    "app_title": {"Français": "Sir Comptable - Tableau de Bord", "Anglais": "Sir Comptable - Dashboard"},
    "you": {"Français": "Vous", "Anglais": "You"},

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
    return str(text).encode('latin-1', 'replace').decode('latin-1')

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
    new_data = pd.DataFrame([{"Date": pd.to_datetime(transaction_date), "Type": trans_type, "Montant": amount, "Catégorie": category, "Description": description}])
    st.session_state.transactions = pd.concat([st.session_state.transactions, new_data], ignore_index=True)

# --- Initialisation de la mémoire ---
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

# --- Barre latérale ---
with st.sidebar:
    try:
        logo_image = Image.open("logo sir comptable.jpg")
        st.image(logo_image, width=180)
    except FileNotFoundError:
        st.error(_("logo_file_missing"))
    st.title("Sir Comptable")
    st.markdown("---")
    
    if st.button(_("sidebar_dashboard"), use_container_width=True): st.session_state.page = "Tableau de Bord"
    if st.button(_("sidebar_accounts"), use_container_width=True): st.session_state.page = "Mes Comptes"
    if st.button(_("sidebar_transactions"), use_container_width=True): st.session_state.page = "Transactions"
    if st.button(_("sidebar_business"), use_container_width=True): st.session_state.page = "Sir Business"
    if st.button(_("sidebar_reports"), use_container_width=True): st.session_state.page = "Rapports"
    st.markdown("---")
    if st.button(_("sidebar_subscribe"), use_container_width=True): st.session_state.page = "Abonnement"
    st.markdown("---")
    if st.button(_("sidebar_settings"), use_container_width=True): st.session_state.page = "Paramètres"

# --- PAGE TABLEAU DE BORD ---
if st.session_state.page == "Tableau de Bord":
    st.title(_("dashboard_title"))
    st.session_state.sarcasm_mode = st.toggle(_("sarcasm_mode"), value=st.session_state.sarcasm_mode)
    st.markdown("---")

    if not st.session_state.transactions.empty:
        st.session_state.transactions['Montant'] = pd.to_numeric(st.session_state.transactions['Montant'], errors='coerce').fillna(0)

    total_revenus = st.session_state.transactions[st.session_state.transactions['Type'] == 'Revenu']['Montant'].sum()
    total_depenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Dépense']['Montant'].sum()
    solde_net = total_revenus - total_depenses

    if 'last_total_revenus' not in st.session_state: st.session_state.last_total_revenus = -1

    if st.session_state.sarcasm_mode and st.session_state.last_total_revenus != total_revenus:
        with st.spinner(_("thinking")):
            try:
                API_URL = "https://esipiikg9rd3h659.us-east4.gcp.endpoints.huggingface.cloud"
                headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

                def query_ai_comment(prompt_text):
                    formatted_prompt = f"<s>[INST] {prompt_text} [/INST]"
                    response = requests.post(API_URL, headers=headers, json={"inputs": formatted_prompt, "parameters": {"max_new_tokens": 50, "return_full_text": False, "do_sample": True, "temperature": 0.7}})
                    output = response.json()
                    if isinstance(output, list) and 'generated_text' in output[0]:
                        return output[0]['generated_text'].strip()
                    return ""
                
                lang = st.session_state.language
                prompt_revenu = f"Tu es Sir Comptable, un majordome sarcastique. En une seule phrase très courte et percutante, commente un revenu total de {total_revenus:,.0f} {st.session_state.currency}. Réponds en {lang}."
                st.session_state.revenue_comment = query_ai_comment(prompt_revenu)
                prompt_solde = f"Tu es Sir Comptable, un majordome sarcastique. En une seule phrase très courte et percutante, commente un solde net de {solde_net:,.0f} {st.session_state.currency}. Réponds en {lang}."
                st.session_state.balance_comment = query_ai_comment(prompt_solde)
                st.session_state.last_total_revenus = total_revenus
            except Exception:
                st.session_state.revenue_comment = _("error_ai_contact")
                st.session_state.balance_comment = _("error_ai_speechless")

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
            df_copy['Mois'] = df_copy['Date'].dt.to_period('M')
            monthly_summary = df_copy.groupby('Mois').apply(lambda x: pd.Series({'Revenus': x[x['Type'] == 'Revenu']['Montant'].sum(),'Dépenses': x[x['Type'] == 'Dépense']['Montant'].sum()})).reset_index()
            monthly_summary['Mois'] = monthly_summary['Mois'].astype(str)
            monthly_summary.sort_values(by='Mois', inplace=True)
            fig_line = px.line(monthly_summary, x='Mois', y=[_("revenues"), _("expenses")], title=f'{_("revenues")} vs. {_("expenses")}')
            st.plotly_chart(fig_line, use_container_width=True)
    with col_graphs2:
        st.subheader(_("expense_distribution"))
        df_depenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Dépense']
        if not df_depenses.empty:
            fig_pie = px.pie(df_depenses, names='Catégorie', values='Montant', title=_("expense_distribution"))
            st.plotly_chart(fig_pie, use_container_width=True)
            
    st.markdown("---")
    st.subheader(_("talk_to_sir_comptable"))
    prompt = st.text_input("ask_your_question", label_visibility="collapsed", placeholder=_("ask_your_question"))
    
    if st.button(_("send")):
        if prompt:
            st.write(f"**{_('you')} :** {prompt}")
            with st.spinner(_("thinking")):
                try:
                    API_URL = "https://esipiikg9rd3h659.us-east4.gcp.endpoints.huggingface.cloud"
                    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
                    # ... (logique de contexte identique)

                    prompt_final = (
                        f"<s>[INST] {_('ai_persona')} "
                        f"{_('ai_context_label')} : {contexte_financier} "
                        f"{_('ai_question_label')} : '{prompt}' [/INST]"
                    )
                    # ... (logique de la requête identique)
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
            account_to_manage = st.selectbox(_("select_account"), options=[_("choose")] + list(st.session_state.comptes["Nom du Compte"]))
            if account_to_manage != _("choose"):
                # ... (logique de modification/suppression traduite)
                pass
        with st.form("new_account_form", clear_on_submit=True):
            st.write(_("add_new_account"))
            nom_compte = st.text_input(_("account_name"))
            # ... (logique d'ajout traduite)

# --- PAGE TRANSACTIONS ---
elif st.session_state.page == "Transactions":
    st.title(_("transactions_title"))
    st.markdown(_("transactions_description"))
    st.dataframe(st.session_state.transactions, use_container_width=True)

# --- PAGE SIR BUSINESS ---
elif st.session_state.page == "Sir Business":
    st.title(_("business_title"))
    sub_page_options = [_("home"), _("invoicing"), _("op_expenses"), _("salaries"), _("planning")]
    sub_page = st.selectbox(_("choose_section"), sub_page_options)
    
    # ... (toutes les sous-pages traduites avec _())

# --- PAGE RAPPORTS ---
elif st.session_state.page == "Rapports":
    st.title("Rapports Financiers") # À traduire
    # ... (contenu à traduire)

# --- PAGE ABONNEMENT ---
elif st.session_state.page == "Abonnement":
    st.title("Abonnement Premium") # À traduire
    # ... (contenu à traduire)

# --- PAGE PARAMÈTRES ---
elif st.session_state.page == "Paramètres":
    st.title(_("settings_title"))
    st.subheader(_("settings_general"))
    
    langue_choisie = st.selectbox(_("settings_language"), options=["Français", "Anglais"], index=["Français", "Anglais"].index(st.session_state.language))
    if langue_choisie != st.session_state.language:
        st.session_state.language = langue_choisie
        st.rerun()

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
            # ... (logique de sauvegarde identique)
            st.success(_("settings_info_updated"))
    
    if st.session_state.company_logo:
        st.write(_("settings_current_logo"))
        st.image(st.session_state.company_logo, width=100)
    if st.session_state.company_signature:
        st.write(_("settings_current_signature"))
        st.image(st.session_state.company_signature, width=150)
