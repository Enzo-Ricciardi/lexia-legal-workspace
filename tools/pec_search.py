import re
from typing import Dict, List, Any

# Pre-populated PEC directory for common Italian legal and public offices
PEC_DATABASE = {
    # Tribunali
    "tribunale roma": "prot.tribunale.roma@giustiziacert.it",
    "tribunale milano": "prot.tribunale.milano@giustiziacert.it",
    "tribunale torino": "prot.tribunale.torino@giustiziacert.it",
    "tribunale napoli": "prot.tribunale.napoli@giustiziacert.it",
    "tribunale palermo": "prot.tribunale.palermo@giustiziacert.it",
    "tribunale firenze": "prot.tribunale.firenze@giustiziacert.it",
    "tribunale bologna": "prot.tribunale.bologna@giustiziacert.it",
    "tribunale genova": "prot.tribunale.genova@giustiziacert.it",
    "tribunale bari": "prot.tribunale.bari@giustiziacert.it",
    "tribunale venezia": "prot.tribunale.venezia@giustiziacert.it",
    "tribunale cuneo": "prot.tribunale.cuneo@giustiziacert.it",
    
    # Cassazione e procure
    "corte di cassazione": "prot.cassazione@giustiziacert.it",
    "procura della repubblica roma": "prot.procura.roma@giustiziacert.it",
    "procura della repubblica milano": "prot.procura.milano@giustiziacert.it",
    "procura della repubblica torino": "prot.procura.torino@giustiziacert.it",
    
    # Comuni principali
    "comune roma": "protocollo.generale@pec.comune.roma.it",
    "comune milano": "protocollo@pec.comune.milano.it",
    "comune torino": "protocollo.generale@pec.comune.torino.it",
    "comune firenze": "protocollo@pec.comune.fi.it",
    "comune napoli": "protocollo@pec.comune.napoli.it",
    "comune cuneo": "protocollo.comune.cuneo@legalmail.it",
    
    # Enti nazionali
    "agenzia delle entrate": "agenziaentratepec@pce.agenziaentrate.it",
    "inps": "direzionegenerale@postacert.inps.gov.it",
    "inail": "inail@postacert.inail.it",
    "ministero della giustizia": "prot.dag@giustiziacert.it",
    "carabinieri comando generale": "sm.c.urp@pec.carabinieri.it"
}

class PecSearchEngine:
    @classmethod
    def search(cls, query: str) -> Dict[str, Any]:
        """
        Searches the PEC database for a public office matching the query.
        Returns a dictionary with search details and found addresses.
        """
        clean_query = query.lower().strip()
        clean_query = re.sub(r'\s+', ' ', clean_query)
        
        stop_words = {
            'di', 'del', 'della', 'dello', 'dei', 'degli', 'delle', 
            'a', 'al', 'alla', 'allo', 'ai', 'agli', 'alle', 
            'da', 'dal', 'dalla', 'dallo', 'dai', 'dagli', 'dalle',
            'in', 'nel', 'nella', 'nello', 'nei', 'negli', 'nelle',
            'con', 'col', 'coi', 'su', 'sul', 'sulla', 'sullo', 'sui', 'sugli', 'sulle',
            'per', 'tra', 'fra', 'e', 'o', 'd'
        }
        
        def get_keywords(text: str) -> set:
            words = re.findall(r'[a-z0-9]+', text.lower())
            return {w for w in words if w not in stop_words}
            
        query_keywords = get_keywords(clean_query)
        matches = []
        
        if query_keywords:
            for office, pec in PEC_DATABASE.items():
                office_keywords = get_keywords(office)
                common = query_keywords.intersection(office_keywords)
                if common:
                    # Score based on keyword overlap
                    score = len(common) / max(len(query_keywords), len(office_keywords))
                    # Or check if one is fully contained in the other
                    is_contained = query_keywords.issubset(office_keywords) or office_keywords.issubset(query_keywords)
                    if score >= 0.5 or is_contained:
                        matches.append({
                            "ufficio": office.title(),
                            "pec": pec,
                            "fonte": "Indice Interno LexIA",
                            "score": score
                        })
                        
            # Sort matches by score descending
            matches.sort(key=lambda x: x.get("score", 0), reverse=True)
            # Remove score from output structure
            for m in matches:
                m.pop("score", None)
                
        # Fallback heuristic generator if no match is found
        if not matches:
            if "comune" in clean_query:
                # Extract city following "comune"
                parts = clean_query.split("comune")
                city = ""
                if len(parts) > 1:
                    sub_words = [w for w in re.findall(r'[a-z0-9]+', parts[1]) if w not in stop_words]
                    if sub_words:
                        city = sub_words[0]
                if not city:
                    city = "comune"
                
                pec_address = f"protocollo@pec.comune.{city}.it"
                matches.append({
                    "ufficio": f"Comune di {city.title()} (Generato per analogia)",
                    "pec": pec_address,
                    "fonte": "Heuristica Regole di Dominio PA"
                })
            elif "tribunale" in clean_query:
                # Extract city following "tribunale"
                parts = clean_query.split("tribunale")
                city = ""
                if len(parts) > 1:
                    sub_words = [w for w in re.findall(r'[a-z0-9]+', parts[1]) if w not in stop_words]
                    if sub_words:
                        city = sub_words[0]
                if not city:
                    city = "tribunale"
                    
                pec_address = f"prot.tribunale.{city}@giustiziacert.it"
                matches.append({
                    "ufficio": f"Tribunale di {city.title()} (Generato per analogia)",
                    "pec": pec_address,
                    "fonte": "Heuristica Regole di Dominio GiustiziaCert"
                })
            else:
                # Basic domain presumption using keywords if any
                clean_name = "".join(list(query_keywords)) if query_keywords else clean_query.replace(' ', '')
                matches.append({
                    "ufficio": f"Ufficio '{query}' (Indice Generale)",
                    "pec": f"protocollo@{clean_name}.pec.it",
                    "fonte": "Ricerca indiziaria - Dominio presunto"
                })
                
        return {
            "query": query,
            "risultati": matches,
            "totale": len(matches)
        }

    @classmethod
    def generate_report(cls, search_result: Dict[str, Any]) -> str:
        res = search_result["risultati"]
        md = f"# Report Ricerca PEC Uffici Pubblici\n"
        md += f"Chiave di ricerca: *{search_result['query']}*\n\n"
        md += "| Ufficio / Ente Pubblico | Indirizzo PEC | Fonte Informazione |\n"
        md += "| --- | --- | --- |\n"
        for item in res:
            md += f"| {item['ufficio']} | `{item['pec']}` | {item['fonte']} |\n"
            
        md += "\n*Nota: Ricontrollare sempre l'indirizzo PEC sull'Indice Nazionale dei Domicili Digitali (IPA / INI-PEC) prima di procedere con notifiche ex art. 3-bis L. 53/1994.*"
        return md
