import streamlit as st
from validators.hvb_validator import HVBValidator
from validators.coba_validator import CoBaValidator
import utils
import pandas as pd

# --- READABILITY-FOCUSED CSS ---
CLEAN_STYLE = """
<style>
    /* ==================== MAXIMUM READABILITY ==================== */
    
    /* Input Fields - BLACK TEXT on WHITE */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        color: #000000 !important;
        font-weight: 500 !important;
        background: white !important;
        border: 1px solid #999 !important;
    }
    
    /* Labels - BLACK & BOLD */
    .stTextInput label, .stTextArea label, .stSelectbox label, label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Metrics - LARGE & BLACK */
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Headers - BLACK */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    /* Text - BLACK (no gray!) */
    p, span, div {
        color: #000000;
    }
    
    /* Captions - Dark Gray */
    .stCaption {
        color: #444444 !important;
        font-size: 13px !important;
    }
    
    /* Tabs - BOLD & CLEAR */
    .stTabs [data-baseweb="tab"] {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 10px 20px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #0066cc !important;
        font-weight: bold !important;
        border-bottom: 3px solid #0066cc !important;
    }
    
    /* DataFrames - BLACK TEXT */
    .dataframe {
        font-size: 13px !important;
        color: #000000 !important;
    }
    
    .dataframe th {
        background: #e8f4ff !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    .dataframe td {
        color: #000000 !important;
    }
    
    /* Sidebar - Light Background */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    
    /* Info/Success Boxes - Readable */
    .stAlert {
        color: #000000 !important;
    }
</style>
"""

# --- SETUP ---
st.set_page_config(
    page_title="ISO 20022 Payment Validator | KTC", 
    page_icon="📋", 
    layout="wide"
)
st.markdown(CLEAN_STYLE, unsafe_allow_html=True)

XSD_PATH = "schemas/pain.001.001.09.xsd"

# --- SIDEBAR ---
with st.sidebar:
    # KTC LOGO - Nur 1x, kleiner!
    try:
        st.image("KTC_Logo_blauer_Hintergrund.png", width=150)
        st.markdown("<br>", unsafe_allow_html=True)
    except:
        st.markdown("🏢", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Einstellungen")
    bank = st.selectbox("Hausbank Profil", ["HypoVereinsbank", "Commerzbank"])
    
    if bank == "HypoVereinsbank":
        validator = HVBValidator(XSD_PATH)
    else:
        validator = CoBaValidator(XSD_PATH)
        
    st.divider()
    st.caption("📌 **ISO 20022 Payment Validator**")
    st.caption("Version 2.6 | KTC Treasury Consulting")

# --- MAIN HEADER (ohne Logo!) ---
st.title("📋 ISO 20022 Payment Validator")
st.markdown("**KTC Treasury Consulting** | Free Form Payment Tool")
st.caption(f"Aktives Bankprofil: **{bank}**")

uploaded_file = st.file_uploader(
    "📂 Zahlungsdatei hochladen (pain.001.001.09 XML)", 
    type=["xml"],
    help="Wählen Sie eine ISO 20022 XML-Datei"
)

if uploaded_file:
    xml_bytes = uploaded_file.read()
    
    # Validieren
    validator.validate(xml_bytes)
    profile_name, profile_desc = validator.get_profile_info()
    
    # Parsen
    data = utils.parse_payment_data(xml_bytes)

    # --- TABS ---
    tab_payment, tab_check, tab_rules, tab_xml = st.tabs([
        "💳 Payment Data", 
        "🔍 Validation Log",
        "📜 Bank Rules",
        "📄 XML Source"
    ])

    # ========== TAB 1: PAYMENT DATA ==========
    with tab_payment:
        if data:
            for batch_idx, b in enumerate(data['batches'], 1):
                
                # PAYEE SECTION
                st.markdown("### 👤 Payee")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Name", value=b['dbtr'], disabled=True, key=f"payee_name_{batch_idx}")
                    st.text_input("Bank Account (IBAN)", value=b['iban'], disabled=True, key=f"payee_iban_{batch_idx}")
                
                with col2:
                    st.text_input("Reference (PmtInfId)", value=b['id'], disabled=True, key=f"ref_{batch_idx}")
                
                st.markdown("---")
                
                # POSTING DATA SECTION
                st.markdown("### 📊 Posting Data")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Payment Batch ID", value=b['id'], disabled=True, key=f"batch_{batch_idx}")
                
                with col2:
                    st.text_input("Execution Date", value=b['date'], disabled=True, key=f"date_{batch_idx}")
                
                st.markdown("---")
                
                # PAYMENT TABS
                payment_tab, additional_tab = st.tabs(["💳 Payment Data", "📎 Additional"])
                
                with payment_tab:
                    st.markdown("### 📊 Payment Overview")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Transactions", len(b['txs']))
                    col2.metric("Control Sum", f"{b.get('ctrl_sum', '-')} {b.get('ccy', 'EUR')}")
                    col3.metric("Currency", b.get('ccy', 'EUR'))
                    col4.metric("Payment Method", "SEPA CT")
                    
                    st.markdown("---")
                    
                    # TRANSACTIONS TABLE
                    st.markdown("### 💸 Transaction Items")
                    
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
                        st.dataframe(df, use_container_width=True, hide_index=True, height=400)
                        
                        # TRANSACTION SELECTOR
                        st.markdown("---")
                        st.markdown("### 🔍 Transaction Details")
                        
                        selected_tx = st.selectbox(
                            "Select Transaction to View",
                            range(1, len(b['txs']) + 1),
                            format_func=lambda x: f"Transaction {x}: {b['txs'][x-1]['cdtr']} - {b['txs'][x-1]['amt']} {b['txs'][x-1]['ccy']}",
                            key=f"tx_select_{batch_idx}"
                        )
                        
                        if selected_tx:
                            tx = b['txs'][selected_tx - 1]
                            
                            st.markdown("---")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.text_input("Creditor Name", value=tx['cdtr'], disabled=True, key=f"tx_name_{batch_idx}_{selected_tx}")
                                st.text_input("IBAN", value=tx['cdtr_iban'], disabled=True, key=f"tx_iban_{batch_idx}_{selected_tx}")
                                st.text_input("Amount", value=f"{tx['amt']} {tx['ccy']}", disabled=True, key=f"tx_amt_{batch_idx}_{selected_tx}")
                            
                            with col2:
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
                
                with additional_tab:
                    st.markdown("### 📎 Additional Information")
                    st.info("📌 Additional payment information from XML header")
                    
                    h = data['header']
                    st.text_input("Message ID (MsgId)", value=h['id'], disabled=True, key=f"msgid_{batch_idx}")
                    st.text_input("Creation DateTime", value=h['cre_dt'], disabled=True, key=f"credt_{batch_idx}")
                    st.text_input("Initiating Party", value=h['init_pty'], disabled=True, key=f"initpty_{batch_idx}")
                
                # Separator
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
