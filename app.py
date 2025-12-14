import streamlit as st
from validators.hvb_validator import HVBValidator
from validators.coba_validator import CoBaValidator
import utils
import pandas as pd

# --- SETUP ---
st.set_page_config(page_title="ISO Payment Cockpit", page_icon="💶", layout="wide")
XSD_PATH = "schemas/pain.001.001.09.xsd"

# --- SIDEBAR ---
with st.sidebar:
    st.header("Konfiguration")
    bank = st.selectbox("Hausbank Profil", ["HypoVereinsbank", "Commerzbank"])
    
    if bank == "HypoVereinsbank":
        validator = HVBValidator(XSD_PATH)
    else:
        validator = CoBaValidator(XSD_PATH)
        
    st.divider()
    st.info("v2.3 Enhanced | Improved UI")

# --- MAIN ---
st.title(f"🌍 ISO Payment Cockpit: {bank}")
uploaded_file = st.file_uploader("Zahlungsdatei (XML) hier ablegen", type=["xml"])

if uploaded_file:
    xml_bytes = uploaded_file.read()
    
    # 1. Validieren
    validator.validate(xml_bytes)
    profile_name, profile_desc = validator.get_profile_info()
    
    # 2. Parsen
    data = utils.parse_payment_data(xml_bytes)

    # --- TABS ---
    tab_check, tab_view, tab_rules, tab_xml = st.tabs([
        "🔍 Prüfung & Protokoll", 
        "💳 Zahlungs-Maske", 
        "📜 Bank-Regeln",
        "📄 XML Analyse"
    ])

    # TAB 1: PROTOKOLL
    with tab_check:
        st.subheader("Validierungs-Ergebnis")
        if not validator.errors:
            st.success("✅ **Datei ist technisch und fachlich korrekt.**")
        else:
            errs = [e for e in validator.errors if e['level'] in ['CRITICAL','ERROR']]
            warns = [e for e in validator.errors if e['level'] == 'WARNING']
            c1, c2 = st.columns(2)
            c1.metric("Fehler", len(errs))
            c2.metric("Warnungen", len(warns))
            st.divider()
            for e in validator.errors:
                icon = "🛑" if e['level'] == 'CRITICAL' else "🟠" if e['level'] == 'ERROR' else "⚠️"
                with st.expander(f"{icon} Zeile {e['line']}: {e['title']}", expanded=True):
                    st.write(e['msg'])
                    if e.get('tag'): st.code(f"Tag: <{e['tag']}>")

    # TAB 2: ZAHLUNGS-MASKE (VERBESSERT)
    with tab_view:
        if data:
            h = data['header']
            
            # HEADER SECTION - Kompakt mit XML-Tags
            st.markdown("### 📋 Nachrichtenkopf (GrpHdr)")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Nachrichten-ID (MsgId)", h['id'])
            with col2:
                st.metric("Erstellungsdatum (CreDtTm)", h['cre_dt'])
            with col3:
                st.metric("Einreicher (InitgPty/Nm)", h['init_pty'])
            with col4:
                st.metric("Anzahl Sammler", len(data['batches']))
            
            st.divider()
            
            # BATCH/SAMMLER SECTION
            for i, b in enumerate(data['batches'], 1):
                st.markdown(f"### 📦 Sammler {i} / Payment Information")
                
                # Sammler-Header in 2 Spalten
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.markdown("#### 👤 Auftraggeber (Debtor)")
                    st.info(f"""
**Name (Dbtr/Nm):**  
`{b['dbtr']}`

**IBAN (DbtrAcct/Id/IBAN):**  
`{b['iban']}`

**BIC (DbtrAgt/FinInstnId/BICFI):**  
`{b.get('bic', '-')}`
                    """)
                
                with col_right:
                    st.markdown("#### 📅 Ausführungsdetails")
                    st.success(f"""
**Sammler-ID (PmtInfId):**  
`{b['id']}`

**Ausführungsdatum (ReqdExctnDt):**  
`{b['date']}`

**Anzahl Transaktionen (NbOfTxs):**  
`{len(b['txs'])}`

**Gesamtbetrag (CtrlSum):**  
`{b.get('ctrl_sum', '-')} {b.get('ccy', 'EUR')}`
                    """)
                
                # TRANSAKTIONEN als Tabelle
                st.markdown(f"#### 💸 Transaktionen ({len(b['txs'])} Stück)")
                
                if b['txs']:
                    # DataFrame für bessere Darstellung
                    tx_data = []
                    for idx, tx in enumerate(b['txs'], 1):
                        tx_data.append({
                            "Nr.": idx,
                            "E2E-Referenz\n(EndToEndId)": tx['e2e'],
                            "Empfänger\n(Cdtr/Nm)": tx['cdtr'],
                            "IBAN\n(CdtrAcct/Id/IBAN)": tx['cdtr_iban'],
                            "Betrag\n(InstdAmt)": f"{tx['amt']} {tx['ccy']}",
                            "Verwendungszweck\n(RmtInf/Ustrd)": tx['rmt'][:50] + "..." if len(tx['rmt']) > 50 else tx['rmt'],
                            "Purpose\n(Purp/Cd)": tx.get('purp', '-')
                        })
                    
                    df = pd.DataFrame(tx_data)
                    
                    # Konfigurierbare Tabelle mit Highlighting
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Betrag\n(InstdAmt)": st.column_config.TextColumn(
                                width="medium",
                            ),
                            "Verwendungszweck\n(RmtInf/Ustrd)": st.column_config.TextColumn(
                                width="large",
                            ),
                        }
                    )
                    
                    # Detail-Expander für jede Transaktion
                    with st.expander("🔎 Detail-Ansicht Transaktionen", expanded=False):
                        for idx, tx in enumerate(b['txs'], 1):
                            with st.container(border=True):
                                st.markdown(f"**Transaktion #{idx}**")
                                
                                detail_col1, detail_col2, detail_col3 = st.columns(3)
                                
                                with detail_col1:
                                    st.markdown("**📤 Zahlung**")
                                    st.text(f"E2E-ID (EndToEndId):\n{tx['e2e']}")
                                    st.text(f"Instr-ID (InstrId):\n{tx.get('instr_id', '-')}")
                                    st.text(f"Betrag (InstdAmt):\n{tx['amt']} {tx['ccy']}")
                                
                                with detail_col2:
                                    st.markdown("**👥 Empfänger**")
                                    st.text(f"Name (Cdtr/Nm):\n{tx['cdtr']}")
                                    st.text(f"IBAN (CdtrAcct/Id/IBAN):\n{tx['cdtr_iban']}")
                                    st.text(f"BIC (CdtrAgt/FinInstnId/BICFI):\n{tx.get('cdtr_bic', '-')}")
                                
                                with detail_col3:
                                    st.markdown("**📝 Verwendung**")
                                    st.text_area(
                                        "Zweck (RmtInf/Ustrd):",
                                        tx['rmt'],
                                        height=100,
                                        disabled=True,
                                        key=f"rmt_{i}_{idx}"
                                    )
                                    if tx.get('purp') and tx['purp'] != '-':
                                        st.text(f"Purpose Code (Purp/Cd):\n{tx['purp']}")
                
                # Trennlinie zwischen Sammlern
                if i < len(data['batches']):
                    st.markdown("---")
        else:
            st.error("❌ Datei konnte nicht visualisiert werden (Strukturfehler).")

    # TAB 3: REGELN
    with tab_rules:
        st.subheader("Aktives Profil")
        st.markdown(f"## {profile_name}")
        st.markdown(profile_desc)

    # TAB 4: XML
    with tab_xml:
        st.subheader("Detail-Analyse")
        if validator.errors:
            st.caption("🔴 Fehlerhafte Zeilen sind rot markiert.")
        html_view = utils.render_highlighted_xml(xml_bytes, validator.errors)
        st.markdown(html_view, unsafe_allow_html=True)