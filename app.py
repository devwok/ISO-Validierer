import streamlit as st
from validators.hvb_validator import HVBValidator
from validators.coba_validator import CoBaValidator
import utils
import pandas as pd

# --- SAP STYLE CSS ---
SAP_STYLE = """
<style>
    /* Logo in Sidebar */
    .sidebar-logo {
        text-align: center;
        padding: 20px 10px;
        margin-bottom: 20px;
    }
    
    .sidebar-logo img {
        max-width: 180px;
        height: auto;
    }
    
    /* Header Logo */
    .header-logo {
        display: inline-block;
        vertical-align: middle;
        margin-right: 15px;
    }
    
    .header-logo img {
        height: 50px;
        width: auto;
    }
    
    /* SAP Blau-Grau Theme - IMPROVED CONTRAST */
    .sap-section {
        background: linear-gradient(to bottom, #e8f2fc 0%, #d8e8f7 100%);
        border: 1px solid #8fb3d9;
        border-radius: 3px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .sap-header {
        background: linear-gradient(to bottom, #b8d4f1 0%, #a8c8ea 100%);
        border: 1px solid #7ba7d6;
        padding: 8px 12px;
        font-weight: bold;
        color: #002244;  /* Darker for better readability */
        font-size: 14px;
        border-radius: 3px 3px 0 0;
        margin-bottom: 0;
    }
    
    /* IMPROVED: Darker text, better contrast */
    .sap-field-label {
        color: #1a1a1a;  /* Much darker! */
        font-size: 13px;
        font-weight: 500;
        padding: 5px 0;
    }
    
    .sap-field-value {
        background: white;
        border: 1px solid #999;
        padding: 4px 8px;
        font-family: monospace;
        font-size: 13px;
        color: #000000;  /* Pure black for readability */
        border-radius: 2px;
    }
    
    /* Streamlit Input Fields - IMPROVED */
    .stTextInput input {
        color: #000000 !important;  /* Black text */
        font-weight: 500 !important;
        background: white !important;
    }
    
    .stTextArea textarea {
        color: #000000 !important;  /* Black text */
        font-weight: 500 !important;
        background: white !important;
    }
    
    /* Labels - IMPROVED */
    .stTextInput label, .stTextArea label, .stSelectbox label {
        color: #1a1a1a !important;  /* Dark text */
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Metrics - IMPROVED */
    div[data-testid="stMetricValue"] {
        font-size: 16px !important;
        color: #002244 !important;  /* Dark blue */
        font-weight: bold !important;
        font-family: monospace;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #1a1a1a !important;  /* Dark */
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    
    /* Tabs - IMPROVED */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #d4e4f7;
        border: 1px solid #8fb3d9;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        color: #002244 !important;  /* Darker tab text */
        font-weight: 600 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        border-bottom: 2px solid white;
        color: #001122 !important;  /* Even darker for active tab */
        font-weight: bold !important;
    }
    
    /* DataFrames - IMPROVED */
    .dataframe {
        font-size: 13px !important;
        color: #000000 !important;
    }
    
    .dataframe th {
        background: #b8d4f1 !important;
        color: #002244 !important;
        font-weight: bold !important;
    }
    
    .dataframe td {
        color: #000000 !important;
    }
    
    /* General text readability */
    p, span, div {
        color: #1a1a1a;
    }
    
    /* Caption text */
    .stCaption {
        color: #333333 !important;
        font-size: 12px !important;
    }
</style>
"""

# --- SETUP ---
st.set_page_config(
    page_title="ISO Payment Validator | SAP Style", 
    page_icon="📋", 
    layout="wide"
)
st.markdown(SAP_STYLE, unsafe_allow_html=True)

XSD_PATH = "schemas/pain.001.001.09.xsd"

# --- SIDEBAR (SAP Navigation Style) ---
with st.sidebar:
    # KTC LOGO
    try:
        st.image("KTC_Logo_blauer_Hintergrund.png", use_column_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    except:
        st.markdown('<div style="text-align: center; font-size: 40px; padding: 20px;">🏢</div>', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Einstellungen")
    bank = st.selectbox("Hausbank Profil", ["HypoVereinsbank", "Commerzbank"])
    
    if bank == "HypoVereinsbank":
        validator = HVBValidator(XSD_PATH)
    else:
        validator = CoBaValidator(XSD_PATH)
        
    st.divider()
    st.caption("📌 **ISO 20022 Payment Validator**")
    st.caption("Version 2.5 | KTC Treasury Consulting")

# --- MAIN ---
# Header with KTC Logo
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("KTC_Logo_blauer_Hintergrund.png", width=120)
    except:
        st.markdown("### 🏢")

with col_title:
    st.title("📋 ISO 20022 Payment Validator")
    st.caption("**KTC Treasury Consulting** | Free Form Payment Tool")
    st.caption(f"Aktives Bankprofil: **{bank}**")

uploaded_file = st.file_uploader(
    "📂 Zahlungsdatei hochladen (pain.001.001.09 XML)", 
    type=["xml"],
    help="Wählen Sie eine ISO 20022 XML-Datei zum Validieren und Anzeigen"
)

if uploaded_file:
    xml_bytes = uploaded_file.read()
    
    # 1. Validieren
    validator.validate(xml_bytes)
    profile_name, profile_desc = validator.get_profile_info()
    
    # 2. Parsen
    data = utils.parse_payment_data(xml_bytes)

    # --- TABS (SAP Style) ---
    tab_payment, tab_check, tab_rules, tab_xml = st.tabs([
        "💳 Payment Data", 
        "🔍 Validation Log",
        "📜 Bank Rules",
        "📄 XML Source"
    ])

    # ========== TAB 1: PAYMENT DATA (SAP FIBLFFP Style) ==========
    with tab_payment:
        if data:
            for batch_idx, b in enumerate(data['batches'], 1):
                
                # === PAYEE SECTION ===
                st.markdown('<div class="sap-header">Payee</div>', unsafe_allow_html=True)
                st.markdown('<div class="sap-section">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.text_input("Name", value=b['dbtr'], disabled=True, key=f"payee_name_{batch_idx}")
                    st.text_input("Bank Account (IBAN)", value=b['iban'], disabled=True, key=f"payee_iban_{batch_idx}")
                
                with col2:
                    st.text_input("Reference (PmtInfId)", value=b['id'], disabled=True, key=f"ref_{batch_idx}")
                    # Bank Country und Bank Key würden hier stehen (nicht in ISO XML)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # === POSTING DATA SECTION ===
                st.markdown('<div class="sap-header">Posting Data</div>', unsafe_allow_html=True)
                st.markdown('<div class="sap-section">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    # Company Code / Business Area nicht in ISO direkt
                    st.text_input("Payment Batch ID", value=b['id'], disabled=True, key=f"batch_{batch_idx}")
                
                with col2:
                    st.text_input("Execution Date", value=b['date'], disabled=True, key=f"date_{batch_idx}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # === PAYMENT DATA TAB SECTION ===
                payment_tab, additional_tab = st.tabs(["Payment Data", "Additional"])
                
                with payment_tab:
                    st.markdown('<div class="sap-header">Payment Overview</div>', unsafe_allow_html=True)
                    st.markdown('<div class="sap-section">', unsafe_allow_html=True)
                    
                    # Summary Metrics
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    with metric_col1:
                        st.metric("Total Transactions", len(b['txs']))
                    with metric_col2:
                        st.metric("Control Sum", f"{b.get('ctrl_sum', '-')} {b.get('ccy', 'EUR')}")
                    with metric_col3:
                        st.metric("Currency", b.get('ccy', 'EUR'))
                    with metric_col4:
                        st.metric("Payment Method", "SEPA CT")  # Hardcoded, could parse from XML
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # === TRANSACTIONS TABLE (SAP Style) ===
                    st.markdown('<div class="sap-header">Transaction Items</div>', unsafe_allow_html=True)
                    
                    if b['txs']:
                        tx_data = []
                        for idx, tx in enumerate(b['txs'], 1):
                            tx_data.append({
                                "Item": idx,
                                "Creditor Name": tx['cdtr'],
                                "IBAN": tx['cdtr_iban'],
                                "Amount": f"{tx['amt']} {tx['ccy']}",
                                "Reference (E2E)": tx['e2e'],
                                "Reference Text": tx['rmt'][:40] + "..." if len(tx['rmt']) > 40 else tx['rmt'],
                            })
                        
                        df = pd.DataFrame(tx_data)
                        
                        # Display as table
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                        
                        # === INDIVIDUAL TRANSACTION DETAILS (SAP Form Style) ===
                        st.markdown("---")
                        st.markdown("#### 🔍 Transaction Details")
                        
                        selected_tx = st.selectbox(
                            "Select Transaction to View",
                            range(1, len(b['txs']) + 1),
                            format_func=lambda x: f"Transaction {x}: {b['txs'][x-1]['cdtr']} - {b['txs'][x-1]['amt']} {b['txs'][x-1]['ccy']}",
                            key=f"tx_select_{batch_idx}"
                        )
                        
                        if selected_tx:
                            tx = b['txs'][selected_tx - 1]
                            
                            st.markdown('<div class="sap-section">', unsafe_allow_html=True)
                            
                            # Transaction Form (SAP 2-column layout)
                            form_col1, form_col2 = st.columns([1, 1])
                            
                            with form_col1:
                                st.text_input("Creditor Name", value=tx['cdtr'], disabled=True, key=f"tx_name_{batch_idx}_{selected_tx}")
                                st.text_input("IBAN", value=tx['cdtr_iban'], disabled=True, key=f"tx_iban_{batch_idx}_{selected_tx}")
                                st.text_input("Amount", value=f"{tx['amt']} {tx['ccy']}", disabled=True, key=f"tx_amt_{batch_idx}_{selected_tx}")
                            
                            with form_col2:
                                st.text_input("End-to-End Reference", value=tx['e2e'], disabled=True, key=f"tx_e2e_{batch_idx}_{selected_tx}")
                                if tx.get('cdtr_bic') and tx['cdtr_bic'] != '-':
                                    st.text_input("BIC", value=tx['cdtr_bic'], disabled=True, key=f"tx_bic_{batch_idx}_{selected_tx}")
                                if tx.get('purp') and tx['purp'] != '-':
                                    st.text_input("Purpose Code", value=tx['purp'], disabled=True, key=f"tx_purp_{batch_idx}_{selected_tx}")
                            
                            st.text_area(
                                "Reference Text (Verwendungszweck)", 
                                value=tx['rmt'], 
                                height=80, 
                                disabled=True,
                                key=f"tx_rmt_{batch_idx}_{selected_tx}"
                            )
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                
                with additional_tab:
                    st.markdown('<div class="sap-section">', unsafe_allow_html=True)
                    st.info("📌 Additional payment information (if available in XML)")
                    
                    # Header Info
                    h = data['header']
                    st.text_input("Message ID (MsgId)", value=h['id'], disabled=True, key=f"msgid_{batch_idx}")
                    st.text_input("Creation DateTime", value=h['cre_dt'], disabled=True, key=f"credt_{batch_idx}")
                    st.text_input("Initiating Party", value=h['init_pty'], disabled=True, key=f"initpty_{batch_idx}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Separator between batches
                if batch_idx < len(data['batches']):
                    st.markdown("---")
                    st.markdown("---")
        
        else:
            st.error("❌ Could not parse payment file. Please check XML structure.")

    # ========== TAB 2: VALIDATION LOG ==========
    with tab_check:
        st.subheader("🔍 Validation Results")
        
        if not validator.errors:
            st.success("✅ **File is technically and functionally correct.**")
        else:
            errs = [e for e in validator.errors if e['level'] in ['CRITICAL','ERROR']]
            warns = [e for e in validator.errors if e['level'] == 'WARNING']
            
            col1, col2 = st.columns(2)
            col1.metric("❌ Errors", len(errs))
            col2.metric("⚠️ Warnings", len(warns))
            
            st.divider()
            
            for e in validator.errors:
                icon = "🛑" if e['level'] == 'CRITICAL' else "🟠" if e['level'] == 'ERROR' else "⚠️"
                with st.expander(f"{icon} Line {e['line']}: {e['title']}", expanded=True):
                    st.write(e['msg'])
                    if e.get('tag'): 
                        st.code(f"XML Tag: <{e['tag']}>")

    # ========== TAB 3: BANK RULES ==========
    with tab_rules:
        st.subheader("📜 Active Bank Profile")
        st.markdown(f"## {profile_name}")
        st.markdown(profile_desc)

    # ========== TAB 4: XML SOURCE ==========
    with tab_xml:
        st.subheader("📄 XML Source Analysis")
        if validator.errors:
            st.caption("🔴 Lines with errors are highlighted in red.")
        
        html_view = utils.render_highlighted_xml(xml_bytes, validator.errors)
        st.markdown(html_view, unsafe_allow_html=True)

