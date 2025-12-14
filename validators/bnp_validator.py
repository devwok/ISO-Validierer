import xmlschema
from lxml import etree
import re
import io

class HVBValidator:
    def __init__(self, xsd_path):
        self.xsd_path = xsd_path
        self.errors = []
        self.ns = {'pain': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}

    def validate(self, xml_content):
        self.errors = []
        
        # 1. XSD Schema Prüfung
        try:
            schema = xmlschema.XMLSchema(self.xsd_path)
            if not schema.is_valid(io.BytesIO(xml_content)):
                for error in schema.iter_errors(io.BytesIO(xml_content)):
                    readable_msg = self._translate_xsd_error(error)
                    self.errors.append({"level": "CRITICAL", "title": "Struktur-Fehler (Schema)", "msg": readable_msg})
                return False 
        except Exception as e:
            self.errors.append({"level": "CRITICAL", "title": "System-Fehler", "msg": f"XSD defekt: {e}"})
            return False

        # 2. Bank-Spezifische Regeln
        try:
            tree = etree.fromstring(xml_content)
            self._check_hvb_rules(tree)
        except Exception as e:
            self.errors.append({"level": "CRITICAL", "title": "Parsing Fehler", "msg": str(e)})
        
        return len(self.errors) == 0

    def _translate_xsd_error(self, error):
        """Übersetzt technische Fehler intelligent ins Deutsche"""
        msg = str(error.message)
        
        # 1. Den Feldnamen mit Regex extrahieren (Das ist der Fix!)
        # Wir suchen nach dem Muster: }Feldname'  oder }Feldname>
        match = re.search(r"\}?([a-zA-Z0-9]+)['>]", msg)
        
        if match:
            raw_tag = match.group(1) # Das ist z.B. "ReqdExctnDt"
        else:
            raw_tag = "Unbekanntes Feld"

        # 2. Übersetzungstabelle (Erweitern nach Bedarf)
        translations = {
            "GrpHdr": "Gruppenkopf (Header)",
            "PmtInf": "Zahlungsinformation (Block)",
            "PmtInfId": "Referenznummer",
            "CdtTrfTxInf": "Einzel-Transaktion",
            "ReqdExctnDt": "Ausführungsdatum",
            "Dt": "Datum",
            "DtTm": "Datum & Uhrzeit",
            "Dbtr": "Auftraggeber",
            "Cdtr": "Empfänger",
            "IBAN": "IBAN",
            "EndToEndId": "End-to-End-ID",
            "Ustrd": "Verwendungszweck",
            "Amt": "Betrag",
            "InstdAmt": "Betrag",
            "MndtId": "Mandatsreferenz",
            "DrctDbtTxInf": "Lastschrift-Transaktion"
        }
        
        # Den schönen Namen holen (oder den technischen behalten, falls nicht in Liste)
        nice_name = translations.get(raw_tag, raw_tag)

        # 3. Fehlerursache erklären
        if "model='choice'" in msg:
            return f"Fehler in '{nice_name}': Hier ist eine Auswahl nötig (z.B. Datum ODER Datum+Uhrzeit), aber das Format passt nicht."
        
        if "model='sequence'" in msg:
            return f"Fehler in '{nice_name}': Die Struktur ist unvollständig. Ein Pflichtfeld fehlt oder die Reihenfolge ist falsch."
        
        if "missing required attribute" in msg:
            return f"Fehler in '{nice_name}': Ein technisches Attribut fehlt (z.B. Währung 'Ccy')."
            
        if "unexpected child" in msg:
            return f"Fehler in '{nice_name}': Dieses Feld darf hier nicht stehen (oder es steht an der falschen Stelle)."

        if "value is not a valid" in msg:
            return f"Fehler in '{nice_name}': Der Wert ist ungültig (falsches Format oder unerlaubte Zeichen)."

        # Fallback: Wenn wir es nicht genau wissen, geben wir eine saubere Version zurück
        clean_msg = msg.replace("{urn:iso:std:iso:20022:tech:xsd:pain.001.001.09}", "")
        return f"Detailfehler in '{nice_name}': {clean_msg}"

    def _check_hvb_rules(self, tree):
        # ... (Dieser Teil bleibt gleich wie vorher) ...
        # (Kopiere hier den Rest der _check_hvb_rules Funktion aus dem vorherigen Code rein, 
        # oder lass ihn stehen, wenn du nur die translate-Funktion getauscht hast)
        
        forbidden_slash = r'^/|/$|//'
        # ... (Rest der Regeln) ...
        for pmt in tree.xpath('//pain:PmtInf', namespaces=self.ns):
             # ... (Dummy Platzhalter, damit Code valide bleibt beim Kopieren)
             pass
