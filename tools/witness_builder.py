from datetime import datetime
from typing import Dict, Any

class WitnessDataBuilder:
    @classmethod
    def build_witness(cls, name: str, role: str, contact: str, relevance: str, facts: str) -> Dict[str, Any]:
        """
        Creates a structured dictionary representing a witness details sheet.
        """
        return {
            "nominativo": name,
            "ruolo": role, # es. "Oculare", "De relato", "Tecnico"
            "recapiti": contact,
            "rilevanza_probatoria": relevance,
            "fatti_da_testimoniare": facts,
            "creato_il": datetime.now().isoformat()
        }

    @classmethod
    def generate_markdown(cls, data: Dict[str, Any]) -> str:
        md = f"""# Scheda Testimoniale - {data['nominativo']}
Data Creazione: {datetime.now().strftime('%d/%m/%Y')}

## Generalità e Recapiti
- **Nominativo**: {data['nominativo']}
- **Ruolo / Tipo Teste**: {data['ruolo']}
- **Recapiti / Contatto**: {data['recapiti']}

## Rilevanza Probatoria
**Importanza e pertinenza strategica:**
{data['rilevanza_probatoria']}

## Fatti su cui riferire
**Capitoli di prova / Fatti da testimoniare:**
{data['fatti_da_testimoniare']}

---
*Compilato tramite il modulo Witness Builder di LexIA.*
"""
        return md
