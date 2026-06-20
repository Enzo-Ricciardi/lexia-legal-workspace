import os
from datetime import datetime
from typing import Dict, Any

TEMPLATES = {
    "querela": """ALLEGATO: ATTO DI QUERELA-DENUNCIA

ILL.MO SIGNOR PROCURATORE DELLA REPUBBLICA
PRESSO IL TRIBUNALE DI {TRIBUNALE}
(tramite la competente Autorità di Polizia Giudiziaria)

Destinatario: {DESTINATION_NAME}
PEC: {DESTINATION_PEC}
Indirizzo: {DESTINATION_ADDRESS}

Il sottoscritto, {CLIENT_NAME}, nato a {CLIENT_BORN} il {CLIENT_BORN_DATE}, residente in {CLIENT_ADDRESS}, Codice Fiscale {CLIENT_FC}, ed eletto domicilio presso lo studio dell'Avv. {LAWYER_NAME}, con studio in {LAWYER_ADDRESS}, il quale lo rappresenta e difende giusta procura speciale in calce al presente atto, espone quanto segue in ordine ai fatti di cui è stato vittima:

FATTI
{FACTS}

DIRITTO
I fatti sopra esposti integrano chiari ed inequivocabili estremi del reato di cui all'articolo/i {ARTICLES} del Codice Penale, nonché ogni altra fattispecie di reato ravvisabile nei fatti medesimi dall'Ecc.ma Autorità Giudiziaria.

Tutto ciò premesso, il sottoscritto {CLIENT_NAME} come sopra rappresentato e difeso,
SPORGE FORMALE QUERELA-DENUNCIA
contro {OPPONENT_NAME} e contro chiunque altro sia ritenuto responsabile dei fatti descritti, chiedendone la punizione penale ai sensi di legge.
Si formula espressa richiesta di essere informati, ex art. 406, comma 3, c.p.p., di eventuali richieste di proroga delle indagini preliminari, nonché, ex art. 408 c.p.p., di un'eventuale richiesta di archiviazione.

Con riserva di costituzione di parte civile per il risarcimento di tutti i danni subiti e subendi.
Si indicano a prova contraria i seguenti testimoni: {WITNESSES}.

{TRIBUNALE}, lì {DATE}

_______________________
(Firma del Querelante)

_______________________
(Firma Avv. {LAWYER_NAME} per autentica)
""",

    "denuncia": """ALLEGATO: ESPOSIZIONE DI DENUNCIA

ALL'ECC.MA PROCURA DELLA REPUBBLICA
PRESSO IL TRIBUNALE DI {TRIBUNALE}

Destinatario: {DESTINATION_NAME}
PEC: {DESTINATION_PEC}
Indirizzo: {DESTINATION_ADDRESS}

Il sottoscritto, {CLIENT_NAME}, residente in {CLIENT_ADDRESS}, in qualità di {CLIENT_ROLE}, intende denunciare a codesta Autorità Giudiziaria i seguenti fatti di rilevanza penale per i quali si rende necessaria l'apertura di un'indagine:

ESPOSIZIONE DEI FATTI
{FACTS}

Si segnalano i seguenti elementi di riscontro oggettivo e prove documentali: {DOCUMENTS}.
Si indicano quali persone informate sui fatti: {WITNESSES}.

Tutto ciò premesso, si sottopone quanto sopra all'attenzione di codesta Procura per ogni opportuna valutazione, con espressa richiesta di punizione dei colpevoli qualora i fatti integrino reati perseguibili d'ufficio.

{TRIBUNALE}, lì {DATE}

_______________________
(Firma del Denunciante)
""",

    "esposto": """ALLEGATO: ATTO DI ESPOSTO

ALL'ILL.MO SIGNOR QUESTORE DI {TRIBUNALE}
(ovvero al Comando Compagnia Carabinieri di {TRIBUNALE})

Il sottoscritto, {CLIENT_NAME}, residente in {CLIENT_ADDRESS}, espone a codesta Autorità di Pubblica Sicurezza una situazione di dissidio e potenziale turbamento dell'ordine pubblico che richiede un sollecito intervento, eventualmente anche ai fini del tentativo di conciliazione ex art. 1 T.U.L.P.S.

DESCRIZIONE DELLA SITUAZIONE
{FACTS}

La controparte interessata da tale condotta è il Sig. {OPPONENT_NAME}.
Si richiede l'intervento delle Autorità affinché vengano effettuati gli opportuni accertamenti e diffidato il Sig. {OPPONENT_NAME} dal proseguire in condotte moleste o illegittime.

{TRIBUNALE}, lì {DATE}

_______________________
(Firma dell'Espositore)
""",

    "diffida": """ALLEGATO: ATTO DI COSTITUZIONE IN MORA E DIFFIDA AD ADEMPIERE
(Inviata a mezzo Raccomandata A.R. / PEC)

Spett.le
{OPPONENT_NAME}
residente/con sede in {OPPONENT_ADDRESS}

In nome e per conto del Sig. {CLIENT_NAME}, residente in {CLIENT_ADDRESS}, che mi ha conferito espresso mandato professionale, Vi comunico e formulo quanto segue:

La presente è volta a significarVi che ad oggi non avete ancora provveduto a soddisfare la prestazione dovuta relativa a:
{FACTS}

Tale inadempimento arreca grave pregiudizio al mio assistito.
Tutto ciò premesso, con la presente
VI DIFFIDO E COSTITUISCO IN MORA
ai sensi e per gli effetti dell'art. 1219 del Codice Civile, ad adempiere a quanto dovuto entro e non oltre il termine perentorio di 15 (quindici) giorni dal ricevimento della presente.
Con l'espresso avvertimento che, decorso inutilmente tale termine, il contratto s'intenderà risolto di diritto ai sensi dell'art. 1454 c.c. e si procederà senza ulteriore preavviso per le vie giudiziarie per il risarcimento di tutti i danni subiti.

Con ogni riserva di legge.

{TRIBUNALE}, lì {DATE}

_______________________
Avv. {LAWYER_NAME}
""",

    "istanza": """ALLEGATO: ISTANZA DI ACCESSO / PROVVEDIMENTO

ALL'UFFICIO {TRIBUNALE}
{DEPARTMENT}

Il sottoscritto, {CLIENT_NAME}, nato a {CLIENT_BORN} il {CLIENT_BORN_DATE}, residente in {CLIENT_ADDRESS}, in relazione al procedimento n. {PROCEDURAL_NUMBER}, presenta formale istanza al fine di ottenere quanto segue:

OGGETTO DELL'ISTANZA
{FACTS}

A sostegno della presente richiesta si espongono i seguenti motivi di fatto e di diritto:
{LEGAL_REASONS}

Si allega alla presente: {DOCUMENTS}.

{TRIBUNALE}, lì {DATE}

_______________________
(Firma dell'Istante)
""",

    "memoria": """ALLEGATO: MEMORIA ILLUSTRATIVA E DIFENSIVA

TRIBUNALE DI {TRIBUNALE} - SEZIONE {SECTION}
Giudice Dott. {JUDGE} - R.G. {PROCEDURAL_NUMBER}

Per: {CLIENT_NAME}, rappresentato e difeso dall'Avv. {LAWYER_NAME}
Contro: {OPPONENT_NAME}

Il sottoscritto difensore, nell'interesse di {CLIENT_NAME}, deposita la presente memoria illustrativa per chiarire la posizione del proprio assistito in ordine alle risultanze dell'udienza precedente.

DEDUZIONI IN FATTO ED IN DIRITTO
{FACTS}

CONCLUSIONI
Voglia l'Ill.mo Giudice adito, contrariis reiectis:
- Accogliere le eccezioni sollevate;
- Disporre l'ammissione dei mezzi istruttori richiesti, in particolare l'audizione del teste {WITNESSES};
- Rigettare ogni contraria domanda.

Si producono i seguenti documenti: {DOCUMENTS}.

{TRIBUNALE}, lì {DATE}

_______________________
Avv. {LAWYER_NAME}
""",

    "atto di citazione": """ALLEGATO: ATTO DI CITAZIONE

TRIBUNALE ORDINARIO DI {TRIBUNALE}

Nell'interesse del Sig. {CLIENT_NAME}, nato a {CLIENT_BORN} il {CLIENT_BORN_DATE}, residente in {CLIENT_ADDRESS}, C.F. {CLIENT_FC}, rappresentato e difeso dall'Avv. {LAWYER_NAME}, C.F. {LAWYER_FC}, PEC {LAWYER_PEC}, presso il cui studio in {LAWYER_ADDRESS} elegge domicilio giusta procura in calce,

SI CITA
Il Sig. {OPPONENT_NAME}, residente in {OPPONENT_ADDRESS}, C.F. {OPPONENT_FC}, a comparire dinanzi al Tribunale Ordinario di {TRIBUNALE}, all'udienza del giorno {COURT_DATE}, ore di rito, con l'invito a costituirsi nel termine di settanta giorni prima dell'udienza indicata, ai sensi e nelle forme stabilite dall'art. 166 c.p.c., con l'avvertimento che la costituzione oltre i suddetti termini implica le decadenze di cui agli artt. 38 e 167 c.p.c. e che in difetto di costituzione si procederà in sua legittima contumacia, per ivi sentir accogliere le seguenti

CONCLUSIONI
Voglia l'On.le Tribunale adito, respinta ogni contraria istanza ed eccezione:
{FACTS}
Con vittoria di spese e competenze professionali di causa.

Si offre in comunicazione la seguente documentazione: {DOCUMENTS}.

{TRIBUNALE}, lì {DATE}

_______________________
Avv. {LAWYER_NAME}
""",

    "ricorso": """ALLEGATO: RICORSO EX ARTICOLO {ARTICLES}

ECC.MO TRIBUNALE DI {TRIBUNALE}
Sezione {SECTION}

Il sottoscritto, {CLIENT_NAME}, C.F. {CLIENT_FC}, rappresentato e difeso dall'Avv. {LAWYER_NAME}, con studio in {LAWYER_ADDRESS}, propone formale ricorso per le motivazioni che di seguito si espongono.

PREMESSO IN FATTO
{FACTS}

RITENUTO IN DIRITTO
{LEGAL_REASONS}

Tutto ciò premesso, il ricorrente come sopra difeso e rappresentato,
RICORRE
a Codesto On.le Tribunale affinché voglia fissare l'udienza di comparizione delle parti per l'accoglimento delle seguenti conclusioni:
{CONCLUSIONS}

Si producono i seguenti documenti: {DOCUMENTS}.

{TRIBUNALE}, lì {DATE}

_______________________
Avv. {LAWYER_NAME}
""",

    "comparsa": """ALLEGATO: COMPARSA DI COSTITUZIONE E RISPOSTA

TRIBUNALE ORDINARIO DI {TRIBUNALE}
Giudice Dott. {JUDGE} - R.G. n. {PROCEDURAL_NUMBER}

Per: il Sig. {CLIENT_NAME}, C.F. {CLIENT_FC}, rappresentato e difeso dall'Avv. {LAWYER_NAME}
Convenuto
Contro: il Sig. {OPPONENT_NAME}
Attore

Con il presente atto si costituisce in giudizio il Sig. {CLIENT_NAME}, contestando integralmente quanto ex adverso dedotto, eccepito e richiesto nell'atto di citazione per i seguenti motivi.

IN FATTO E IN DIRITTO
{FACTS}

CONCLUSIONI
Voglia l'On.le Giudice adito, contrariis reiectis:
1. In via preliminare, dichiarare la nullità/inammissibilità della domanda dell'attore;
2. Nel merito, respingere la domanda attorea poiché infondata in fatto e in diritto;
3. Con vittoria di spese, competenze ed onorari di giudizio.

{TRIBUNALE}, lì {DATE}

_______________________
Avv. {LAWYER_NAME}
""",

    "parere pro veritate": """ALLEGATO: PARERE PRO VERITATE

OGGETTO: Analisi di legittimità ed inquadramento giuridico relativo a:
{SUBJECT}

Richiedente: {CLIENT_NAME}
Estensore: Avv. {LAWYER_NAME}, Foro di {TRIBUNALE}

PREMESSA E INTRODUZIONE
Ci si interroga in ordine alla rilevanza giuridica ed alle possibili conseguenze della fattispecie di seguito descritta, con particolare riferimento ai profili di responsabilità civile e penale.

QUADRO FATTUALE (I FATTI)
{FACTS}

INQUADRAMENTO GIURIDICO (IL DIRITTO)
{LEGAL_REASONS}

CONCLUSIONI E STRATEGIA CONSIGLIATA
Alla luce dell'analisi svolta, si ritiene che la posizione del richiedente sia tutelabile in quanto:
{CONCLUSIONS}

Si suggerisce di procedere tempestivamente con: {STRATEGY}.

Il presente parere viene rilasciato in scienza e coscienza, secondo il miglior apprezzamento dello scrivente.

{TRIBUNALE}, lì {DATE}

_______________________
Avv. {LAWYER_NAME}
"""
}

class DocumentGenerator:
    @classmethod
    def generate(cls, doc_type: str, data: Dict[str, Any]) -> str:
        """
        Renders a legal document template based on doc_type and replacement variables.
        """
        template_text = TEMPLATES.get(doc_type.lower())
        if not template_text:
            raise ValueError(f"Tipo di atto '{doc_type}' non supportato. Tipi supportati: {list(TEMPLATES.keys())}")
            
        # Complete missing variables with defaults
        defaults = {
            "TRIBUNALE": "Roma",
            "CLIENT_NAME": "[Nome Cliente]",
            "CLIENT_BORN": "[Luogo Nascita]",
            "CLIENT_BORN_DATE": "[Data Nascita]",
            "CLIENT_ADDRESS": "[Indirizzo Cliente]",
            "CLIENT_FC": "[Codice Fiscale Cliente]",
            "CLIENT_ROLE": "privato cittadino",
            "LAWYER_NAME": "[Nome Avvocato]",
            "LAWYER_ADDRESS": "[Studio Avvocato]",
            "LAWYER_FC": "[Codice Fiscale Avvocato]",
            "LAWYER_PEC": "[PEC Avvocato]",
            "OPPONENT_NAME": "[Nome Controparte]",
            "OPPONENT_ADDRESS": "[Indirizzo Controparte]",
            "OPPONENT_FC": "[Codice Fiscale Controparte]",
            "FACTS": "[Descrizione dettagliata dei fatti]",
            "ARTICLES": "[Articoli di legge]",
            "WITNESSES": "[Nessuno indicato]",
            "DOCUMENTS": "[Nessuno allegato]",
            "DATE": datetime.now().strftime("%d/%m/%Y"),
            "PROCEDURAL_NUMBER": "[R.G. N.]",
            "DEPARTMENT": "[Sezione]",
            "SECTION": "[Sezione]",
            "JUDGE": "[Nome Giudice]",
            "COURT_DATE": "[Data Udienza]",
            "SUBJECT": "[Oggetto del parere]",
            "LEGAL_REASONS": "[Motivi in diritto]",
            "CONCLUSIONS": "[Conclusioni formulate]",
            "STRATEGY": "[Azioni stragiudiziali/giudiziali consigliate]"
        }
        
        # Merge data into defaults
        rendered_data = {}
        for k, v in defaults.items():
            rendered_data[k] = str(data.get(k, data.get(k.lower(), v)))
            
        # Perform rendering
        return template_text.format(**rendered_data)
