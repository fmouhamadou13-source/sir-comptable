# dashboard.py
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, date
import io
import plotly.express as px
from fpdf import FPDF
import requests

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
    "ai_question_label": {"Français": "Question de l'utilisateur", "Anglais": "User's question"},
    # ... more to be added as needed
}

def _(key):
    lang = st.session_state.get("language", "Français")
    return TEXTS.get(key, {}).get(lang, f"[{key}]")

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
    st.title("Tableau de Bord")
    st.session_state.sarcasm_mode = st.toggle("Mode Sarcasme", value=st.session_state.sarcasm_mode)
    st.markdown("---")

    if not st.session_state.transactions.empty:
        st.session_state.transactions['Montant'] = pd.to_numeric(st.session_state.transactions['Montant'], errors='coerce').fillna(0)

    total_revenus = st.session_state.transactions[st.session_state.transactions['Type'] == 'Revenu']['Montant'].sum()
    total_depenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Dépense']['Montant'].sum()
    solde_net = total_revenus - total_depenses

    if 'last_total_revenus' not in st.session_state: st.session_state.last_total_revenus = -1

    if st.session_state.sarcasm_mode and st.session_state.last_total_revenus != total_revenus:
        with st.spinner("Sir Comptable affûte ses commentaires..."):
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
                prompt_revenu = f"Tu es Sir Comptable, un majordome sarcastique. En une seule phrase très courte et percutante, commente un revenu total de {total_revenus:,.0f} {st.session_state.currency}."
                st.session_state.revenue_comment = query_ai_comment(prompt_revenu)
                prompt_solde = f"Tu es Sir Comptable, un majordome sarcastique. En une seule phrase très courte et percutante, commente un solde net de {solde_net:,.0f} {st.session_state.currency}."
                st.session_state.balance_comment = query_ai_comment(prompt_solde)
                st.session_state.last_total_revenus = total_revenus
            except Exception:
                st.session_state.revenue_comment = "*Impossible de contacter Sir Comptable pour un commentaire.*"
                st.session_state.balance_comment = "*Sir Comptable est momentanément sans voix.*"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Revenus", f"{total_revenus:,.0f} {st.session_state.currency}")
        if st.session_state.sarcasm_mode:
            st.caption(f"*{st.session_state.get('revenue_comment', '...')}*")
    with col2:
        st.metric("Dépenses", f"{total_depenses:,.0f} {st.session_state.currency}")
    with col3:
        st.metric("Solde Net", f"{solde_net:,.0f} {st.session_state.currency}")
        if st.session_state.sarcasm_mode:
            st.caption(f"*{st.session_state.get('balance_comment', '...')}*")

    st.markdown("---")
    
    col_graphs1, col_graphs2 = st.columns(2)
    with col_graphs1:
        st.subheader("Évolution Mensuelle")
        if not st.session_state.transactions.empty:
            df_copy = st.session_state.transactions.copy()
            df_copy['Mois'] = df_copy['Date'].dt.to_period('M')
            monthly_summary = df_copy.groupby('Mois').apply(lambda x: pd.Series({'Revenus': x[x['Type'] == 'Revenu']['Montant'].sum(),'Dépenses': x[x['Type'] == 'Dépense']['Montant'].sum()})).reset_index()
            monthly_summary['Mois'] = monthly_summary['Mois'].astype(str)
            monthly_summary.sort_values(by='Mois', inplace=True)
            fig_line = px.line(monthly_summary, x='Mois', y=['Revenus', 'Dépenses'], title='Revenus vs. Dépenses')
            st.plotly_chart(fig_line, use_container_width=True)
    with col_graphs2:
        st.subheader("Répartition des Dépenses")
        df_depenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Dépense']
        if not df_depenses.empty:
            fig_pie = px.pie(df_depenses, names='Catégorie', values='Montant', title='Dépenses par Catégorie', hole=.3)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    st.markdown("---")
    st.subheader("Parler à Sir Comptable")
    prompt = st.text_input("Posez votre question...", label_visibility="collapsed")
    
    if st.button("Envoyer"):
        if prompt:
            st.write(f"**Vous :** {prompt}")
            with st.spinner("Sir Comptable est en train de réfléchir..."):
                try:
                    API_URL = "https://esipiikg9rd3h659.us-east4.gcp.endpoints.huggingface.cloud"
                    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

                    # --- CONTEXTE ENRICHI AVEC LES DERNIERS ARTICLES FACTURÉS ---
                    transactions_df = st.session_state.transactions
                    revenus = transactions_df[transactions_df['Type'] == 'Revenu']['Montant'].sum()
                    depenses = transactions_df[transactions_df['Type'] == 'Dépense']['Montant'].sum()
                    solde = revenus - depenses
                    
                    # NOUVELLE LOGIQUE : On récupère les articles des 5 dernières factures
                    recents_articles_str = "Aucune facture récente."
                    if st.session_state.factures:
                        recents_articles = []
                        # On prend les 5 dernières factures (les plus récentes sont à la fin)
                        for facture in st.session_state.factures[-5:]:
                            for item in facture['Articles']:
                                recents_articles.append(f"- {item['description']} ({item['montant']:,.0f} {st.session_state.currency})")
                        recents_articles_str = "\n".join(recents_articles)

                    contexte_financier = (
                        f"Résumé financier : Solde net = {solde:,.0f} {st.session_state.currency}. "
                        f"Voici le détail des articles des dernières factures pour analyse :\n{recents_articles_str}"
                    )
                    # --- FIN DU CONTEXTE ENRICHI ---

                    prompt_final = (
                        f"<s>[INST] Tu es Sir Comptable, un majordome financier sarcastique. "
                        f"Ta mission est de répondre à la question de l'utilisateur en te basant STRICTEMENT sur les faits du contexte fourni, notamment le détail des articles récents. N'invente jamais de données. "
                        f"Contexte : {contexte_financier} "
                        f"Question de l'utilisateur : '{prompt}' [/INST]"
                    )

                    def query(payload):
                        response = requests.post(API_URL, headers=headers, json=payload)
                        return response.json()

                    output = query({"inputs": prompt_final, "parameters": {"max_new_tokens": 512, "return_full_text": False, "do_sample": True, "top_p": 0.9, "temperature": 0.7}})
                    
                    if isinstance(output, list) and 'generated_text' in output[0]:
                        st.success(f"**Sir Comptable :** {output[0]['generated_text'].strip()}")
                    elif 'error' in output:
                        st.error(f"L'IA a rencontré une erreur : {output['error']}")
                    else:
                        st.warning(f"Réponse inattendue de l'IA : {output}")

                except KeyError:
                    st.error("Erreur : Le token Hugging Face (HF_TOKEN) n'est pas trouvé.")
                except Exception as e:
                    st.error(f"Une erreur critique est survenue : {e}")
        else:
            st.warning("Veuillez entrer une question.")

# --- PAGE MES COMPTES ---
elif st.session_state.page == "Mes Comptes":
    st.title("Mes Comptes")
    st.markdown("Gérez ici les différentes sources de vos finances.")
    st.subheader("Liste de vos comptes")
    if not st.session_state.comptes.empty:
        excel_data = convert_df_to_excel(st.session_state.comptes)
        st.download_button(label="📥 Télécharger en Excel (.xlsx)", data=excel_data, file_name='mes_comptes.xlsx')
    st.dataframe(st.session_state.comptes, use_container_width=True)
    with st.expander("Gérer les comptes"):
        if not st.session_state.comptes.empty:
            account_to_manage = st.selectbox("Sélectionnez un compte", options=["<Choisir>"] + list(st.session_state.comptes["Nom du Compte"]))
            if account_to_manage != "<Choisir>":
                account_index = st.session_state.comptes[st.session_state.comptes["Nom du Compte"] == account_to_manage].index[0]
                with st.form(f"edit_{account_index}"):
                    st.write(f"Modification : **{account_to_manage}**")
                    new_name = st.text_input("Nom", value=account_to_manage)
                    new_balance = st.number_input("Solde", value=float(st.session_state.comptes.loc[account_index, "Solde Actuel"]))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Modifier"):
                            st.session_state.comptes.loc[account_index, "Nom du Compte"] = new_name
                            st.session_state.comptes.loc[account_index, "Solde Actuel"] = new_balance
                            st.success("Compte mis à jour."); st.rerun()
                    with col2:
                        if st.form_submit_button("Supprimer"):
                            st.session_state.comptes = st.session_state.comptes.drop(index=account_index).reset_index(drop=True)
                            st.warning("Compte supprimé."); st.rerun()
        with st.form("new_account_form", clear_on_submit=True):
            st.write("Ajouter un nouveau compte")
            nom_compte = st.text_input("Nom du Compte")
            type_compte = st.selectbox("Type", ["Banque", "Mobile Money", "Espèces"])
            solde_initial = st.number_input(f"Solde Initial ({st.session_state.currency})", min_value=0.0)
            if st.form_submit_button("Ajouter"):
                new_account = pd.DataFrame([{"Nom du Compte": nom_compte, "Solde Actuel": solde_initial, "Type": type_compte}])
                st.session_state.comptes = pd.concat([st.session_state.comptes, new_account], ignore_index=True)
                add_transaction(date.today(), 'Revenu', solde_initial, 'Capital Initial', f"Création du compte '{nom_compte}'")
                st.success("Compte ajouté et solde initial enregistré comme revenu."); st.rerun()

# --- PAGE TRANSACTIONS ---
elif st.session_state.page == "Transactions":
    st.title("Historique des Transactions")
    st.markdown("Voici la liste de toutes les opérations enregistrées.")
    st.dataframe(st.session_state.transactions, use_container_width=True)

# --- PAGE SIR BUSINESS ---
elif st.session_state.page == "Sir Business":
    st.title("Sir Business")
    sub_page_options = ["Accueil", "Facturation", "Dépenses de fonctionnement", "Salaires", "Planification"]
    sub_page = st.selectbox("Choisissez une section", sub_page_options)
    
    if sub_page == "Accueil":
        st.header("Bienvenue dans Sir Business")
        st.write("Veuillez choisir une section dans le menu déroulant ci-dessus.")

    elif sub_page == "Facturation":
        st.subheader("Gestion des Factures")
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
                for i, item in enumerate(st.session_state.invoice_items):
                    cols = st.columns([3, 1])
                    item["description"] = cols[0].text_input(f"Description #{i+1}", item["description"], key=f"desc_{i}")
                    item["montant"] = cols[1].number_input(f"Montant", value=float(item["montant"]), key=f"montant_{i}", min_value=0.0, format="%.2f")

                soustotal_ht = sum(item['montant'] for item in st.session_state.invoice_items)
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
                        st.session_state.invoice_items.append({"description": "", "montant": 0.0}); st.rerun()
                with submit_col2:
                    if st.form_submit_button("Enregistrer la facture"):
                        new_invoice_data = {"Numéro": numero_facture, "Client": nom_client, "Date Émission": date_emission, "Statut": "Enregistrée", "Type": type_facture, "Articles": st.session_state.invoice_items.copy(), "Sous-total": soustotal_ht, "TVA %": vat_rate, "Montant TVA": vat_amount, "Montant": total_ttc}
                        st.session_state.factures.append(new_invoice_data)
                        add_transaction(date_emission, type_facture, total_ttc, 'Facturation', f"Facture {numero_facture} pour {nom_client}")
                        st.session_state.invoice_items = [{"description": "", "montant": 0.0}]
                        st.success(f"Facture enregistrée et ajoutée aux transactions."); st.rerun()
        
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
                            pil_logo.save("temp_logo.png")
                            pdf.image("temp_logo.png", x=10, y=8, w=33)
                        except Exception: pass
                    
                    current_y = pdf.get_y()
                    pdf.set_y(8)
                    pdf.set_x(110)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.multi_cell(90, 7, f"{st.session_state.company_name}\n{st.session_state.company_address}\n{st.session_state.company_contact}", 0, 'R')
                    pdf.set_y(current_y + 30)
                    
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, text=f"Facture N°: {facture['Numéro']}", border=0, ln=1, align='C')
                    pdf.ln(5)
                    pdf.set_font("Arial", '', 12)
                    pdf.cell(0, 8, text=f"Client: {facture['Client']}", ln=1)
                    pdf.cell(0, 8, text=f"Date: {facture['Date Émission'].strftime('%d/%m/%Y')}", ln=1)
                    pdf.ln(10)
                    
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(150, 10, "Description", 1, 0, 'C')
                    pdf.cell(40, 10, "Montant", 1, 1, 'C')
                    pdf.set_font("Arial", '', 12)
                    
                    for item in facture["Articles"]:
                        safe_description = item['description'].encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(150, 10, text=safe_description, border=1)
                        pdf.cell(40, 10, text=f"{item['montant']:,.2f}", border=1, ln=1, align='R')

                    pdf.set_font("Arial", '', 12)
                    pdf.cell(150, 10, text="Sous-total HT", border=1, align='R')
                    pdf.cell(40, 10, text=f"{facture.get('Sous-total', 0):,.2f}", border=1, ln=1, align='R')
                    pdf.cell(150, 10, text=f"TVA ({facture.get('TVA %', 0)}%)", border=1, align='R')
                    pdf.cell(40, 10, text=f"{facture.get('Montant TVA', 0):,.2f}", border=1, ln=1, align='R')
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(150, 10, text="TOTAL TTC", border=1, align='R')
                    pdf.cell(40, 10, text=f"{facture['Montant']:,.2f}", border=1, ln=1, align='R')
                    
                    if st.session_state.company_signature:
                        try:
                            sig_bytes = io.BytesIO(st.session_state.company_signature)
                            pil_sig = Image.open(sig_bytes)
                            pil_sig.save("temp_signature.png")
                            pdf.image("temp_signature.png", x=150, y=pdf.get_y() + 10, w=50)
                        except Exception: pass

                    pdf_output = bytes(pdf.output(dest='S'))
                    col3.download_button(label="📄 Télécharger en PDF", data=pdf_output, file_name=f"Facture_{facture['Numéro']}.pdf", mime="application/pdf")

    elif sub_page == "Dépenses de fonctionnement":
        st.subheader("Dépenses de Fonctionnement")
        with st.form("operating_expenses_form", clear_on_submit=True):
            categorie = st.selectbox("Catégorie de dépense", ["Loyer", "Facture électricité", "Facture Eau", "Facture téléphone et connexion", "Réparation"])
            montant = st.number_input("Montant", min_value=0.0, format="%.2f")
            description = st.text_area("Description (obligatoire si 'Réparation')")
            if st.form_submit_button("Enregistrer la dépense"):
                add_transaction(date.today(), 'Dépense', montant, categorie, description)
                st.success(f"Dépense de '{categorie}' enregistrée.")

    elif sub_page == "Salaires":
        st.subheader("Gestion de la Paie")
        with st.expander("Ajouter un employé"):
            with st.form("new_employee_form", clear_on_submit=True):
                nom_employe = st.text_input("Nom de l'employé")
                poste_employe = st.text_input("Poste occupé")
                salaire_brut = st.number_input(f"Salaire Brut Mensuel ({st.session_state.currency})", min_value=0.0)
                if st.form_submit_button("Ajouter"):
                    new_employee = pd.DataFrame([{"Nom de l'employé": nom_employe, "Poste": poste_employe, "Salaire Brut": salaire_brut}])
                    st.session_state.salaries = pd.concat([st.session_state.salaries, new_employee], ignore_index=True)
                    st.success(f"{nom_employe} a été ajouté.")
        
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

    elif sub_page == "Planification":
        st.subheader("Planification d'Entreprise")
        st.markdown("Fournissez les détails de votre projet et Sir Comptable rédigera une ébauche de business plan.")
        with st.form("bp_form"):
            nom_projet = st.text_input("Nom du projet ou de l'entreprise")
            description_projet = st.text_area("Description détaillée du projet (activité, cible, objectifs)")
            budget_disponible = st.number_input(f"Budget de départ disponible ({st.session_state.currency})", min_value=0)
            submitted = st.form_submit_button("Générer l'ébauche")
            if submitted:
                if not nom_projet or not description_projet:
                    st.error("Veuillez renseigner au moins le nom et la description du projet.")
                else:
                    with st.spinner("Sir Comptable rédige votre plan stratégique..."):
                        try:
                            API_URL = "https://esipiikg9rd3h659.us-east4.gcp.endpoints.huggingface.cloud"
                            headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
                            prompt_final_bp = (f"<s>[INST] Tu es Sir Comptable, un conseiller en stratégie d'entreprise sarcastique et réaliste. Ta mission est de rédiger une ébauche de business plan professionnelle et structurée en te basant sur les informations fournies. Adopte un ton direct et pragmatique. Informations du projet: - Nom: '{nom_projet}' - Description: '{description_projet}' - Budget Initial: {budget_disponible:,.0f} {st.session_state.currency}. Le business plan doit inclure les sections suivantes, clairement titrées: 1. **Résumé Exécutif**: Une synthèse percutante. 2. **Analyse du Marché**: Cible, concurrence et opportunités. 3. **Stratégie Marketing et Commerciale**: Comment attirer les clients. 4. **Prévisions Financières Simples**: Comment le budget sera utilisé et les premières estimations de revenus. 5. **Risques et Recommandations**: Tes conseils sarcastiques mais pertinents sur les points faibles du projet. [/INST]")
                            
                            def query(payload):
                                response = requests.post(API_URL, headers=headers, json=payload)
                                return response.json()
                            
                            output = query({"inputs": prompt_final_bp, "parameters": {"max_new_tokens": 1024, "return_full_text": False, "do_sample": True, "top_p": 0.9, "temperature": 0.7}})
                            
                            if isinstance(output, list) and 'generated_text' in output[0]:
                                response_text = output[0]['generated_text']
                                st.markdown("---")
                                st.subheader("Proposition de Business Plan par Sir Comptable")
                                st.markdown(response_text)
                            elif 'error' in output:
                                st.error(f"L'IA a rencontré une erreur : {output['error']}")
                            else:
                                st.warning(f"Réponse inattendue de l'IA : {output}")
                        except Exception as e:
                            st.error(f"Une erreur critique est survenue : {e}")

# --- PAGE RAPPORTS ---
elif st.session_state.page == "Rapports":
    st.title("Rapports Financiers")
    st.markdown("Analysez vos performances avec des rapports personnalisés.")
    
    st.subheader("Filtres")
    col1, col2 = st.columns(2)
    with col1:
        type_donnees = st.selectbox("Type de données", ["Dépenses et Revenus", "Dépenses seulement", "Revenus seulement"])
    with col2:
        period_options = ["Année en cours", "Semestre en cours", "Trimestre en cours", "Mois en cours"] + [date(2024, m, 1).strftime('%B') for m in range(1, 13)]
        periode = st.selectbox("Période", period_options)

    df_filtered = st.session_state.transactions.copy()
    if not df_filtered.empty:
        today = date.today()
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
        if start_date:
            df_filtered = df_filtered[(df_filtered['Date'] >= pd.to_datetime(start_date)) & (df_filtered['Date'] <= pd.to_datetime(end_date))]
        if type_donnees == "Dépenses seulement": df_filtered = df_filtered[df_filtered['Type'] == 'Dépense']
        elif type_donnees == "Revenus seulement": df_filtered = df_filtered[df_filtered['Type'] == 'Revenu']

    st.markdown("---")
    st.subheader(f"Résultats pour : {periode}")
    if df_filtered.empty:
        st.warning("Aucune donnée à afficher pour la période sélectionnée.")
    else:
        st.dataframe(df_filtered, use_container_width=True)

# --- PAGE ABONNEMENT ---
elif st.session_state.page == "Abonnement":
    st.title("Abonnement Premium")
    st.markdown("Passez à la version Premium pour débloquer toutes les fonctionnalités de Sir Comptable.")

    st.markdown("---")
    st.subheader("Forfait Premium")
    st.markdown("- Transactions illimitées\n- Accès complet à Sir Business\n- Rapports avancés")
    st.metric("Prix", f"5,000 {st.session_state.currency}/mois")
    
    if st.button("Procéder au paiement"):
        with st.spinner("Initialisation de la transaction avec PAYDUNYA..."):
            try:
                api_url = "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create"
                headers = {
                    'PAYDUNYA-MASTER-KEY': st.secrets["PAYDUNYA_MASTER_KEY"],
                    'PAYDUNYA-PRIVATE-KEY': st.secrets["PAYDUNYA_PRIVATE_KEY"],
                    'PAYDUNYA-PUBLIC-KEY': st.secrets["PAYDUNYA_PUBLIC_KEY"],
                    'PAYDUNYA-TOKEN': st.secrets["PAYDUNYA_TOKEN"],
                    'Content-Type': 'application/json'
                }
                payload = {
                    "invoice": {"items": {"item_0": {"name": "Abonnement Premium Sir Comptable (1 mois)", "quantity": 1, "unit_price": "5000", "total_price": "5000"}}, "total_amount": 5000},
                    "store": {"name": "Sir Comptable"},
                    "actions": {"return_url": "http://localhost", "cancel_url": "http://localhost"}
                }
                response = requests.post(api_url, json=payload, headers=headers)
                response_data = response.json()

                if response_data.get('response_code') == '00':
                    payment_url = response_data.get('response_text')
                    st.success("Transaction initialisée !")
                    st.markdown(f'<h5><a href="{payment_url}" target="_blank">Cliquez ici pour ouvrir la page de paiement sécurisée de PAYDUNYA dans un nouvel onglet.</a></h5>', unsafe_allow_html=True)
                else:
                    error_message = response_data.get('response_text', 'Erreur inconnue.')
                    st.error(f"Erreur lors de l'initialisation du paiement : {error_message}")
            except KeyError:
                st.error("Erreur : Une ou plusieurs clés PAYDUNYA ne sont pas trouvées. Veuillez vérifier votre fichier secrets.toml.")
            except Exception as e:
                st.error(f"Une erreur critique est survenue : {e}")

# --- PAGE PARAMÈTRES ---
elif st.session_state.page == "Paramètres":
    st.title("Paramètres")
    st.subheader("Préférences Générales")
    
    langues = ["Français", "Anglais", "Wolof"]
    langue_actuelle_index = langues.index(st.session_state.language)
    new_lang = st.selectbox("Langue", langues, index=langue_actuelle_index)
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.success(f"Langue changée en {new_lang}.")

    devises = ["FCFA", "EUR", "USD"]
    devise_actuelle_index = devises.index(st.session_state.currency)
    new_curr = st.selectbox("Devise", devises, index=devise_actuelle_index)
    if new_curr != st.session_state.currency:
        st.session_state.currency = new_curr
        st.success(f"Devise changée en {new_curr}."); st.rerun()
    
    st.markdown("---")
    st.subheader("Informations de Facturation")
    st.markdown("Ces informations apparaîtront sur vos factures PDF.")

    with st.form("invoice_info_form"):
        logo_file = st.file_uploader("Télécharger votre logo (laisser vide pour ne pas changer)", type=['png', 'jpg', 'jpeg'])
        signature_file = st.file_uploader("Télécharger votre signature (laisser vide pour ne pas changer)", type=['png', 'jpg', 'jpeg'])
        
        company_name = st.text_input("Nom de votre entreprise", value=st.session_state.company_name)
        company_address = st.text_area("Adresse", value=st.session_state.company_address)
        company_contact = st.text_input("Contact (Téléphone / Email)", value=st.session_state.company_contact)
        company_vat_rate = st.number_input("Taux de TVA (%)", value=float(st.session_state.company_vat_rate), min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
        
        submitted = st.form_submit_button("Enregistrer les informations")
        if submitted:
            if logo_file is not None:
                st.session_state.company_logo = logo_file.getvalue()
            if signature_file is not None:
                st.session_state.company_signature = signature_file.getvalue()
            st.session_state.company_name = company_name
            st.session_state.company_address = company_address
            st.session_state.company_contact = company_contact
            st.session_state.company_vat_rate = company_vat_rate
            st.success("Informations de facturation mises à jour.")
    
    if st.session_state.company_logo:
        st.write("Logo actuel :")
        st.image(st.session_state.company_logo, width=100)
    if st.session_state.company_signature:
        st.write("Signature actuelle :")
        st.image(st.session_state.company_signature, width=150)