# LexIA - Stato persistente del progetto

Aggiornato: 20 giugno 2026

## Regole operative

- Effettuare il deploy dopo ogni modifica.
- Verificare online la versione pubblica prima di dichiarare concluso il lavoro.
- Tutti i dati personali, i fascicoli, le chat e i documenti devono restare sul dispositivo dell'utente.
- Non cancellare o sovrascrivere modifiche esistenti senza verificarle.

## Accessi e route

- Applicazione pubblica: `https://vincenzoricciardi.eu/LexIA/`
- Fascicolo dedicato: `/LexIA/cases/{id}`
- Redazione atti separata: `/LexIA/cases/{id}/acts`
- La Redazione Atti viene aperta in una nuova scheda.

## Architettura privacy-first

- Archivio locale dei fascicoli e documenti tramite IndexedDB/localStorage.
- `index.php` serve l'interfaccia pubblica.
- `static/browser-api.js` intercetta gli endpoint `/api/...`.
- Il runtime pubblico di riferimento e' il browser: se `browser-api.js` non si inizializza, la UI deve bloccarsi con errore esplicito invece di simulare un backend parzialmente disponibile.
- PDF e DOCX testuali vengono letti localmente con PDF.js e Mammoth.
- I PDF scansione richiedono ancora OCR.
- L'invio di testo a provider cloud richiede consenso esplicito.

## Fascicoli

- La selezione o creazione di un fascicolo apre un workspace dedicato.
- Il workspace del fascicolo usa soltanto due aree: menu laterale e contenuto principale.
- La vecchia colonna contestuale "Contenuto fascicolo" è nascosta nel workspace dedicato.
- La Consulenza Legale si apre come unica schermata principale a tutta larghezza.
- Il menu del fascicolo contiene Consulenza Legale, Carica documenti, Documenti nel fascicolo, Profilo fascicolo, Parti e destinatario, redazione atti, suite investigativa e strategia.
- Caricamento e consultazione dei documenti sono schermate separate.
- `Documenti nel fascicolo` dispone di un editor testuale con salvataggio locale delle modifiche.
- La schermata usa lo stesso sistema di `Conversazioni importate`: elenco fisso con scorrimento autonomo a sinistra ed editor a destra.
- Sono leggibili TXT, Markdown, CSV, RTF, JSON, HTML, XML, LOG, EML, DOCX, ODT e PDF con testo estraibile.
- I file ODT vengono letti localmente estraendo il testo da `content.xml`.
- I file EML vengono interpretati localmente mostrando mittente, destinatari, data, oggetto e corpo.
- Gli EML sono formattati come messaggi email leggibili, con intestazioni in un riquadro e corpo separato.
- Per PDF e DOCX l'originale viene conservato e le modifiche riguardano una versione editoriale associata.
- Profilo fascicolo e Parti e destinatario sono schermate separate, aperte solo su richiesta dal menu.
- Il profilo contiene:
  - persona offesa o querelante;
  - controparte;
  - ente destinatario;
  - indirizzi;
  - PEC;
  - codici fiscali;
  - note.
- Il profilo può essere precompilato dai documenti caricati.

## Consulenza Legale

- Ogni chat riguarda esclusivamente il fascicolo attivo.
- La consulenza usa la documentazione leggibile del fascicolo.
- I messaggi restano memorizzati localmente.
- Il prompt legale avanzato è allineato tra browser privacy-first e backend.
- Il prompt impone raccolta dati mirata, controllo di termini e rito, distinzione tra fatti e ipotesi, strategia, rischi e controllo qualità.
- Il prompt ora include anche l'obiettivo esplicito della consulenza, la gerarchia delle fonti, la sezione sulla giurisprudenza e una struttura di analisi in nove punti.
- La struttura di risposta privilegia ricostruzione dei fatti, questioni giuridiche, normativa applicabile, valutazione, posizione prevalente, azioni possibili, procedura, rischi e conclusione.
- LexIA non deve inventare norme o precedenti e cita sentenze specifiche solo quando dispone di riferimenti ragionevolmente certi.
- LexIA distingue assistenza digitale e attività riservate a un avvocato abilitato.
- La sintassi Markdown non viene mostrata letteralmente.
- Titoli, paragrafi, grassetto, corsivo, elenchi, link e codice breve vengono resi in HTML sicuro.
- La narrazione dei fatti degli atti viene precompilata dalla consulenza del fascicolo.

## Provider OpenRouter

- Il modello gratuito consigliato e predefinito è `qwen/qwen3-next-80b-a3b-instruct:free`.
- La scelta privilegia contesto lungo, capacità multilingue e rispetto delle istruzioni strutturate.
- `openrouter/free` resta selezionabile come fallback, ma non è il default perché può cambiare modello tra richieste.
- Le vecchie configurazioni browser con router automatico o modelli gratuiti obsoleti vengono migrate al modello consigliato.
- In caso di `429` o indisponibilità temporanea, LexIA prova al massimo tre modelli gratuiti compatibili senza modificare la preferenza salvata.
- Ogni tentativo OpenRouter viene interrotto dopo 25 secondi per evitare attese indefinite.
- Se tutti i modelli gratuiti sono saturi, l'interfaccia mostra il dettaglio OpenRouter e segnala di verificare quota e limiti della chiave.

## Conversazioni della precedente edizione

- Le chat trovate negli ZIP della vecchia LexIA non vengono importate nella Consulenza Legale.
- Ogni chat storica viene convertita in un documento HTML locale modificabile.
- I documenti sono raccolti nella voce di menu `Conversazioni importate`.
- La colonna delle conversazioni resta fissa su desktop e dispone di scorrimento autonomo.
- I titoli mostrano soltanto il nome utile della pratica, senza `case_data` o origine.
- Provenienza e percorso originale restano conservati soltanto nei metadati interni.
- Il testo delle box va a capo e non può fuoriuscire dai contenitori.
- L'editor storico permette correzione e formattazione del testo.
- Conversazioni formattate e metadati di provenienza sono inclusi nei backup locali.

## Redazione Atti Forensi

- Workspace autonomo senza sidebar e colonne contestuali.
- Tipologie disponibili:
  - querela;
  - denuncia;
  - esposto;
  - diffida e costituzione in mora;
  - istanza;
  - memoria difensiva;
  - atto di citazione;
  - ricorso;
  - comparsa di costituzione e risposta;
  - parere pro veritate.
- Variabili precompilate dai dati del fascicolo.
- Intestazione automatica con persona interessata, controparte ed ente destinatario.
- Modelli distinti con struttura e riferimenti normativi prudenziali.
- Ogni bozza contiene un'avvertenza di verifica professionale.

## Editor atti

- Bozza modificabile prima della conferma definitiva.
- Pulizia automatica dei simboli Markdown.
- Barra di formattazione con:
  - annulla e ripristina;
  - grassetto, corsivo e sottolineato;
  - allineamento e giustificazione;
  - famiglia e dimensione del carattere;
  - colore del testo;
  - elenchi puntati e numerati;
  - rimozione della formattazione.
- Documento suddiviso in pagine A4 reali.
- Ogni pagina ha una propria area editabile.
- Il testo eccedente passa automaticamente alla pagina successiva.
- Contatore e numerazione delle pagine.
- Margini superiore, inferiore, sinistro e destro configurabili tra 10 e 60 mm.
- Margini standard: 25 mm sopra, 25 mm sotto, 30 mm a sinistra, 25 mm a destra.
- Bozze, formattazione e margini sono salvati localmente per fascicolo.
- Originale e PDF diventano disponibili solo dopo conferma del testo definitivo.
- Esportazione `.doc` compatibile con LibreOffice.
- Stampa/esportazione PDF in formato A4 con interruzioni di pagina reali.

## Deploy

- Script: `deploy_lexia.py`
- Il deploy avviene via FTP su `/LexIA`.
- Dopo il deploy eseguire una verifica HTTPS autenticata della funzione modificata.

## File principali

- `templates/index.html`: interfaccia e logica del frontend.
- `static/browser-api.js`: archivio locale, provider, documenti e API browser.
- `index.php`: entrypoint pubblico dell'interfaccia.
- `deploy_lexia.py`: pubblicazione FTP.

## Email EML

- Le email sono mostrate nell'editor con oggetto, intestazioni e corpo separati.
- Il filtro dell'editor conserva esclusivamente le classi grafiche sicure di LexIA.
- Le anteprime EML create con il vecchio filtro vengono rigenerate, salvo modifiche gia' salvate dall'utente.
- Anche i PDF che contengono intestazioni email `From`, `To`, `Date` e `Subject` vengono riconosciuti e impaginati come messaggi.
- Il riconoscimento PDF accetta anche `Da`, `Mittente`, `A`, `Destinatario`, `Data`, `Inviato`, `Oggetto`, `Cc` e `Ccn`, in ordine variabile.

## Documenti nella consulenza

- Ogni documento del fascicolo ha una scelta esplicita `Usa nella Consulenza Legale`.
- La chat consulta esclusivamente i documenti selezionati dall'utente.
- I documenti nuovi e quelli esistenti sono esclusi per impostazione predefinita.

## Salvataggio e stampa documenti

- `Salva con nome` usa il selettore di file del browser, quando supportato, per scegliere cartella e nome.
- Nei browser privi di File System Access API resta disponibile il normale download del browser.
- Ogni documento leggibile nell'editor puo' essere stampato direttamente in formato A4.

## Consulenza Legale

- Il campo di inserimento resta fisso nella parte inferiore del pannello.
- Scorre esclusivamente l'elenco dei messaggi, non la barra di scrittura.
- LexIA entra direttamente nel merito e non ripete a ogni risposta formule di autopresentazione o annunci dell'analisi.
- LexIA fornisce direttamente l'analisi specialistica e non rinvia genericamente l'utente a un avvocato per la sola complessita' del caso.
- Il professionista umano viene menzionato soltanto per specifiche attivita' riservate, difesa tecnica o adempimenti che lo richiedono.
- Il pulsante `Azzera chat` cancella esclusivamente la conversazione della Consulenza Legale del fascicolo attivo.

## Prossimi controlli consigliati

- Test manuale dell'editor con documenti di almeno tre pagine.
- Verifica del riflusso del testo cancellando contenuto tra due pagine.
- Verifica dei margini con valori minimi e massimi.
- Apertura del `.doc` esportato in LibreOffice.
- Confronto tra anteprima A4 e PDF prodotto dal browser.
- Valutazione e implementazione OCR locale per PDF scansione.
