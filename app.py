import streamlit as st
from validators.hvb_validator_enhanced import HVBValidator
from validators.coba_validator_enhanced import CoBaValidator
import utils
import pandas as pd

# --- ULTRA-READABLE CSS ---
READABLE_STYLE = """
<style>
    /* Input Fields - DUNKELBLAU */
    .stTextInput input, .stTextArea textarea {
        color: #003d7a !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        background: white !important;
        border: 2px solid #0066cc !important;
    }
    
    /* Labels - SCHWARZ */
    .stTextInput label, .stTextArea label {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }
    
    /* Metrics - DUNKELBLAU & GROSS */
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        color: #003d7a !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }
    
    /* Headers - SCHWARZ */
    h1, h2, h3 {
        color: #000000 !important;
        font-weight: bold !important;
        margin-bottom: 10px !important;
        margin-top: 10px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #0066cc !important;
        font-weight: bold !important;
        border-bottom: 4px solid #0066cc !important;
    }
    
    /* DataFrames - DUNKELBLAU */
    .dataframe th {
        background: #003d7a !important;
        color: white !important;
        font-weight: bold !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        color: #003d7a !important;
        font-weight: 600 !important;
        padding: 10px !important;
    }
    
    /* Selectbox - DUNKELBLAU */
    .stSelectbox select {
        color: #003d7a !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* Validation Checklist Styling */
    .check-ok {
        color: #00aa00;
        font-size: 20px;
        font-weight: bold;
    }
    
    .check-fail {
        color: #cc0000;
        font-size: 20px;
        font-weight: bold;
    }
    
    .check-skip {
        color: #999999;
        font-size: 20px;
    }
    
    .element-container {
        margin-bottom: 0.5rem !important;
    }
</style>
"""

# --- SETUP ---
st.set_page_config(
    page_title="ISO Payment Validator | KTC", 
    page_icon="📋", 
    layout="wide"
)
st.markdown(READABLE_STYLE, unsafe_allow_html=True)

XSD_PATH = "schemas/pain.001.001.09.xsd"

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("KTC_Logo_blauer_Hintergrund.png", width=150)
    except:
        st.markdown("🏢")
    
    st.markdown("### ⚙️ Einstellungen")
    bank = st.selectbox("Hausbank Profil", ["HypoVereinsbank", "Commerzbank"])
    
    if bank == "HypoVereinsbank":
        validator = HVBValidator(XSD_PATH)
    else:
        validator = CoBaValidator(XSD_PATH)
        
    st.divider()
    st.caption("📌 **ISO 20022 Payment Validator**")
    st.caption("v2.8 | Enhanced Validation | KTC")

# --- HEADER ---
st.title("📋 ISO 20022 Payment Validator")
st.caption(f"**KTC Treasury Consulting** | Aktives Profil: **{bank}**")

uploaded_file = st.file_uploader("📂 Zahlungsdatei (pain.001.001.09 XML)", type=["xml"])

if uploaded_file:
    xml_bytes = uploaded_file.read()
    
    validator.validate(xml_bytes)
    profile_name, profile_desc = validator.get_profile_info()
    data = utils.parse_payment_data(xml_bytes)
    
    checks_summary = validator.get_checks_summary()

    # --- TABS ---
    tab_check, tab_payment, tab_rules, tab_xml = st.tabs([
        "✅ Validierung", 
        "💳 Zahlungen",
        "📜 Regeln",
        "📄 XML"
    ])

    # ========== TAB 1: VALIDIERUNG (NEU!) ==========
    with tab_check:
        st.markdown("## 🔍 Validierungs-Checkliste")
        
        # Gesamtstatus
        total_checks = len(validator.checks)
        passed_checks = len([c for c in validator.checks.values() if c['status'] is True])
        failed_checks = len([c for c in validator.checks.values() if c['status'] is False])
        skipped_checks = len([c for c in validator.checks.values() if c['status'] is None])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gesamt", total_checks)
        col2.metric("✅ Bestanden", passed_checks)
        col3.metric("❌ Fehlgeschlagen", failed_checks)
        col4.metric("⚪ Übersprungen", skipped_checks)
        
        st.markdown("---")
        
        # Level 1: Technische Prüfungen
        st.markdown("### 🔧 Level 1: Technische Validierung (XSD)")
        
        for check in checks_summary['technical']:
            status_icon = "✅" if check['status'] is True else "❌" if check['status'] is False else "⚪"
            status_class = "check-ok" if check['status'] is True else "check-fail" if check['status'] is False else "check-skip"
            
            col_icon, col_name = st.columns([1, 9])
            col_icon.markdown(f'<span class="{status_class}">{status_icon}</span>', unsafe_allow_html=True)
            col_name.markdown(f"**{check['name']}**")
        
        st.markdown("---")
        
        # Level 2: SEPA Standard
        st.markdown("### 🇪🇺 Level 2: SEPA Standard (Generisch)")
        
        for check in checks_summary['sepa']:
            status_icon = "✅" if check['status'] is True else "❌" if check['status'] is False else "⚪"
            status_class = "check-ok" if check['status'] is True else "check-fail" if check['status'] is False else "check-skip"
            
            col_icon, col_name = st.columns([1, 9])
            col_icon.markdown(f'<span class="{status_class}">{status_icon}</span>', unsafe_allow_html=True)
            col_name.markdown(f"**{check['name']}**")
        
        st.markdown("---")
        
        # Level 3: Bank-Spezifisch
        st.markdown(f"### 🏦 Level 3: Bank-Spezifisch ({bank})")
        
        if checks_summary['bank']:
            for check in checks_summary['bank']:
                status_icon = "✅" if check['status'] is True else "❌" if check['status'] is False else "⚪"
                status_class = "check-ok" if check['status'] is True else "check-fail" if check['status'] is False else "check-skip"
                
                col_icon, col_name = st.columns([1, 9])
                col_icon.markdown(f'<span class="{status_class}">{status_icon}</span>', unsafe_allow_html=True)
                col_name.markdown(f"**{check['name']}**")
        else:
            st.info("ℹ️ Keine bankspezifischen Prüfungen konfiguriert")
        
        st.markdown("---")
        
        # Fehler-Details
        if validator.errors:
            st.markdown("### 📋 Fehler-Details")
            
            errs = [e for e in validator.errors if e['level'] in ['CRITICAL','ERROR']]
            warns = [e for e in validator.errors if e['level'] == 'WARNING']
            
            if errs:
                st.markdown(f"#### ❌ Fehler ({len(errs)})")
                for e in errs:
                    with st.expander(f"🛑 Zeile {e['line']}: {e['title']}", expanded=False):
                        st.error(e['msg'])
                        if e.get('tag') and e['tag'] != 'Unbekannt': 
                            st.code(f"<{e['tag']}>")
            
            if warns:
                st.markdown(f"#### ⚠️ Warnungen ({len(warns)})")
                for e in warns:
                    with st.expander(f"⚠️ Zeile {e['line']}: {e['title']}", expanded=False):
                        st.warning(e['msg'])
                        if e.get('tag') and e['tag'] != 'Unbekannt': 
                            st.code(f"<{e['tag']}>")
        else:
            st.success("🎉 **Keine Fehler gefunden - Datei ist vollständig korrekt!**")

    # ========== TAB 2: ZAHLUNGEN ==========
    with tab_payment:
        if data:
            for batch_idx, b in enumerate(data['batches'], 1):
                
                st.markdown(f"### 📦 Sammler {batch_idx}")
                
                # Header Info
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Transaktionen", len(b['txs']))
                c2.metric("Summe", f"{b.get('ctrl_sum', '-')}")
                c3.metric("Währung", b.get('ccy', 'EUR'))
                c4.metric("Datum", b['date'])
                c5.metric("Zahlweg", "SEPA CT")
                
                # Auftraggeber
                st.markdown("**👤 Auftraggeber**")
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.text_input("Name", b['dbtr'], key=f"d_name_{batch_idx}", label_visibility="collapsed")
                col2.text_input("IBAN", b['iban'], key=f"d_iban_{batch_idx}", label_visibility="collapsed")
                col3.text_input("Ref", b['id'][:15], key=f"d_ref_{batch_idx}", label_visibility="collapsed")
                
                st.markdown("---")
                
                # Transaktionen
                st.markdown("**💸 Transaktionen**")
                
                if b['txs']:
                    tx_list = []
                    for idx, tx in enumerate(b['txs'], 1):
                        tx_list.append({
                            "#": idx,
                            "Empfänger": tx['cdtr'][:35],
                            "IBAN": tx['cdtr_iban'],
                            "Betrag": f"{tx['amt']} {tx['ccy']}",
                            "Referenz (E2E)": tx['e2e'][:20],
                            "Verwendungszweck": tx['rmt'][:50] + "..." if len(tx['rmt']) > 50 else tx['rmt']
                        })
                    
                    df = pd.DataFrame(tx_list)
                    st.dataframe(df, use_container_width=True, hide_index=True, height=min(400, len(tx_list) * 45 + 50))
                    
                    # Detail-Ansicht
                    with st.expander("🔍 Transaktion im Detail anzeigen", expanded=False):
                        sel = st.selectbox(
                            "Transaktion wählen:",
                            range(1, len(b['txs']) + 1),
                            format_func=lambda x: f"#{x}: {b['txs'][x-1]['cdtr']} - {b['txs'][x-1]['amt']} {b['txs'][x-1]['ccy']}",
                            key=f"sel_{batch_idx}"
                        )
                        
                        tx = b['txs'][sel - 1]
                        
                        d1, d2 = st.columns(2)
                        with d1:
                            st.text_input("Empfänger", tx['cdtr'], key=f"t_cdtr_{batch_idx}_{sel}")
                            st.text_input("IBAN", tx['cdtr_iban'], key=f"t_iban_{batch_idx}_{sel}")
                            st.text_input("Betrag", f"{tx['amt']} {tx['ccy']}", key=f"t_amt_{batch_idx}_{sel}")
                        
                        with d2:
                            st.text_input("E2E Referenz", tx['e2e'], key=f"t_e2e_{batch_idx}_{sel}")
                            if tx.get('cdtr_bic') and tx['cdtr_bic'] != '-':
                                st.text_input("BIC", tx['cdtr_bic'], key=f"t_bic_{batch_idx}_{sel}")
                        
                        st.text_area("Verwendungszweck", tx['rmt'], height=70, key=f"t_rmt_{batch_idx}_{sel}")
                
                if batch_idx < len(data['batches']):
                    st.markdown("---")
        else:
            st.error("❌ Datei konnte nicht geparst werden.")

    # ========== TAB 3: REGELN ==========
    with tab_rules:
        st.markdown(f"## 📜 {profile_name}")
        st.markdown(profile_desc)

    # ========== TAB 4: XML ==========
    with tab_xml:
        st.markdown("### 📄 XML Quelltext")
        if validator.errors:
            st.caption("🔴 Fehler sind rot markiert.")
        
        html_view = utils.render_highlighted_xml(xml_bytes, validator.errors)
        st.markdown(html_view, unsafe_allow_html=True)
