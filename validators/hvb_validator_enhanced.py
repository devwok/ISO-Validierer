from .base_validator_enhanced import BaseValidator
import re

class HVBValidator(BaseValidator):
    def __init__(self, xsd_path):
        super().__init__(xsd_path)
        
        # Erweitere Checks um HVB-spezifische Prüfungen
        self.checks.update({
            'hvb_no_slashes': {'status': None, 'name': 'HVB: Keine Slashes', 'level': 'bank'},
            'hvb_urgp_uetr': {'status': None, 'name': 'HVB: URGP mit UETR', 'level': 'bank'},
            'hvb_address_format': {'status': None, 'name': 'HVB: Adressformat', 'level': 'bank'},
        })
    
    def get_profile_info(self):
        return "HypoVereinsbank (HVB)", """
## HypoVereinsbank Validierungsregeln

### Technische Anforderungen
- **pain.001.001.09** (SEPA Credit Transfer)
- **Zeichensatz:** SEPA-konform (Latin-1)
- **Encoding:** UTF-8

### Besondere HVB-Regeln

#### 1. Referenzen (S.54 ZV-Formate-DE.pdf)
- ❌ **Keine Slashes** am Anfang/Ende: `/ABC/`, `ABC/`
- ❌ **Keine doppelten Slashes:** `ABC//DEF`
- ✅ Erlaubt: `ABC/DEF/GHI`
- Betrifft: `MsgId`, `PmtInfId`, `EndToEndId`

#### 2. Eilzahlungen / SEPA Instant (S.72)
- **Service Level:** `URGP`
- **UETR erforderlich:** Unique End-to-End Transaction Reference
- ⚠️ Ohne UETR: Eingeschränktes Tracking

#### 3. Adressformat
- **Strukturierte Adressen** bevorzugt (Straße, PLZ, Ort)
- ⚠️ `AdrLine` (unstrukturiert) wird akzeptiert, aber nicht empfohlen

#### 4. Betragslimits
- **SEPA Standard:** Max. 999.999.999,99 EUR
- **SEPA Instant:** Max. 100.000 EUR
- **Einzelzahlung:** Min. 0,01 EUR

### Referenz
Basierend auf **"ZV-Formate-DE.pdf"** (Stand 2025)
"""
    
    def _check_business_rules(self, tree):
        """HVB-spezifische Geschäftsregeln"""
        
        # 1. Slashes in Referenzen
        slash_ok = True
        for xpath in ['//pain:MsgId', '//pain:PmtInfId', '//pain:EndToEndId']:
            for elem in tree.xpath(xpath, namespaces=self.ns):
                if elem.text and re.search(r'^/|/$|//', elem.text):
                    slash_ok = False
                    self.add_error(
                        elem, 
                        "ERROR", 
                        "HVB: Slash-Regel", 
                        f"'{elem.text}' enthält unerlaubte Slashes (Anfang/Ende oder doppelt)"
                    )
        
        self.checks['hvb_no_slashes']['status'] = slash_ok
        
        # 2. URGP (SEPA Instant) benötigt UETR
        urgp_ok = True
        for pmt in tree.xpath('//pain:PmtInf', namespaces=self.ns):
            svc = pmt.find('.//pain:SvcLvl/pain:Cd', self.ns)
            if svc is not None and svc.text == 'URGP':
                for tx in pmt.findall('.//pain:CdtTrfTxInf', self.ns):
                    uetr = tx.find('.//pain:PmtId/pain:UETR', self.ns)
                    if uetr is None:
                        urgp_ok = False
                        self.add_error(
                            tx, 
                            "WARNING", 
                            "HVB: URGP ohne UETR", 
                            "Eilzahlung (URGP) ohne UETR - Tracking eingeschränkt"
                        )
        
        self.checks['hvb_urgp_uetr']['status'] = urgp_ok
        
        # 3. Adressformat (Warnung bei unstrukturiert)
        addr_ok = True
        adr_lines = tree.xpath('//pain:AdrLine', namespaces=self.ns)
        if adr_lines:
            addr_ok = False  # Nicht kritisch, nur Warnung
            for adr in adr_lines:
                self.add_error(
                    adr, 
                    "WARNING", 
                    "HVB: Adressformat", 
                    "Unstrukturierte Adresse (AdrLine) - Strukturierte Adresse bevorzugt"
                )
        
        self.checks['hvb_address_format']['status'] = addr_ok if not adr_lines else None
