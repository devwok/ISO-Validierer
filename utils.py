import xml.dom.minidom
from lxml import etree
import html
import re

def render_highlighted_xml(xml_bytes, errors):
    """
    Rendert XML mit Syntax-Highlighting und markiert fehlerhafte Zeilen rot
    """
    try:
        xml_str = xml_bytes.decode("utf-8")
        try:
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
        except:
            pretty_xml = xml_str

        error_tags = set([e['tag'] for e in errors if e.get('tag') and e['tag'] != "Unbekannt" and e['tag'] != "System" and e['tag'] != "XML"])
        
        html_output = """<style>
.x-cont { 
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace; 
    font-size: 13px; 
    background: #fafafa; 
    border: 1px solid #ddd; 
    padding: 10px; 
    overflow-x: auto; 
    border-radius: 5px;
} 
.x-line { 
    display: block; 
    white-space: pre; 
    min-height: 1.2em; 
    padding: 2px 5px;
    border-left: 3px solid transparent;
} 
.x-line:hover {
    background: #f0f0f0;
}
.x-err { 
    background: #ffe6e6; 
    border-left: 5px solid #d00; 
    color: #a00; 
    font-weight: bold; 
}
</style><div class="x-cont">"""
        
        for line in pretty_xml.splitlines():
            # Nur Zeilen mit öffnenden oder schließenden Tags der Error-Tags markieren
            is_err = False
            if error_tags:
                for tag in error_tags:
                    # Prüfe auf <tag> oder <tag attribute oder </tag>
                    if re.search(fr'<{tag}[\s>]|</{tag}>', line):
                        is_err = True
                        break
            
            cls = "x-err" if is_err else "x-line"
            safe_line = html.escape(line)
            html_output += f'<div class="{cls}">{safe_line}</div>'
            
        return html_output + "</div>"
    except Exception as e:
        return f"<div style='color: red;'>Rendering-Fehler: {e}</div>"


def parse_payment_data(xml_bytes):
    """
    Parst ISO 20022 pain.001.001.09 XML und extrahiert alle relevanten Daten
    inklusive zusätzlicher Felder für bessere Visualisierung
    """
    data = {
        'header': {
            'id': '-', 
            'cre_dt': '-', 
            'init_pty': '-', 
            'tx_count': '-', 
            'sum': '-'
        }, 
        'batches': []
    }
    
    try:
        root = etree.fromstring(xml_bytes)
        ns = {'pain': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}
        
        # === GROUP HEADER ===
        gh = root.find('pain:GrpHdr', namespaces=ns)
        if gh is not None:
            data['header']['id'] = gh.findtext('pain:MsgId', '-', ns)
            data['header']['cre_dt'] = gh.findtext('pain:CreDtTm', '-', ns)
            data['header']['init_pty'] = gh.findtext('.//pain:InitgPty/pain:Nm', '-', ns)
            data['header']['tx_count'] = gh.findtext('pain:NbOfTxs', '-', ns)
            data['header']['sum'] = gh.findtext('pain:CtrlSum', '-', ns)

        # === PAYMENT INFORMATION (Sammler) ===
        for pmt in root.xpath('//pain:PmtInf', namespaces=ns):
            # Extrahiere Währung aus erstem InstdAmt falls vorhanden
            first_amt = pmt.find('.//pain:InstdAmt', namespaces=ns)
            ccy = first_amt.get("Ccy") if first_amt is not None else "EUR"
            
            batch = {
                'id': pmt.findtext('pain:PmtInfId', '-', ns),
                'date': pmt.findtext('pain:ReqdExctnDt/pain:Dt', '-', ns) or pmt.findtext('pain:ReqdExctnDt', '-', ns),
                'dbtr': pmt.findtext('.//pain:Dbtr/pain:Nm', '-', ns),
                'iban': pmt.findtext('.//pain:DbtrAcct/pain:Id/pain:IBAN', '-', ns),
                'bic': pmt.findtext('.//pain:DbtrAgt/pain:FinInstnId/pain:BICFI', '-', ns),
                'ctrl_sum': pmt.findtext('pain:CtrlSum', '-', ns),
                'nb_of_txs': pmt.findtext('pain:NbOfTxs', '-', ns),
                'ccy': ccy,
                'txs': []
            }
            
            # === CREDIT TRANSFER TRANSACTIONS ===
            for tx in pmt.xpath('.//pain:CdtTrfTxInf', namespaces=ns):
                # Betrag
                amt_node = tx.find('.//pain:Amt/pain:InstdAmt', namespaces=ns)
                amt = amt_node.text if amt_node is not None else "0.00"
                tx_ccy = amt_node.get("Ccy") if amt_node is not None else ccy
                
                # Purpose Code
                purp = tx.findtext('.//pain:Purp/pain:Cd', '-', ns)
                
                # Remittance Info - kann mehrere Ustrd haben
                rmt_info = tx.find('.//pain:RmtInf', namespaces=ns)
                rmt_text = '-'
                if rmt_info is not None:
                    ustrd_list = rmt_info.findall('pain:Ustrd', namespaces=ns)
                    if ustrd_list:
                        rmt_text = ' '.join([u.text for u in ustrd_list if u.text])
                    else:
                        # Fallback auf direktes findtext
                        rmt_text = rmt_info.findtext('pain:Ustrd', '-', ns)
                
                t = {
                    'e2e': tx.findtext('pain:PmtId/pain:EndToEndId', '-', ns),
                    'instr_id': tx.findtext('pain:PmtId/pain:InstrId', '-', ns),
                    'amt': amt, 
                    'ccy': tx_ccy,
                    'cdtr': tx.findtext('.//pain:Cdtr/pain:Nm', '-', ns),
                    'cdtr_iban': tx.findtext('.//pain:CdtrAcct/pain:Id/pain:IBAN', '-', ns),
                    'cdtr_bic': tx.findtext('.//pain:CdtrAgt/pain:FinInstnId/pain:BICFI', '-', ns),
                    'purp': purp if purp != '-' else None,
                    'rmt': rmt_text if rmt_text != '-' else ''
                }
                batch['txs'].append(t)
                
            data['batches'].append(batch)
            
        return data
        
    except Exception as e:
        print(f"Parse Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_amount(amount_str, currency="EUR"):
    """
    Formatiert Beträge für bessere Lesbarkeit
    """
    try:
        amount = float(amount_str)
        return f"{amount:,.2f} {currency}"
    except:
        return f"{amount_str} {currency}"