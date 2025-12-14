import xmlschema
from lxml import etree
import io
import re

class BaseValidator:
    def __init__(self, xsd_path):
        self.xsd_path = xsd_path
        self.errors = []
        self.ns = {'pain': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}

    def get_profile_info(self):
        return "Basis Profil", "Keine spezifischen Regeln."

    def validate(self, xml_content):
        self.errors = []
        
        # 1. XSD Prüfung (Technical)
        try:
            schema = xmlschema.XMLSchema(self.xsd_path)
            if not schema.is_valid(io.BytesIO(xml_content)):
                for error in schema.iter_errors(io.BytesIO(xml_content)):
                    # JETZT NEU: Wir holen Tag UND Text
                    tag_name, readable_msg = self._translate_xsd_error(error)
                    
                    self.errors.append({
                        "line": 1,
                        "tag": tag_name, # Hier steht jetzt z.B. 'ReqdExctnDt' statt 'Schema'
                        "level": "CRITICAL", 
                        "title": "Schema-Verletzung", 
                        "msg": readable_msg
                    })
                return False
        except Exception as e:
            self.errors.append({
                "line": 0, "tag": "System", 
                "level": "CRITICAL", "title": "System", "msg": f"XSD Fehler: {e}"
            })
            return False

        # 2. Business Rules (Logical)
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.fromstring(xml_content, parser)
            self._check_business_rules(tree)
        except Exception as e:
            self.errors.append({
                "line": 0, "tag": "XML-Parser", 
                "level": "CRITICAL", "title": "Parsing", "msg": str(e)
            })
        
        return len(self.errors) == 0

    def _check_business_rules(self, tree):
        pass

    def add_error(self, element, level, title, msg):
        line = element.sourceline if element is not None else 0
        tag = etree.QName(element).localname if element is not None else "Unbekannt"
        
        self.errors.append({
            "line": line,
            "tag": tag,
            "level": level,
            "title": title,
            "msg": msg
        })

    def _translate_xsd_error(self, error):
        """Gibt (Tagname, Nachricht) zurück"""
        msg = str(error.message)
        clean_msg = msg.replace("{urn:iso:std:iso:20022:tech:xsd:pain.001.001.09}", "")
        
        # Tag extrahieren
        match = re.search(r"\}?([a-zA-Z0-9]+)['>]", msg)
        tag_name = match.group(1) if match else "Unbekannt"
        
        # Nachricht übersetzen
        if "model='choice'" in msg:
            return tag_name, f"Fehler in <{tag_name}>: Auswahl falsch oder Format ungültig."
        if "model='sequence'" in msg:
            return tag_name, f"Fehler in <{tag_name}>: Reihenfolge falsch oder Pflichtfeld fehlt."
        if "unexpected child" in msg:
            return tag_name, f"Fehler in <{tag_name}>: Dieses Feld darf hier nicht stehen."
        if "value is not a valid" in msg:
            return tag_name, f"Fehler in <{tag_name}>: Ungültiger Wert."
            
        return tag_name, clean_msg
