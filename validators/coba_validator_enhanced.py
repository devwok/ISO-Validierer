from .base_validator_enhanced import BaseValidator

class CoBaValidator(BaseValidator):
    def __init__(self, xsd_path):
        super().__init__(xsd_path)
        
        # Platzhalter für künftige Commerzbank-Regeln
        self.checks.update({
            'coba_placeholder1': {'status': None, 'name': 'CoBa: Regel 1', 'level': 'bank'},
            'coba_placeholder2': {'status': None, 'name': 'CoBa: Regel 2', 'level': 'bank'},
        })
    
    def get_profile_info(self):
        return "Commerzbank", """
## Commerzbank Validierungsregeln

### Status
⚠️ **In Entwicklung** - Bankspezifische Regeln werden sukzessive ergänzt

### Geplante Prüfungen
- Referenz-Formate
- Verwendungszweck-Regeln
- Adressanforderungen
- Betragslimits
- Weitere bankspezifische Anforderungen

### Nächste Schritte
1. Commerzbank Dokumentation analysieren
2. Spezifische Regeln identifizieren
3. In Code implementieren
4. Testen & freigeben
"""
    
    def _check_business_rules(self, tree):
        """Commerzbank-spezifische Geschäftsregeln - TODO"""
        
        # Markiere als "nicht durchgeführt" (grau) bis Regeln implementiert sind
        self.checks['coba_placeholder1']['status'] = None
        self.checks['coba_placeholder2']['status'] = None
        
        # TODO: Hier werden später die CoBa-Regeln implementiert
        pass
