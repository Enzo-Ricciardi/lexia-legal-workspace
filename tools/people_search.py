import httpx
from datetime import datetime
from typing import Dict, Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# NOTA TECNICA SUL MODULO DI VERIFICA SOLVIBILITÀ
# ─────────────────────────────────────────────────────────────────────────────
# I dati reali su pregiudizievoli (ipoteche, pignoramenti, procedure
# concorsuali) e visure camerali (CCIAA / InfoCamere) NON sono disponibili
# tramite API pubblica gratuita senza credenziali professionali.
#
# Fonti ufficiali integrabili (richiedono registrazione e/o costi):
#   - InfoCamere / Registro Imprese  →  https://www.registroimprese.it
#   - Openapi.it (Visure, Pregiudizievoli, Protesti)  →  https://openapi.it
#   - Agenzia delle Entrate / Sister  →  accesso per professionisti abilitati
#
# Dato GRATUITO e UFFICIALE disponibile:
#   - Verifica P.IVA tramite il sistema VIES della Commissione Europea.
#     Endpoint: https://ec.europa.eu/taxation_customs/vies/rest-api/ms/IT/vat/{piva}
#     Restituisce: denominazione, indirizzo e stato di validità intracomunitaria.
#
# Il motore configura un token Openapi.it nella sezione Impostazioni
# (campo "openapi_token") per sbloccare le verifiche complete.
# ─────────────────────────────────────────────────────────────────────────────

VIES_API_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/ms/IT/vat/{vat}"

def _clean_vat(vat: str) -> str:
    """Normalizes a VAT/P.IVA number removing IT prefix, spaces and dashes."""
    cleaned = vat.strip().upper()
    if cleaned.startswith("IT"):
        cleaned = cleaned[2:]
    return "".join(c for c in cleaned if c.isdigit())


def _check_vies(vat: str) -> Dict[str, Any]:
    """
    Checks the validity of an Italian P.IVA against the EU VIES system.
    Returns a dict with keys: valid, name, address, requestDate, errorMessage.
    """
    clean = _clean_vat(vat)
    if not clean or len(clean) != 11:
        return {
            "valid": None,
            "name": None,
            "address": None,
            "requestDate": None,
            "errorMessage": "Formato P.IVA non valido (attesi 11 cifre)"
        }
    try:
        url = VIES_API_URL.format(vat=clean)
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "valid": data.get("isValid", False),
                    "name": data.get("name", "Non disponibile"),
                    "address": data.get("address", "Non disponibile"),
                    "requestDate": data.get("requestDate"),
                    "errorMessage": None
                }
            else:
                return {
                    "valid": None,
                    "name": None,
                    "address": None,
                    "requestDate": None,
                    "errorMessage": f"Servizio VIES non raggiungibile (HTTP {resp.status_code})"
                }
    except Exception as exc:
        return {
            "valid": None,
            "name": None,
            "address": None,
            "requestDate": None,
            "errorMessage": f"Errore di connessione al VIES: {exc}"
        }


def _check_openapi(name: str, tax_code: str, vat: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Queries Openapi.it for CCIAA / pregiudizievoli data if a token is configured.
    Returns None if no token is set, a dict with real data otherwise.
    """
    if not token:
        return None
    try:
        clean_vat = _clean_vat(vat) if vat else ""
        cf = tax_code.strip() if tax_code else ""
        identifier = clean_vat or cf
        if not identifier:
            return None

        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.openapi.it/v1/impresa/{identifier}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return None
    except Exception:
        return None


class PeopleSearchEngine:
    @classmethod
    def search_data(
        cls,
        name: str,
        tax_code: str = "",
        vat: str = "",
        address: str = "",
        openapi_token: str = ""
    ) -> Dict[str, Any]:
        """
        Performs real public registry checks on physical or legal entities.

        Available verifications (depending on input and configured credentials):
          • VIES EU (gratuito): verifica validità P.IVA per operazioni intracomunitarie
          • Openapi.it (token richiesto): visure CCIAA, pregiudizievoli, procedure concorsuali
        """
        now = datetime.now().isoformat()
        is_company = bool(vat) or any(
            kw in name.lower() for kw in ["s.r.l.", "s.p.a.", "s.n.c.", "s.a.s.", "spa", "srl"]
        )

        # ── VIES check (free, real data) ──────────────────────────────────────
        vies_result = None
        if vat:
            vies_result = _check_vies(vat)

        # ── Openapi.it check (requires token, real data) ─────────────────────
        openapi_result = _check_openapi(name, tax_code, vat, openapi_token)

        # ── Assemble the report ───────────────────────────────────────────────
        registries: Dict[str, str] = {}

        # VIES
        if vies_result:
            if vies_result["errorMessage"]:
                registries["VIES – Commissione Europea"] = (
                    f"⚠️ {vies_result['errorMessage']}"
                )
            elif vies_result["valid"] is True:
                registries["VIES – Commissione Europea"] = (
                    f"✅ P.IVA VALIDA per operazioni intracomunitarie\n"
                    f"  Denominazione registrata: {vies_result['name']}\n"
                    f"  Sede registrata: {vies_result['address']}\n"
                    f"  Data verifica VIES: {vies_result['requestDate']}"
                )
            elif vies_result["valid"] is False:
                registries["VIES – Commissione Europea"] = (
                    "❌ P.IVA NON VALIDA o non abilitata per operazioni intracomunitarie"
                )
            else:
                registries["VIES – Commissione Europea"] = (
                    "⚠️ Verifica VIES non conclusiva"
                )
        else:
            registries["VIES – Commissione Europea"] = (
                "ℹ️ Nessuna P.IVA fornita – verifica non eseguita"
            )

        # Openapi.it / CCIAA
        if openapi_result:
            stato_cc = openapi_result.get("statoRegistro") or openapi_result.get("stato") or "n/d"
            registries["Camera di Commercio (Openapi.it)"] = (
                f"Stato: {stato_cc}\n"
                f"  Dati raw: {str(openapi_result)[:300]}"
            )
            pregiudizievoli_raw = openapi_result.get("pregiudizievoli") or openapi_result.get("ipoteche")
            if pregiudizievoli_raw is not None:
                registries["Pregiudizievoli / Ipoteche (Openapi.it)"] = str(pregiudizievoli_raw)
        else:
            if openapi_token:
                registries["Camera di Commercio / Pregiudizievoli"] = (
                    "⚠️ Dati non recuperati – verificare token Openapi.it nelle Impostazioni"
                )
            else:
                registries["Camera di Commercio / Pregiudizievoli"] = (
                    "🔑 VERIFICA NON ESEGUITA – Richiede token Openapi.it\n"
                    "  Configurare il campo 'openapi_token' in Impostazioni per accedere a:\n"
                    "  • Visure camerali (CCIAA / InfoCamere)\n"
                    "  • Pregiudizievoli (ipoteche, pignoramenti, sequestri)\n"
                    "  • Protesti e procedure concorsuali\n"
                    "  Sito: https://openapi.it  –  costo medio: ~€3,90/visura"
                )

        # Determine overall status from available real data
        status = "DATI PARZIALI – verifica completa richiede credenziali professionali"
        if vies_result and vies_result.get("valid") is True and not openapi_result:
            status = "P.IVA VALIDA (VIES) – Pregiudizievoli non verificati (token mancante)"
        elif vies_result and vies_result.get("valid") is False:
            status = "ATTENZIONE – P.IVA non valida o non attiva nel VIES"
        elif openapi_result:
            stato_op = openapi_result.get("statoRegistro") or ""
            if "attiv" in stato_op.lower():
                status = "ATTIVO – dati da Registro Imprese (Openapi.it)"
            elif "liquid" in stato_op.lower() or "cancel" in stato_op.lower():
                status = "ATTENZIONE – Impresa in liquidazione o cancellata"
            else:
                status = f"Stato: {stato_op}" if stato_op else status

        # Score only if we have real data
        if vies_result and vies_result.get("valid") is True:
            score = "VERIFICATO PARZIALMENTE (VIES OK)"
        elif vies_result and vies_result.get("valid") is False:
            score = "ATTENZIONE – P.IVA NON VALIDA"
        else:
            score = "NON DETERMINABILE – inserire P.IVA e/o token Openapi.it"

        # Use VIES name/address as canonical if available and not superseded by openapi
        canonical_name = (
            (vies_result or {}).get("name") or name or "Non fornito"
        )
        canonical_address = (
            (vies_result or {}).get("address") or address or "Non fornito"
        )
        # Prefer user-supplied name if VIES returned "---" (sometimes it masks it)
        if canonical_name in ("---", "***", ""):
            canonical_name = name or "Non fornito"

        report = {
            "soggetto": {
                "denominazione_o_nome": name,
                "denominazione_verificata": canonical_name,
                "codice_fiscale": tax_code or "Non fornito",
                "partita_iva": vat or "Non fornito",
                "indirizzo": canonical_address,
            },
            "verifica_data": now,
            "stato_soggetto": status,
            "registri_consultati": registries,
            "score_solvibilita": score,
            "vies_raw": vies_result,
            "openapi_raw": openapi_result,
            "note_operative": (
                "I dati VIES provengono dal sistema ufficiale della Commissione Europea "
                "(ec.europa.eu). Per pregiudizievoli e visure CCIAA complete è necessario "
                "configurare un token Openapi.it nelle Impostazioni di LexIA."
            )
        }
        return report

    @classmethod
    def generate_markdown_report(cls, data: Dict[str, Any]) -> str:
        s = data["soggetto"]
        regs = data["registri_consultati"]

        md = f"# Relazione Investigativa – {s['denominazione_o_nome']}\n"
        md += f"**Data Verifica:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"

        md += "## Dati del Soggetto\n"
        md += f"- **Denominazione richiesta**: {s['denominazione_o_nome']}\n"
        md += f"- **Denominazione verificata (VIES/registro)**: {s['denominazione_verificata']}\n"
        md += f"- **Codice Fiscale**: {s['codice_fiscale']}\n"
        md += f"- **Partita IVA**: {s['partita_iva']}\n"
        md += f"- **Sede / Indirizzo verificato**: {s['indirizzo']}\n\n"

        md += "## Stato di Solvibilità e Rischio\n"
        md += f"- **Stato Soggetto**: **{data['stato_soggetto']}**\n"
        md += f"- **Score di Solvibilità**: **{data['score_solvibilita']}**\n\n"

        md += "## Esito Verifiche Registri Pubblici\n"
        for reg, status in regs.items():
            # Handle multiline status (show as blockquote)
            lines = status.split("\n")
            md += f"### {reg}\n"
            for line in lines:
                md += f"{line.strip()}\n"
            md += "\n"

        md += "---\n"
        md += f"> ℹ️ **Nota operativa**: {data['note_operative']}\n\n"
        md += "*Report generato da LexIA – Suite Investigativa.*\n"
        return md
