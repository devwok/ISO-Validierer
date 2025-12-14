from .base_validator import BaseValidator

class CoBaValidator(BaseValidator):
    def get_profile_info(self):
        return "Commerzbank (CoBa)", """
        **Spezifika (Beispiel):**
        - 🌍 **Ausland:** Erweiterte Prüfung auf Ländercodes.
        - 🆔 **IDs:** Maximale Länge 30 Zeichen (HVB hat 35).
        """

    def _check_business_rules(self, tree):
        # Beispiel Regel
        for elem in tree.xpath('//pain:PmtInfId', namespaces=self.ns):
            if elem.text and len(elem.text) > 30:
                self.add_error(elem, "ERROR", "Längen-Fehler (CoBa)", "ID ist länger als 30 Zeichen.")
