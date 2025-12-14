from .base_validator import BaseValidator
import re

class HVBValidator(BaseValidator):
    
    def get_profile_info(self):
        return "HypoVereinsbank (UniCredit)", """
        **Bekannte Abweichungen / Regeln:**
        - 📄 **Referenzen:** Keine Slashes (/) am Anfang/Ende (PDF S. 54)
        - ⚡ **Eilzahlungen:** Müssen ServiceLevel `URGP` haben und `UETR` enthalten (PDF S. 72)
        - 🏠 **Adressen:** Warnung vor unstrukturierten Adressen (Migration 2025)
        """

    def _check_business_rules(self, tree):
        # REGEL 1: Slashes
        forbidden_slash = r'^/|/$|//'
        checks = [('//pain:MsgId', 'Message-ID'), ('//pain:PmtInfId', 'PmtInf-ID'), ('//pain:EndToEndId', 'E2E-ID')]
        
        for xpath, title in checks:
            for elem in tree.xpath(xpath, namespaces=self.ns):
                if elem.text and re.search(forbidden_slash, elem.text):
                    self.add_error(elem, "ERROR", "Format-Fehler (HVB)", f"'{title}' enthält unerlaubte Slashes.")

        # REGEL 2: Eilzahlungen
        for pmt in tree.xpath('//pain:PmtInf', namespaces=self.ns):
            svc_lvl = pmt.find('.//pain:SvcLvl/pain:Cd', self.ns)
            if svc_lvl is not None and svc_lvl.text == 'URGP':
                txs = pmt.findall('.//pain:CdtTrfTxInf', self.ns)
                for tx in txs:
                    uetr = tx.find('.//pain:PmtId/pain:UETR', self.ns)
                    if uetr is None:
                        # Wir markieren den ganzen Transaktions-Block
                        self.add_error(tx, "WARNING", "Eilzahlung (HVB)", "Urgent Payment (URGP) ohne UETR gefunden.")

        # REGEL 3: Adressen
        for adr in tree.xpath('//pain:AdrLine', namespaces=self.ns):
            self.add_error(adr, "WARNING", "Migration 2025", "Unstrukturierte Adresse (<AdrLine>) gefunden.")
