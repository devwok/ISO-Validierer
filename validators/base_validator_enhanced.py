import xmlschema
from lxml import etree
import io
import re

class BaseValidator:
    def __init__(self, xsd_path):
        self.xsd_path = xsd_path
        self.errors = []
        self.checks = {
            'xsd_valid': {'status': None, 'name': 'XSD Schema', 'level': 'technical'},
            'xml_wellformed': {'status': None, 'name': 'XML Wohlgeformt', 'level': 'technical'},
            'sepa_currency': {'status': None, 'name': 'SEPA Währung (EUR)', 'level': 'sepa'},
            'sepa_charset': {'status': None, 'name': 'SEPA Zeichensatz', 'level': 'sepa'},
            'iban_format': {'status': None, 'name': 'IBAN Format', 'level': 'sepa'},
            'bic_format': {'status': None, 'name': 'BIC Format', 'level': 'sepa'},
            'amount_positive': {'status': None, 'name': 'Beträge > 0', 'level': 'sepa'},
            'reference_length': {'status': None, 'name': 'Referenz-Längen', 'level': 'sepa'},
            'service_level': {'status': None, 'name': 'Service Level', 'level': 'sepa'},
            'amount_limits': {'status': None, 'name': 'Betragslimits', 'level': 'sepa'},
        }
        self.ns = {'pain': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}
    
    def get_profile_info(self):
        return "Basis", "Standard ISO 20022 Validierung"
    
    def get_checks_summary(self):
        """Gibt Zusammenfassung der Checks zurück für UI"""
        technical = [c for c in self.checks.values() if c['level'] == 'technical']
        sepa = [c for c in self.checks.values() if c['level'] == 'sepa']
        bank = [c for c in self.checks.values() if c['level'] == 'bank']
        
        return {
            'technical': technical,
            'sepa': sepa,
            'bank': bank
        }
    
    def validate(self, xml_content):
        self.errors = []
        tree = None
        
        # 1. XML Wellformed Check
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.fromstring(xml_content, parser)
            self.checks['xml_wellformed']['status'] = True
        except Exception as e:
            self.checks['xml_wellformed']['status'] = False
            self.errors.append({
                "line": 0, 
                "tag": "XML", 
                "level": "CRITICAL", 
                "title": "XML Parsing Fehler", 
                "msg": f"Datei ist nicht wohlgeformt: {str(e)}"
            })
            return False
        
        # 2. XSD Schema Validation
        try:
            schema = xmlschema.XMLSchema(self.xsd_path)
            if schema.is_valid(io.BytesIO(xml_content)):
                self.checks['xsd_valid']['status'] = True
            else:
                self.checks['xsd_valid']['status'] = False
                for error in schema.iter_errors(io.BytesIO(xml_content)):
                    tag, msg = self._translate_xsd_error(error)
                    self.errors.append({
                        "line": 1, 
                        "tag": tag, 
                        "level": "CRITICAL", 
                        "title": "Schema-Fehler", 
                        "msg": msg
                    })
        except Exception as e:
            self.checks['xsd_valid']['status'] = False
            self.errors.append({
                "line": 0, 
                "tag": "System", 
                "level": "CRITICAL", 
                "title": "XSD Validierung", 
                "msg": str(e)
            })
            return False
        
        # 3. SEPA Standard Checks (nur wenn XSD OK)
        if tree is not None and self.checks['xsd_valid']['status']:
            self._check_sepa_standard(tree)
        
        # 4. Business Rules (überschreibbar in Subklassen)
        if tree is not None:
            self._check_business_rules(tree)
        
        return len([e for e in self.errors if e['level'] in ['CRITICAL', 'ERROR']]) == 0
    
    def _check_sepa_standard(self, tree):
        """SEPA Standard Checks - Generisch für alle Banken"""
        
        # 1. Währung Check - Nur EUR erlaubt
        currency_ok = True
        non_eur_found = []
        for amt in tree.xpath('//pain:InstdAmt[@Ccy]', namespaces=self.ns):
            ccy = amt.get('Ccy')
            if ccy != 'EUR':
                currency_ok = False
                non_eur_found.append(ccy)
                self.add_error(
                    amt, 
                    "ERROR", 
                    "SEPA Währung", 
                    f"SEPA erlaubt nur EUR, gefunden: {ccy}"
                )
        
        self.checks['sepa_currency']['status'] = currency_ok
        
        # 2. IBAN Format Check
        iban_ok = True
        for iban_elem in tree.xpath('//pain:IBAN', namespaces=self.ns):
            iban = iban_elem.text.strip() if iban_elem.text else ""
            if not self._validate_iban_format(iban):
                iban_ok = False
                self.add_error(
                    iban_elem, 
                    "ERROR", 
                    "IBAN Format", 
                    f"IBAN Format ungültig: {iban}"
                )
        
        self.checks['iban_format']['status'] = iban_ok
        
        # 3. BIC Format Check
        bic_ok = True
        for bic_elem in tree.xpath('//pain:BICFI', namespaces=self.ns):
            bic = bic_elem.text.strip() if bic_elem.text else ""
            if not self._validate_bic_format(bic):
                bic_ok = False
                self.add_error(
                    bic_elem, 
                    "WARNING", 
                    "BIC Format", 
                    f"BIC Format ungültig: {bic}"
                )
        
        self.checks['bic_format']['status'] = bic_ok
        
        # 4. Beträge > 0
        amount_ok = True
        for amt in tree.xpath('//pain:InstdAmt', namespaces=self.ns):
            try:
                value = float(amt.text.strip() if amt.text else "0")
                if value <= 0:
                    amount_ok = False
                    self.add_error(
                        amt, 
                        "ERROR", 
                        "Betrag ungültig", 
                        f"Betrag muss > 0 sein, gefunden: {value}"
                    )
            except ValueError:
                amount_ok = False
                self.add_error(
                    amt, 
                    "ERROR", 
                    "Betrag ungültig", 
                    f"Betrag ist keine Zahl: {amt.text}"
                )
        
        self.checks['amount_positive']['status'] = amount_ok
        
        # 5. SEPA Zeichensatz (Latin-1 Basic + Erweiterungen)
        charset_ok = True
        sepa_pattern = re.compile(r'^[a-zA-Z0-9/?:().,\'+ \-]*$')
        
        for text_field in tree.xpath('//pain:Ustrd | //pain:EndToEndId | //pain:PmtInfId', namespaces=self.ns):
            text = text_field.text.strip() if text_field.text else ""
            if text and not sepa_pattern.match(text):
                charset_ok = False
                invalid_chars = ''.join(set([c for c in text if not sepa_pattern.match(c)]))
                self.add_error(
                    text_field, 
                    "WARNING", 
                    "SEPA Zeichensatz", 
                    f"Ungültige Zeichen: {invalid_chars} in '{text[:30]}...'"
                )
        
        self.checks['sepa_charset']['status'] = charset_ok
        
        # 6. Referenz-Längen (Max 35 Zeichen)
        ref_ok = True
        for ref in tree.xpath('//pain:EndToEndId | //pain:PmtInfId | //pain:MsgId', namespaces=self.ns):
            text = ref.text.strip() if ref.text else ""
            if len(text) > 35:
                ref_ok = False
                self.add_error(
                    ref, 
                    "ERROR", 
                    "Referenz zu lang", 
                    f"Max. 35 Zeichen erlaubt, gefunden: {len(text)} ('{text[:40]}...')"
                )
        
        self.checks['reference_length']['status'] = ref_ok
        
        # 7. Service Level Check
        svc_ok = True
        valid_service_levels = ['SEPA', 'URGP', 'SDVA', 'NURG']
        
        for svc in tree.xpath('//pain:SvcLvl/pain:Cd', namespaces=self.ns):
            code = svc.text.strip() if svc.text else ""
            if code and code not in valid_service_levels:
                svc_ok = False
                self.add_error(
                    svc, 
                    "WARNING", 
                    "Service Level", 
                    f"Unbekannter Service Level: {code} (Erlaubt: {', '.join(valid_service_levels)})"
                )
        
        self.checks['service_level']['status'] = svc_ok
        
        # 8. Betragslimits (SEPA Instant max 100.000 EUR)
        limit_ok = True
        for pmt in tree.xpath('//pain:PmtInf', namespaces=self.ns):
            svc = pmt.find('.//pain:SvcLvl/pain:Cd', self.ns)
            if svc is not None and svc.text == 'URGP':
                # SEPA Instant (URGP) - Max 100.000 EUR
                for amt in pmt.xpath('.//pain:InstdAmt', namespaces=self.ns):
                    try:
                        value = float(amt.text.strip() if amt.text else "0")
                        if value > 100000:
                            limit_ok = False
                            self.add_error(
                                amt, 
                                "ERROR", 
                                "SEPA Instant Limit", 
                                f"SEPA Instant max. 100.000 EUR, gefunden: {value:,.2f} EUR"
                            )
                    except ValueError:
                        pass
        
        self.checks['amount_limits']['status'] = limit_ok
    
    def _validate_iban_format(self, iban):
        """Validiert IBAN Format (vereinfacht)"""
        # Entferne Leerzeichen
        iban = iban.replace(' ', '').upper()
        
        # IBAN muss 15-34 Zeichen haben
        if len(iban) < 15 or len(iban) > 34:
            return False
        
        # Muss mit 2 Buchstaben beginnen (Ländercode)
        if not iban[:2].isalpha():
            return False
        
        # Dann 2 Prüfziffern
        if not iban[2:4].isdigit():
            return False
        
        # Deutsche IBAN hat genau 22 Zeichen
        if iban[:2] == 'DE' and len(iban) != 22:
            return False
        
        return True
    
    def _validate_bic_format(self, bic):
        """Validiert BIC Format"""
        bic = bic.replace(' ', '').upper()
        
        # BIC muss 8 oder 11 Zeichen haben
        if len(bic) not in [8, 11]:
            return False
        
        # Erste 6 Zeichen müssen Buchstaben sein
        if not bic[:6].isalpha():
            return False
        
        # Zeichen 7-8 sind Länder/Ortscode (Buchstaben oder Ziffern)
        if not bic[6:8].isalnum():
            return False
        
        # Falls 11 Zeichen: Zeichen 9-11 sind Filialcode
        if len(bic) == 11 and not bic[8:11].isalnum():
            return False
        
        return True
    
    def _check_business_rules(self, tree):
        """Bankspezifische Regeln - wird in Subklassen überschrieben"""
        # Markiere Bank-Checks als "nicht durchgeführt" wenn keine Bank-Regeln aktiv
        for check_id, check in self.checks.items():
            if check['level'] == 'bank' and check['status'] is None:
                check['status'] = None  # Grau = nicht durchgeführt
    
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
        msg = str(error.message).replace("{urn:iso:std:iso:20022:tech:xsd:pain.001.001.09}", "")
        match = re.search(r"\}?([a-zA-Z0-9]+)['>]", msg)
        tag = match.group(1) if match else "Unbekannt"
        
        if "model='choice'" in msg: 
            return tag, f"Fehler in <{tag}>: Auswahl falsch oder Format ungültig."
        if "model='sequence'" in msg: 
            return tag, f"Fehler in <{tag}>: Reihenfolge falsch oder Pflichtfeld fehlt."
        
        return tag, msg
