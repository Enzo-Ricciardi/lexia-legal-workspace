(function () {
  "use strict";

  const nativeFetch = window.fetch.bind(window);
  const APP_BASE = location.pathname.startsWith("/LexIA/") || location.pathname === "/LexIA" ? "/LexIA" : "";
  const DB_NAME = "lexia-browser-v1";
  const SETTINGS_KEY = "lexia.settings.v1";
  const CASE_DIRS = [
    "documenti_cliente",
    "documenti_generati",
    "trascrizioni_audio",
    "ricerche_pec",
    "schede_testimoni",
    "conversazioni_importate",
    "note_utente"
  ];
  const ZIP_LIMITS = {
    maxEntries: 200,
    maxEntrySize: 25 * 1024 * 1024,
    maxTotalSize: 150 * 1024 * 1024,
    maxCompressionRatio: 150
  };
  const ACCEPTED_DOCUMENT_EXTENSIONS = new Set([
    "pdf", "docx", "doc", "txt", "md", "rtf", "jpg", "jpeg", "png",
    "gif", "webp", "odt", "csv", "json", "eml", "html", "htm", "xml", "log"
  ]);
  const SENSITIVE_JSON_KEYS = /(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|passwd|authorization|credential|private[_-]?key)/i;
  const DEFAULT_SETTINGS = {
    active_provider: "gemini",
    providers: {
      gemini: { api_key: "", model: "gemini-3.5-flash", url: "https://generativelanguage.googleapis.com/v1beta/models" },
      openai: { api_key: "", model: "gpt-4o", url: "https://api.openai.com/v1" },
      ollama: { api_key: "", model: "llama3", url: "http://localhost:11434" },
      lm_studio: { api_key: "", model: "meta-llama-3-8b-instruct", url: "http://localhost:1234/v1" },
      copilot: { api_key: "", model: "copilot-codex", url: "https://api.githubcopilot.com" },
      openrouter: { api_key: "", model: "qwen/qwen3-next-80b-a3b-instruct:free", url: "https://openrouter.ai/api/v1" }
    }
  };
  const SYSTEM_PROMPT = [
    "Sei LexIA, un agente digitale di assistenza legale avanzata, con metodo e linguaggio tecnico-forense di livello cassazionista.",
    "Operi nell'ambito del diritto italiano ed europeo, in particolare civile, penale, amministrativo, tributario, commerciale e del lavoro.",
    "Non dichiararti un avvocato abilitato e non presentare l'assistenza digitale come sostitutiva della difesa tecnica o delle attivita' riservate dalla legge.",
    "",
    "PRINCIPI OPERATIVI:",
    "- tutela riservatezza, lealta', chiarezza e correttezza; non suggerire condotte illecite, elusive o ingannevoli;",
    "- considera soltanto i fatti forniti dall'utente e i documenti del fascicolo; distingui fatti documentati, dichiarazioni, ipotesi e informazioni mancanti;",
    "- prima di concludere, verifica parti, cronologia, luogo dei fatti, documenti, testimoni, atti ricevuti o notificati, obiettivo dell'utente, termini, prescrizioni e decadenze;",
    "- se mancano dati decisivi, poni domande mirate e non formulare conclusioni definitive;",
    "- segnala possibili conflitti di interesse o posizioni incompatibili, senza affermare di aver svolto una verifica professionale esterna;",
    "- individua rito, competenza, condizioni di procedibilita', onere della prova, legittimazione e possibili rimedi, precisando quando richiedono verifica aggiornata.",
    "- nella Consulenza Legale non scrivere come se stessi redigendo un atto, un parere pro veritate o una lettera formale: produci invece una relazione tecnica chiara sui fatti e una guida pratica per i prossimi passi;",
    "- prima di suggerire il ricorso a un legale civile o penale, indica sempre tutte le iniziative stragiudiziali o comunque direttamente attivabili dal cittadino, se pertinenti: raccolta prove, diffida, messa in mora, accesso agli atti, istanza, segnalazione, reclamo, esposto, denuncia, querela, PEC, richiesta documentale o interlocuzione con l'ente competente;",
    "",
    "FONTI E ACCURATEZZA:",
    "- non inventare articoli, sentenze, numeri, date, massime, termini o autorita';",
    "- cita una fonte giurisprudenziale specifica solo se conosci con ragionevole certezza organo, sezione, data e numero; altrimenti descrivi il principio e scrivi che la citazione deve essere verificata;",
    "- quando richiami una sentenza della Cassazione come verificata, indica anche la fonte originale o ufficiale da cui risulta la pronuncia; se non puoi mostrare una fonte originale verificabile, non presentarla come certa;",
    "- distingui legge vigente, interpretazione, orientamento consolidato, orientamento minoritario e questione controversa;",
    "- segnala eventuali Sezioni Unite, Corte costituzionale, CGUE, Consiglio di Stato o altri precedenti qualificati solo se pertinenti e verificabili;",
    "- tratta norme, termini e procedure come dati soggetti ad aggiornamento e invita alla consultazione di fonti ufficiali.",
    "",
    "STRUTTURA DELLE ANALISI COMPLESSE:",
    "1. Fatti rilevanti: che cosa emerge dai documenti e dai messaggi dell'utente, distinguendo dati certi, allegazioni e punti mancanti.",
    "2. Questioni giuridiche: quali sono i nodi di diritto realmente aperti.",
    "3. Normativa applicabile: fonti pertinenti, condizioni e limiti di applicazione.",
    "4. Giurisprudenza: principi verificabili e orientamenti utili, senza citazioni inventate.",
    "5. Valutazione pratica: punti di forza, criticita', eccezioni prevedibili e aspetti da chiarire.",
    "6. Come procedere: azioni concrete, ordine dei passi, documenti da recuperare, termini da controllare e priorita' operative. Indica prima le iniziative che il cittadino puo' svolgere da solo e solo dopo gli adempimenti che richiedono assistenza tecnica.",
    "7. Rischi e cautele: prove, termini, costi, tempi, soccombenza e responsabilita'. Non esprimere percentuali arbitrarie.",
    "8. Sintesi finale: conclusione operativa breve e comprensibile per l'interessato.",
    "",
    "REDAZIONE ATTI:",
    "Predisponi una bozza formale solo quando l'utente chiede espressamente un atto o usa il workspace dedicato alla redazione atti.",
    "Non inserire dati assenti; usa segnaposto chiaramente riconoscibili. Evidenzia competenza, termini, procura, firma, notifica, deposito e contributi da verificare.",
    "Segnala sempre quando sono necessari avvocato abilitato, procura alle liti, firma professionale, deposito telematico o altra attivita' riservata.",
    "",
    "CONTROLLO QUALITA':",
    "Prima della risposta verifica coerenza logica, completezza, contraddizioni, supporto delle affermazioni e adeguatezza delle avvertenze.",
    "Usa italiano giuridico chiaro e preciso. Evita formule enfatiche, promesse di risultato e certezze non dimostrate.",
    "Non usare tabelle markdown, griglie ASCII, colonne con barre verticali o riquadri grafici: scrivi sempre in testo lineare, con paragrafi brevi ed elenchi semplici.",
    "Per richieste semplici rispondi in modo diretto; applica lo schema completo solo quando utile.",
    "",
    "STILE CONVERSAZIONALE:",
    "- non ripresentarti e non ricordare a ogni risposta di essere LexIA o un agente digitale;",
    "- entra direttamente nel merito, senza preamboli che annunciano l'analisi o riepilogano il metodo;",
    "- non usare formule ricorrenti come «In qualita' di LexIA... procedo all'analisi della Sua richiesta» o espressioni equivalenti;",
    "- considera acquisiti ruolo, contesto e informazioni precedenti; richiama soltanto gli elementi necessari alla risposta corrente;",
    "- usa un'introduzione solo quando chiarisce una questione nuova o un rischio concreto, mai come formula di cortesia automatica;",
    "- fornisci direttamente la consulenza legale specialistica richiesta, anche quando coinvolge piu' materie, senza concludere con un rinvio generico a un avvocato;",
    "- nella consulenza usa forma espositiva semplice e tecnica, come una relazione di lavoro o una guida operativa, non come un documento formale destinato al deposito o all'invio;",
    "- parla direttamente con chi ha posto la domanda, come se fosse seduto davanti a te; puoi usare il 'tu' se il tono del fascicolo e della richiesta lo consente;",
    "- se il fascicolo riguarda l'assistito che sta parlando con te, non riferirti a lui in terza persona come se fosse un soggetto esterno; rivolgiti direttamente all'interessato;",
    "- usa la terza persona solo per soggetti diversi dall'utente, come controparte, testimoni, enti, difensori o altri protagonisti della vicenda;",
    "- se menzioni una sentenza di Cassazione, specifica sempre se e' verificata oppure no; se e' verificata, indica la fonte originale, se non lo e' dillo espressamente;",
    "- non scrivere formule come «data la complessita', e' fortemente raccomandato rivolgersi a un avvocato specializzato» o equivalenti;",
    "- segnala l'intervento di un professionista umano solo dopo aver esposto le iniziative autonome praticabili e solo per una specifica attivita' legalmente riservata o una scadenza concreta, indicando esattamente quale adempimento lo richiede."
  ].join("\n");

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function json(data, status) {
    return new Response(JSON.stringify(data), {
      status: status || 200,
      headers: { "Content-Type": "application/json; charset=utf-8" }
    });
  }

  function failure(status, detail) {
    return json({ detail: detail }, status);
  }

  function safeSegment(value) {
    const decoded = decodeURIComponent(String(value || ""));
    if (!decoded || decoded === "." || decoded === ".." || decoded.includes("/") || decoded.includes("\\")) {
      throw new Error("Nome non valido.");
    }
    return decoded;
  }

  function readSettings() {
    try {
      const parsed = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "null");
      if (!parsed || typeof parsed !== "object") return clone(DEFAULT_SETTINGS);
      const merged = clone(DEFAULT_SETTINGS);
      if (merged.providers[parsed.active_provider]) merged.active_provider = parsed.active_provider;
      Object.keys(merged.providers).forEach(function (id) {
        if (parsed.providers && parsed.providers[id]) {
          Object.assign(merged.providers[id], parsed.providers[id]);
        }
      });
      if (/^gemini-(?:1(?:\.0|\.5)|2\.0|2\.5|3(?:\.\d+)?)(?:-|$)/.test(merged.providers.gemini.model || "")) {
        merged.providers.gemini.model = DEFAULT_SETTINGS.providers.gemini.model;
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
      }
      if ([
        "openrouter/free",
        "meta-llama/llama-3-8b-instruct:free",
        "google/gemini-3.5-flash"
      ].includes(merged.providers.openrouter.model || "")) {
        merged.providers.openrouter.model = DEFAULT_SETTINGS.providers.openrouter.model;
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
      }
      return merged;
    } catch (error) {
      console.warn("Configurazione LexIA non leggibile:", error);
      return clone(DEFAULT_SETTINGS);
    }
  }

  function saveSettings(settings) {
    const merged = clone(DEFAULT_SETTINGS);
    if (settings && merged.providers[settings.active_provider]) merged.active_provider = settings.active_provider;
    Object.keys(merged.providers).forEach(function (id) {
      if (settings && settings.providers && settings.providers[id]) {
        Object.assign(merged.providers[id], settings.providers[id]);
      }
    });
    if (/^gemini-(?:1(?:\.0|\.5)|2\.0|2\.5|3(?:\.\d+)?)(?:-|$)/.test(merged.providers.gemini.model || "")) {
      merged.providers.gemini.model = DEFAULT_SETTINGS.providers.gemini.model;
    }
    if ([
      "openrouter/free",
      "meta-llama/llama-3-8b-instruct:free",
      "google/gemini-3.5-flash"
    ].includes(merged.providers.openrouter.model || "")) {
      merged.providers.openrouter.model = DEFAULT_SETTINGS.providers.openrouter.model;
    }
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
    return merged;
  }

  function openDb() {
    return new Promise(function (resolve, reject) {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = function () {
        const db = request.result;
        if (!db.objectStoreNames.contains("cases")) db.createObjectStore("cases", { keyPath: "id" });
        if (!db.objectStoreNames.contains("files")) {
          const files = db.createObjectStore("files", { keyPath: "key" });
          files.createIndex("caseId", "caseId", { unique: false });
        }
      };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  async function storeAction(storeName, mode, action) {
    const db = await openDb();
    return new Promise(function (resolve, reject) {
      const tx = db.transaction(storeName, mode);
      const store = tx.objectStore(storeName);
      let result;
      try {
        result = action(store);
      } catch (error) {
        db.close();
        reject(error);
        return;
      }
      tx.oncomplete = function () { db.close(); resolve(result); };
      tx.onerror = function () { db.close(); reject(tx.error); };
      tx.onabort = function () { db.close(); reject(tx.error); };
    });
  }

  async function getCase(id) {
    const db = await openDb();
    return new Promise(function (resolve, reject) {
      const tx = db.transaction("cases", "readonly");
      const req = tx.objectStore("cases").get(id);
      req.onsuccess = function () { resolve(req.result || null); };
      req.onerror = function () { reject(req.error); };
      tx.oncomplete = function () { db.close(); };
    });
  }

  async function putCase(item) {
    await storeAction("cases", "readwrite", function (store) { store.put(item); });
    return item;
  }

  async function listCases() {
    const db = await openDb();
    return new Promise(function (resolve, reject) {
      const tx = db.transaction("cases", "readonly");
      const req = tx.objectStore("cases").getAll();
      req.onsuccess = function () {
        resolve((req.result || [])
          .filter(function (item) { return !item.temporary; })
          .sort(function (a, b) { return String(b.created_at).localeCompare(String(a.created_at)); })
          .map(metadataOnly));
      };
      req.onerror = function () { reject(req.error); };
      tx.oncomplete = function () { db.close(); };
    });
  }

  function metadataOnly(item) {
    const result = clone(item);
    delete result.conversation;
    return result;
  }

  function newCase(payload, temporary) {
    const now = new Date().toISOString();
    return {
      id: temporary ? "temp_case" : crypto.randomUUID().slice(0, 8) + "_" + now.replace(/\D/g, "").slice(0, 14),
      name: temporary ? "Consulenza Preliminare" : String(payload.name || "").trim(),
      client: temporary ? "Temporaneo" : String(payload.client || "").trim(),
      description: temporary ? "Fascicolo temporaneo per consultazione libera" : String(payload.description || "").trim(),
      created_at: now,
      status: temporary ? "temporaneo" : "attivo",
      temporary: Boolean(temporary),
      profile: payload.profile && typeof payload.profile === "object" ? clone(payload.profile) : {},
      conversation: Array.isArray(payload.history) ? payload.history : []
    };
  }

  async function resetTempCase() {
    const item = newCase({}, true);
    await deleteCaseAndFiles("temp_case");
    await putCase(item);
    return metadataOnly(item);
  }

  async function deleteCaseAndFiles(id) {
    const db = await openDb();
    return new Promise(function (resolve, reject) {
      const tx = db.transaction(["cases", "files"], "readwrite");
      tx.objectStore("cases").delete(id);
      const index = tx.objectStore("files").index("caseId");
      const req = index.openCursor(IDBKeyRange.only(id));
      req.onsuccess = function () {
        const cursor = req.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        }
      };
      tx.oncomplete = function () { db.close(); resolve(); };
      tx.onerror = function () { db.close(); reject(tx.error); };
    });
  }

  async function filesForCase(caseId) {
    const db = await openDb();
    return new Promise(function (resolve, reject) {
      const tx = db.transaction("files", "readonly");
      const req = tx.objectStore("files").index("caseId").getAll(caseId);
      req.onsuccess = function () { resolve(req.result || []); };
      req.onerror = function () { reject(req.error); };
      tx.oncomplete = function () { db.close(); };
    });
  }

  async function putFile(record) {
    await storeAction("files", "readwrite", function (store) { store.put(record); });
  }

  async function deleteFile(key) {
    await storeAction("files", "readwrite", function (store) { store.delete(key); });
  }

  async function blobToBase64(blob) {
    const buffer = await blob.arrayBuffer();
    let binary = "";
    const bytes = new Uint8Array(buffer);
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
  }

  function base64ToBlob(base64, type) {
    const binary = atob(String(base64 || ""));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new Blob([bytes], { type: type || "application/octet-stream" });
  }

  async function exportLocalBackup() {
    const db = await openDb();
    try {
      const snapshot = { version: 1, exported_at: new Date().toISOString(), cases: [], files: [] };
      snapshot.cases = await new Promise(function (resolve, reject) {
        const tx = db.transaction("cases", "readonly");
        const req = tx.objectStore("cases").getAll();
        req.onsuccess = function () {
          resolve((req.result || []).map(function (item) {
            const copy = clone(item);
            delete copy.conversation;
            return copy;
          }));
        };
        req.onerror = function () { reject(req.error); };
      });
      snapshot.files = await filesForBackup();
      return snapshot;
    } finally {
      try { db.close(); } catch (_) {}
    }
  }

  async function filesForBackup() {
    const db = await openDb();
    return new Promise(function (resolve, reject) {
      const tx = db.transaction("files", "readonly");
      const req = tx.objectStore("files").getAll();
      req.onsuccess = function () {
        Promise.all((req.result || []).map(async function (file) {
          return {
            key: file.key,
            caseId: file.caseId,
            category: file.category,
            name: file.name,
            migrationNotice: file.migrationNotice || "",
            html: file.html || "",
            topic: file.topic || "",
            sourceArchive: file.sourceArchive || "",
            archivePath: file.archivePath || "",
            editorHtml: file.editorHtml || "",
            editorText: file.editorText || "",
            editorModified: file.editorModified || "",
            consultationIncluded: file.consultationIncluded === true,
            size: file.size,
            modified: file.modified,
            text: file.text || "",
            blobType: file.blob && file.blob.type ? file.blob.type : "application/octet-stream",
            blobBase64: file.blob ? await blobToBase64(file.blob) : ""
          };
        })).then(resolve).catch(reject);
      };
      req.onerror = function () { reject(req.error); };
      tx.oncomplete = function () { db.close(); };
    });
  }

  async function restoreLocalBackup(snapshot) {
    if (!snapshot || typeof snapshot !== "object") throw new Error("Backup non valido.");
    if (!Array.isArray(snapshot.cases) || !Array.isArray(snapshot.files)) {
      throw new Error("Struttura backup non valida.");
    }
    const db = await openDb();
    try {
      await new Promise(function (resolve, reject) {
        const tx = db.transaction(["cases", "files"], "readwrite");
        tx.objectStore("cases").clear();
        tx.objectStore("files").clear();
        tx.oncomplete = function () { resolve(); };
        tx.onerror = function () { reject(tx.error); };
        tx.onabort = function () { reject(tx.error); };
      });
      for (const item of snapshot.cases) {
        await putCase(item);
      }
      for (const file of snapshot.files) {
        const restored = clone(file);
        restored.blob = restored.blobBase64 ? base64ToBlob(restored.blobBase64, restored.blobType) : new Blob([restored.text || ""], { type: "text/plain" });
        delete restored.blobBase64;
        delete restored.blobType;
        await putFile(restored);
      }
      return true;
    } finally {
      try { db.close(); } catch (_) {}
    }
  }

  function uniqueName(files, category, original) {
    const clean = String(original || "documento")
      .replace(/^.*[\\/]/, "")
      .replace(/\s+/g, "_")
      .replace(/[^A-Za-z0-9._-]/g, "_");
    const dot = clean.lastIndexOf(".");
    const stem = dot > 0 ? clean.slice(0, dot) : clean;
    const ext = dot > 0 ? clean.slice(dot) : "";
    let candidate = clean || "documento";
    let counter = 1;
    const occupied = new Set(files.filter(function (f) { return f.category === category; }).map(function (f) { return f.name; }));
    while (occupied.has(candidate)) candidate = stem + "_" + counter++ + ext;
    return candidate;
  }

  function zipU16(view, offset) {
    return view.getUint16(offset, true);
  }

  function zipU32(view, offset) {
    return view.getUint32(offset, true);
  }

  function decodeZipName(bytes, utf8) {
    try {
      return new TextDecoder(utf8 ? "utf-8" : "windows-1252").decode(bytes);
    } catch (_) {
      return new TextDecoder().decode(bytes);
    }
  }

  function safeArchiveName(path) {
    const normalized = String(path || "").replace(/\\/g, "/");
    if (!normalized || normalized.startsWith("/") || normalized.includes("../") || /^[A-Za-z]:/.test(normalized)) {
      throw new Error("Percorso non sicuro nell'archivio.");
    }
    const parts = normalized.split("/").filter(Boolean);
    if (!parts.length) throw new Error("Nome file ZIP non valido.");
    return parts.join("__");
  }

  function findZipDirectory(view) {
    const minimum = Math.max(0, view.byteLength - 65557);
    for (let offset = view.byteLength - 22; offset >= minimum; offset--) {
      if (zipU32(view, offset) === 0x06054b50) return offset;
    }
    throw new Error("Archivio ZIP non valido o incompleto.");
  }

  async function inflateZipData(bytes, method) {
    if (method === 0) return bytes;
    if (method !== 8) throw new Error("Metodo di compressione ZIP non supportato: " + method + ".");
    if (typeof DecompressionStream !== "function") {
      throw new Error("Questo browser non supporta l'estrazione ZIP. Aggiornare Chrome, Edge o Firefox.");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  async function extractZip(file) {
    const buffer = await file.arrayBuffer();
    const view = new DataView(buffer);
    const bytes = new Uint8Array(buffer);
    const endOffset = findZipDirectory(view);
    const entriesCount = zipU16(view, endOffset + 10);
    const directoryOffset = zipU32(view, endOffset + 16);
    if (entriesCount === 0xffff || directoryOffset === 0xffffffff) {
      throw new Error("Gli archivi ZIP64 non sono supportati.");
    }
    if (entriesCount > ZIP_LIMITS.maxEntries) {
      throw new Error("Lo ZIP contiene troppi file (massimo " + ZIP_LIMITS.maxEntries + ").");
    }

    const entries = [];
    let offset = directoryOffset;
    let totalSize = 0;
    for (let index = 0; index < entriesCount; index++) {
      if (offset + 46 > view.byteLength || zipU32(view, offset) !== 0x02014b50) {
        throw new Error("Indice centrale ZIP danneggiato.");
      }
      const flags = zipU16(view, offset + 8);
      const method = zipU16(view, offset + 10);
      const compressedSize = zipU32(view, offset + 20);
      const uncompressedSize = zipU32(view, offset + 24);
      const nameLength = zipU16(view, offset + 28);
      const extraLength = zipU16(view, offset + 30);
      const commentLength = zipU16(view, offset + 32);
      const localOffset = zipU32(view, offset + 42);
      const rawName = bytes.slice(offset + 46, offset + 46 + nameLength);
      const archivePath = decodeZipName(rawName, Boolean(flags & 0x0800));
      offset += 46 + nameLength + extraLength + commentLength;

      if (archivePath.endsWith("/")) continue;
      if (flags & 0x0001) throw new Error("Lo ZIP contiene file cifrati, non supportati.");
      if (uncompressedSize > ZIP_LIMITS.maxEntrySize) {
        throw new Error("Il file " + archivePath + " supera 25 MB.");
      }
      totalSize += uncompressedSize;
      if (totalSize > ZIP_LIMITS.maxTotalSize) {
        throw new Error("Il contenuto estratto supera 150 MB.");
      }
      if (compressedSize > 0 && uncompressedSize / compressedSize > ZIP_LIMITS.maxCompressionRatio) {
        throw new Error("Rapporto di compressione sospetto per " + archivePath + ".");
      }
      if (localOffset + 30 > view.byteLength || zipU32(view, localOffset) !== 0x04034b50) {
        throw new Error("Voce ZIP danneggiata: " + archivePath + ".");
      }
      const localNameLength = zipU16(view, localOffset + 26);
      const localExtraLength = zipU16(view, localOffset + 28);
      const dataOffset = localOffset + 30 + localNameLength + localExtraLength;
      if (dataOffset + compressedSize > view.byteLength) {
        throw new Error("Dati ZIP incompleti per " + archivePath + ".");
      }
      const extension = archivePath.split(".").pop().toLowerCase();
      if (!ACCEPTED_DOCUMENT_EXTENSIONS.has(extension)) continue;
      entries.push({
        archivePath: archivePath,
        safeName: safeArchiveName(archivePath),
        method: method,
        compressed: bytes.slice(dataOffset, dataOffset + compressedSize),
        uncompressedSize: uncompressedSize
      });
    }

    const extracted = [];
    for (const entry of entries) {
      const content = await inflateZipData(entry.compressed, entry.method);
      if (content.byteLength !== entry.uncompressedSize) {
        throw new Error("Dimensione estratta non valida per " + entry.archivePath + ".");
      }
      extracted.push({
        archivePath: entry.archivePath,
        safeName: entry.safeName,
        blob: new Blob([content], { type: documentMime(entry.safeName) })
      });
    }
    return extracted;
  }

  async function documentText(blob, name) {
    if (/\.pdf$/i.test(name)) return extractPdfText(blob);
    if (/\.docx$/i.test(name)) return extractDocxText(blob);
    if (/\.odt$/i.test(name)) return extractOdtText(blob);
    if (/\.eml$/i.test(name)) return extractEmlText(await blob.text());
    if (!/\.(txt|md|csv|rtf|json|html?|xml|log)$/i.test(name)) return "";
    const text = await blob.text();
    if (/\.json$/i.test(name)) {
      try {
        return JSON.stringify(sanitizeJson(JSON.parse(text)), null, 2).slice(0, 500000);
      } catch (_) {
        return text.slice(0, 500000);
      }
    }
    return text.slice(0, 500000);
  }

  async function extractOdtText(blob) {
    const entries = await extractZip(blob);
    const content = entries.find(function (entry) {
      return String(entry.archivePath || "").toLowerCase() === "content.xml";
    });
    if (!content) throw new Error("Il file ODT non contiene content.xml.");
    const xml = await content.blob.text();
    const parsed = new DOMParser().parseFromString(xml, "application/xml");
    if (parsed.querySelector("parsererror")) throw new Error("Contenuto ODT non leggibile.");
    const blocks = Array.from(parsed.getElementsByTagNameNS("*", "p"))
      .concat(Array.from(parsed.getElementsByTagNameNS("*", "h")));
    if (blocks.length) {
      return blocks.map(function (node) { return String(node.textContent || "").trim(); })
        .filter(Boolean).join("\n\n").slice(0, 500000);
    }
    return String(parsed.documentElement ? parsed.documentElement.textContent : "")
      .replace(/\s+/g, " ").trim().slice(0, 500000);
  }

  function decodeQuotedPrintable(value) {
    return String(value || "")
      .replace(/=\r?\n/g, "")
      .replace(/=([A-Fa-f0-9]{2})/g, function (_, hex) {
        return String.fromCharCode(parseInt(hex, 16));
      });
  }

  function extractEmlText(raw) {
    const source = String(raw || "").replace(/\r\n/g, "\n");
    const split = source.indexOf("\n\n");
    const headerText = split >= 0 ? source.slice(0, split) : source;
    const bodyText = split >= 0 ? source.slice(split + 2) : "";
    const unfolded = headerText.replace(/\n[ \t]+/g, " ");
    const headers = {};
    unfolded.split("\n").forEach(function (line) {
      const match = line.match(/^([^:]+):\s*(.*)$/);
      if (match) headers[match[1].toLowerCase()] = match[2];
    });
    let body = bodyText;
    if (/quoted-printable/i.test(headers["content-transfer-encoding"] || "")) {
      body = decodeQuotedPrintable(body);
    } else if (/base64/i.test(headers["content-transfer-encoding"] || "")) {
      try { body = decodeURIComponent(escape(atob(body.replace(/\s/g, "")))); } catch (_) {}
    }
    if (/text\/html/i.test(headers["content-type"] || "")) {
      const parsed = new DOMParser().parseFromString(body, "text/html");
      body = parsed.body ? parsed.body.innerText : body.replace(/<[^>]+>/g, " ");
    }
    return [
      "Da: " + (headers.from || ""),
      "A: " + (headers.to || ""),
      headers.cc ? "Cc: " + headers.cc : "",
      "Data: " + (headers.date || ""),
      "Oggetto: " + (headers.subject || ""),
      "",
      body.trim()
    ].filter(function (line, index) { return line || index === 5; }).join("\n").slice(0, 500000);
  }

  function extractEmlHtml(raw) {
    const source = String(raw || "").replace(/\r\n/g, "\n");
    const split = source.indexOf("\n\n");
    const headerText = split >= 0 ? source.slice(0, split) : source;
    let body = split >= 0 ? source.slice(split + 2) : "";
    const unfolded = headerText.replace(/\n[ \t]+/g, " ");
    const headers = {};
    unfolded.split("\n").forEach(function (line) {
      const match = line.match(/^([^:]+):\s*(.*)$/);
      if (match) headers[match[1].toLowerCase()] = match[2];
    });
    if (/quoted-printable/i.test(headers["content-transfer-encoding"] || "")) {
      body = decodeQuotedPrintable(body);
    } else if (/base64/i.test(headers["content-transfer-encoding"] || "")) {
      try { body = decodeURIComponent(escape(atob(body.replace(/\s/g, "")))); } catch (_) {}
    }
    const escapeHtml = function (value) {
      return String(value || "").replace(/[&<>"']/g, function (char) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char];
      });
    };
    let bodyHtml;
    if (/text\/html/i.test(headers["content-type"] || "")) {
      const parsed = new DOMParser().parseFromString(body, "text/html");
      parsed.querySelectorAll("script,style,iframe,object,embed,link,meta,img").forEach(function (element) { element.remove(); });
      bodyHtml = parsed.body ? parsed.body.innerHTML : escapeHtml(body).replace(/\n/g, "<br>");
    } else {
      bodyHtml = escapeHtml(body.trim()).replace(/\n{2,}/g, "</p><p>").replace(/\n/g, "<br>");
      bodyHtml = "<p>" + bodyHtml + "</p>";
    }
    const row = function (label, value) {
      return value ? "<div><strong>" + label + ":</strong> " + escapeHtml(value) + "</div>" : "";
    };
    return [
      '<div class="lexia-email">',
      '<h1>' + escapeHtml(headers.subject || "Messaggio email") + '</h1>',
      '<div class="lexia-email-headers">',
      row("Da", headers.from),
      row("A", headers.to),
      row("Cc", headers.cc),
      row("Data", headers.date),
      row("Oggetto", headers.subject),
      '</div>',
      '<hr>',
      '<div class="lexia-email-body">' + bodyHtml + '</div>',
      '</div>'
    ].join("");
  }

  function extractedEmailHtml(text) {
    const source = String(text || "").replace(/\r/g, "").trim();
    const labelPattern = /(?:^|\s)(From|Da|Mittente|To|A|Destinatario|Cc|Ccn|Date|Data|Sent|Inviato|Subject|Oggetto)\s*:\s*/gi;
    const labels = [];
    let labelMatch;
    while ((labelMatch = labelPattern.exec(source))) {
      labels.push({
        key: labelMatch[1].toLowerCase(),
        start: labelMatch.index,
        valueStart: labelPattern.lastIndex
      });
    }
    if (labels.length < 2) return "";
    const fields = {};
    labels.forEach(function (label, index) {
      const end = index + 1 < labels.length ? labels[index + 1].start : source.length;
      fields[label.key] = source.slice(label.valueStart, end).trim();
    });
    const sender = fields.from || fields.da || fields.mittente || "";
    const recipient = fields.to || fields.a || fields.destinatario || "";
    const date = fields.date || fields.data || fields.sent || fields.inviato || "";
    let subject = fields.subject || fields.oggetto || "";
    if (!sender || !recipient || (!subject && !date)) return "";
    let body = "";
    const bodyStart = subject.search(/\s{2,}(?=\S)|\s+(?=(?:Spett\.?le|Gentil[ei]|Buongiorno|Buonasera|Egregi[oa]|Con la presente|In riferimento|Si comunica)\b)/i);
    if (bodyStart >= 0) {
      body = subject.slice(bodyStart).trim();
      subject = subject.slice(0, bodyStart).trim();
    }
    const escapeHtml = function (value) {
      return String(value || "").replace(/[&<>"']/g, function (char) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char];
      });
    };
    const message = body || subject;
    const paragraphs = message.split(/\n{2,}/).map(function (paragraph) {
      return "<p>" + escapeHtml(paragraph).replace(/\n/g, "<br>") + "</p>";
    }).join("");
    const row = function (label, value) {
      return value ? '<div><strong>' + label + ':</strong> ' + escapeHtml(value) + '</div>' : "";
    };
    return [
      '<div class="lexia-email">',
      '<h1>' + escapeHtml(body && subject ? subject : "Messaggio di posta elettronica") + '</h1>',
      '<div class="lexia-email-headers">',
      row("Da", sender),
      row("A", recipient),
      row("Cc", fields.cc),
      row("Ccn", fields.ccn),
      row("Data", date),
      '</div>',
      '<hr>',
      '<div class="lexia-email-body">' + paragraphs + '</div>',
      '</div>'
    ].join("");
  }

  async function extractPdfText(blob) {
    if (!window.pdfjsLib) throw new Error("Lettore PDF locale non disponibile.");
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = window.LEXIA_PDF_WORKER_URL || (APP_BASE + "/static/vendor/pdf.worker.min.js");
    const pdf = await window.pdfjsLib.getDocument({ data: await blob.arrayBuffer() }).promise;
    const pages = [];
    for (let number = 1; number <= pdf.numPages; number++) {
      const page = await pdf.getPage(number);
      const content = await page.getTextContent();
      pages.push(content.items.map(function (item) { return item.str || ""; }).join(" "));
      if (pages.join("\n").length >= 500000) break;
    }
    return pages.join("\n\n").slice(0, 500000);
  }

  async function extractDocxText(blob) {
    if (!window.mammoth) throw new Error("Lettore DOCX locale non disponibile.");
    const result = await window.mammoth.extractRawText({ arrayBuffer: await blob.arrayBuffer() });
    return String(result.value || "").slice(0, 500000);
  }

  function documentMime(name) {
    const extension = String(name).split(".").pop().toLowerCase();
    return {
      pdf: "application/pdf",
      doc: "application/msword",
      docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      odt: "application/vnd.oasis.opendocument.text",
      txt: "text/plain",
      md: "text/markdown",
      csv: "text/csv",
      json: "application/json",
      rtf: "application/rtf",
      eml: "message/rfc822",
      html: "text/html",
      htm: "text/html",
      xml: "application/xml",
      log: "text/plain",
      jpg: "image/jpeg",
      jpeg: "image/jpeg",
      png: "image/png",
      gif: "image/gif",
      webp: "image/webp"
    }[extension] || "application/octet-stream";
  }

  function sanitizeJson(value, depth) {
    const level = depth || 0;
    if (level > 30) return "[Livello troppo profondo]";
    if (Array.isArray(value)) return value.slice(0, 5000).map(function (item) { return sanitizeJson(item, level + 1); });
    if (!value || typeof value !== "object") return value;
    const clean = {};
    Object.keys(value).slice(0, 5000).forEach(function (key) {
      if (SENSITIVE_JSON_KEYS.test(key)) {
        clean[key] = "[RIMOSSO PER SICUREZZA]";
      } else if (key === "providers" || key === "active_provider") {
        clean[key] = "[CONFIGURAZIONE PROVIDER NON IMPORTATA]";
      } else {
        clean[key] = sanitizeJson(value[key], level + 1);
      }
    });
    return clean;
  }

  function normalizeRole(role) {
    const value = String(role || "").toLowerCase();
    if (["user", "utente", "human", "cliente"].includes(value)) return "utente";
    if (["assistant", "lexia", "ai", "avvocato", "agent"].includes(value)) return "lexia";
    return "";
  }

  function normalizeConversation(data) {
    let source = data;
    if (!Array.isArray(source) && source && typeof source === "object") {
      source = source.conversation || source.conversazione || source.history || source.messages || source.chat;
    }
    if (!Array.isArray(source)) return [];
    return source.slice(0, 5000).map(function (entry) {
      if (!entry || typeof entry !== "object") return null;
      const role = normalizeRole(entry.role || entry.sender || entry.author || entry.type);
      const content = entry.content ?? entry.text ?? entry.message ?? entry.body;
      if (!role || typeof content !== "string" || !content.trim()) return null;
      return {
        role: role,
        content: content.slice(0, 100000),
        timestamp: String(entry.timestamp || entry.created_at || entry.date || new Date().toISOString())
      };
    }).filter(Boolean);
  }

  function legacyMetadata(data) {
    if (!data || typeof data !== "object" || Array.isArray(data)) return null;
    const name = data.name ?? data.nome ?? data.title ?? data.titolo ?? data.case_name;
    const client = data.client ?? data.cliente ?? data.assistito;
    const description = data.description ?? data.descrizione ?? data.notes ?? data.note;
    if (!name && !client && !description && !data.created_at && !data.status) return null;
    return {
      name: String(name || "Fascicolo importato"),
      client: String(client || "Non indicato"),
      description: String(description || ""),
      created_at: String(data.created_at || data.data_creazione || ""),
      status: String(data.status || data.stato || "")
    };
  }

  async function importLegacyJson(caseItem, entry, sourceArchive) {
    const raw = await entry.blob.text();
    if (raw.length > 5 * 1024 * 1024) throw new Error("JSON troppo grande per la migrazione.");
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (_) {
      return { kind: "generic", text: raw.slice(0, 500000) };
    }

    const safeData = sanitizeJson(parsed);
    const lowerPath = entry.archivePath.toLowerCase();
    const messages = normalizeConversation(parsed);
    const metadata = legacyMetadata(parsed);
    const looksLikeSettings = lowerPath.includes("settings") || lowerPath.includes("config") ||
      (parsed && typeof parsed === "object" && (parsed.providers || parsed.active_provider));

    if (looksLikeSettings) {
      return {
        kind: "settings",
        text: JSON.stringify(safeData, null, 2),
        notice: "Configurazione storica archiviata senza importare chiavi o provider."
      };
    }

    if (messages.length) {
      const cleanPracticeName = function (value) {
        const cleaned = String(value || "")
          .replace(/^.*[\\/]/, "")
          .replace(/\.(json|zip|html)$/i, "")
          .replace(/^pratica[_\s-]*importata[_\s-]*/i, "")
          .replace(/^case[_\s-]*data[_\s-]*/i, "")
          .replace(/^dati[_\s-]*fascicolo[_\s-]*/i, "")
          .replace(/[_-]+/g, " ")
          .trim();
        return /^(case data|dati fascicolo|conversation|conversazione|chat)$/i.test(cleaned) ? "" : cleaned;
      };
      const candidates = [
        parsed.topic, parsed.argomento, parsed.title, parsed.titolo,
        metadata && metadata.name,
        entry.archivePath,
        sourceArchive,
        entry.safeName
      ];
      const practiceName = candidates.map(cleanPracticeName).find(Boolean) || "Pratica storica";
      const topic = /^pratica\b/i.test(practiceName) ? practiceName : "Pratica " + practiceName;
      const escapeHtml = function (value) {
        return String(value || "").replace(/[&<>"']/g, function (char) {
          return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char];
        });
      };
      const formatLegacyText = function (value) {
        const lines = String(value || "").replace(/\r/g, "").replace(/```[\w-]*/g, "").replace(/```/g, "").split("\n");
        const output = [];
        let list = "";
        const closeList = function () {
          if (list) output.push("</" + list + ">");
          list = "";
        };
        const inline = function (line) {
          return escapeHtml(line)
            .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
            .replace(/__([^_]+)__/g, "<strong>$1</strong>")
            .replace(/(^|[\s(])\*([^*\n]+)\*(?=$|[\s).,;:!?])/g, "$1<em>$2</em>")
            .replace(/`([^`\n]+)`/g, "<code>$1</code>");
        };
        lines.forEach(function (raw) {
          const line = raw.trim();
          if (!line) { closeList(); return; }
          const heading = line.match(/^#{1,6}\s+(.+)$/);
          if (heading) { closeList(); output.push("<h3>" + inline(heading[1]) + "</h3>"); return; }
          const ordered = line.match(/^\d+[.)]\s+(.+)$/);
          const unordered = line.match(/^[-*•]\s+(.+)$/);
          if (ordered || unordered) {
            const type = ordered ? "ol" : "ul";
            if (list !== type) { closeList(); list = type; output.push("<" + type + ">"); }
            output.push("<li>" + inline((ordered || unordered)[1]) + "</li>");
            return;
          }
          closeList();
          output.push("<p>" + inline(line).replace(/^\s*[*#]+\s*/, "") + "</p>");
        });
        closeList();
        return output.join("");
      };
      const body = [
        "<h1>" + escapeHtml(topic) + "</h1>",
        messages.map(function (message) {
          const author = message.role === "utente" ? "Utente" : "LexIA precedente";
          const date = message.timestamp ? " - " + escapeHtml(message.timestamp) : "";
          return "<section><h2>" + author + date + "</h2>" + formatLegacyText(message.content) + "</section>";
        }).join("")
      ].join("");
      return {
        kind: "conversation",
        text: messages.map(function (message) {
          return (message.role === "utente" ? "UTENTE" : "LEXIA PRECEDENTE") + ": " + message.content;
        }).join("\n\n"),
        html: body,
        topic: topic,
        notice: messages.length + " messaggi archiviati in Conversazioni importate; la Consulenza Legale non e' stata modificata."
      };
    }

    if (metadata || lowerPath.endsWith("metadata.json")) {
      const info = metadata || { name: "Fascicolo importato", client: "Non indicato", description: "", created_at: "", status: "" };
      const report = [
        "# Metadati fascicolo LexIA precedente",
        "",
        "- Nome: " + info.name,
        "- Cliente: " + info.client,
        "- Data creazione: " + (info.created_at || "Non indicata"),
        "- Stato: " + (info.status || "Non indicato"),
        "",
        "## Descrizione",
        info.description || "Nessuna descrizione.",
        "",
        "Archivio di origine: " + sourceArchive,
        "Percorso originale: " + entry.archivePath
      ].join("\n");
      return { kind: "metadata", text: report, notice: "Metadati storici convertiti in documento leggibile." };
    }

    return { kind: "generic", text: JSON.stringify(safeData, null, 2), notice: "JSON importato come documento leggibile." };
  }

  function structureFromFiles(files) {
    const result = {};
    CASE_DIRS.forEach(function (dir) { result[dir] = []; });
    files.forEach(function (file) {
      if (!result[file.category]) result[file.category] = [];
      result[file.category].push({ name: file.name, size: file.size, modified: file.modified });
    });
    return result;
  }

  async function parseBody(input, init) {
    if (init && init.body && typeof init.body === "string") return JSON.parse(init.body || "{}");
    if (input instanceof Request) {
      const contentType = input.headers.get("content-type") || "";
      if (contentType.includes("application/json")) return input.clone().json();
    }
    return {};
  }

  function sleep(milliseconds) {
    return new Promise(function (resolve) { setTimeout(resolve, milliseconds); });
  }

  function isTemporaryGeminiError(status, message) {
    const text = String(message || "");
    if (/quota exceeded|current quota|limit:\s*0|billing details|free_tier/i.test(text)) return false;
    return [500, 502, 503, 504].includes(status) ||
      (status === 429 && /high demand|overload|temporar|try again|unavailable|deadline/i.test(text)) ||
      /high demand|overload|temporarily unavailable|server busy/i.test(text);
  }

  function friendlyGeminiError(message) {
    const text = String(message || "");
    if (/quota exceeded|current quota|limit:\s*0|billing details|free_tier/i.test(text)) {
      return "La quota Gemini disponibile per questa chiave è esaurita o non attiva. Attendi il ripristino della quota oppure abilita un piano Google AI a pagamento. La chiave resta salvata solo sul tuo PC.";
    }
    if (/api key|invalid key|permission denied|unauthenticated/i.test(text)) {
      return "La chiave Gemini non è valida o non è autorizzata. Controllala nelle Impostazioni LLM.";
    }
    return text;
  }

  function geminiModelSequence(preferred) {
    return Array.from(new Set([
      preferred || DEFAULT_SETTINGS.providers.gemini.model,
      "gemini-3.5-flash",
      "gemini-3-flash",
      "gemini-3.1-pro",
      "gemini-3.1-flash-lite",
      "gemini-2.5-flash",
      "gemini-2.5-flash-lite",
      "gemini-2.5-pro"
    ].filter(Boolean)));
  }

  async function geminiGenerate(config, payload) {
    const base = String(config.url || DEFAULT_SETTINGS.providers.gemini.url).replace(/\/$/, "");
    const models = geminiModelSequence(config.model);
    let lastError = "Servizio Gemini temporaneamente non disponibile.";
    for (const model of models) {
      for (let attempt = 0; attempt < 2; attempt++) {
        if (attempt > 0) await sleep(1200);
        let response;
        try {
          response = await nativeFetch(base + "/" + encodeURIComponent(model) + ":generateContent?key=" + encodeURIComponent(config.api_key), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
        } catch (error) {
          lastError = error && error.message ? error.message : "Errore di rete verso Gemini.";
          if (attempt === 0) continue;
          break;
        }
        let data = {};
        try {
          data = await response.json();
        } catch (_) {
          data = {};
        }
        if (response.ok) return { data: data, model: model };
        const message = data.error && data.error.message ? data.error.message : "Errore Gemini (" + response.status + ").";
        lastError = message;
        if (!isTemporaryGeminiError(response.status, message)) throw new Error(friendlyGeminiError(message));
        if (attempt === 0) continue;
        break;
      }
    }
    throw new Error(lastError + " LexIA ha già provato automaticamente i modelli alternativi. Riprova tra qualche minuto.");
  }

  function openRouterModelSequence(preferred) {
    return Array.from(new Set([
      preferred,
      "openai/gpt-oss-120b:free",
      "openrouter/free"
    ].filter(Boolean))).slice(0, 3);
  }

  function providerErrorMessage(data, status) {
    const error = data && data.error;
    if (typeof error === "string" && error.trim()) return error;
    if (error && typeof error.message === "string" && error.message.trim()) return error.message;
    if (data && typeof data.message === "string" && data.message.trim()) return data.message;
    return "Errore del provider AI (HTTP " + status + ").";
  }

  function consultationProviderSummary(settings) {
    const provider = settings.active_provider;
    const config = settings.providers && settings.providers[provider] ? settings.providers[provider] : {};
    return {
      provider: provider,
      model: String(config.model || "").trim(),
      hasApiKey: Boolean(String(config.api_key || "").trim()),
      isLocal: provider === "ollama" || provider === "lm_studio"
    };
  }

  function ensureConsultationProviderReady() {
    const settings = readSettings();
    const summary = consultationProviderSummary(settings);
    if (!summary.model) {
      throw new Error("Seleziona un modello nelle Impostazioni prima di usare la Consulenza Legale.");
    }
    if (!summary.isLocal && !summary.hasApiKey) {
      throw new Error("La Consulenza Legale usa la chiave API inserita dall'utente nelle Impostazioni. Inserisci una chiave valida per il provider attivo.");
    }
    return summary;
  }

  function isOpenRouterFallbackError(status, message) {
    return [404, 408, 409, 429, 500, 502, 503, 504].includes(status) ||
      /rate limit|temporar|overload|capacity|provider returned error|no endpoints|model.*unavailable/i.test(String(message || ""));
  }

  async function openRouterGenerate(config, systemPrompt, userPrompt) {
    const models = openRouterModelSequence(config.model);
    let lastError = "OpenRouter non disponibile.";
    for (const model of models) {
      let response;
      const controller = new AbortController();
      const timeoutId = setTimeout(function () { controller.abort(); }, 25000);
      try {
        response = await nativeFetch(String(config.url).replace(/\/$/, "") + "/chat/completions", {
          method: "POST",
          signal: controller.signal,
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.api_key,
            "HTTP-Referer": location.origin,
            "X-Title": "LexIA"
          },
          body: JSON.stringify({
            model: model,
            temperature: 0.2,
            messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userPrompt }]
          })
        });
      } catch (error) {
        lastError = error && error.name === "AbortError"
          ? model + ": tempo massimo di 25 secondi superato"
          : model + ": " + (error && error.message ? error.message : "errore di rete verso OpenRouter");
        continue;
      } finally {
        clearTimeout(timeoutId);
      }
      let data = {};
      try {
        data = await response.json();
      } catch (_) {
        data = {};
      }
      if (response.ok) {
        const content = data.choices && data.choices[0] && data.choices[0].message
          ? data.choices[0].message.content
          : "";
        if (!content) {
          lastError = "Il modello " + model + " ha restituito una risposta vuota.";
          continue;
        }
        return content;
      }
      const message = providerErrorMessage(data, response.status);
      lastError = model + ": " + message;
      if (!isOpenRouterFallbackError(response.status, message)) {
        throw new Error(lastError);
      }
    }
    throw new Error(
      "OpenRouter non ha trovato un modello gratuito disponibile. " +
      lastError +
      " LexIA ha interrotto i tentativi per evitare attese eccessive. Verifica la quota della chiave o riprova più tardi."
    );
  }

  async function callLlm(systemPrompt, userPrompt, options) {
    const settings = readSettings();
    const provider = settings.active_provider;
    const config = settings.providers[provider] || {};
    const allowCloud = options ? Boolean(options.allowCloud) : true;
    if (!config.model) throw new Error("Seleziona un modello nelle Impostazioni.");
    if (!["ollama", "lm_studio"].includes(provider) && !allowCloud) {
      throw new Error("Il provider selezionato e' cloud. Conferma esplicitamente l'invio del testo estratto oppure usa Ollama o LM Studio.");
    }
    if (!config.api_key && provider !== "ollama" && provider !== "lm_studio") {
      throw new Error("Inserisci la chiave API del provider selezionato.");
    }

    if (provider === "gemini") {
      const result = await geminiGenerate(config, {
          contents: [{ role: "user", parts: [{ text: systemPrompt + "\n\nRichiesta:\n" + userPrompt }] }],
          generationConfig: { temperature: 0.2 }
      });
      const data = result.data;
      const parts = data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts;
      if (!parts || !parts[0] || !parts[0].text) throw new Error("Risposta Gemini non valida.");
      return parts.map(function (part) { return part.text || ""; }).join("\n");
    }

    if (provider === "ollama") {
      const response = await nativeFetch(String(config.url).replace(/\/$/, "") + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: config.model,
          stream: false,
          messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userPrompt }]
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Errore Ollama.");
      return data.message && data.message.content ? data.message.content : "";
    }

    if (provider === "openrouter") {
      return openRouterGenerate(config, systemPrompt, userPrompt);
    }

    const response = await nativeFetch(String(config.url).replace(/\/$/, "") + "/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + config.api_key,
        "HTTP-Referer": location.origin,
        "X-Title": "LexIA"
      },
      body: JSON.stringify({
        model: config.model,
        temperature: 0.2,
        messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userPrompt }]
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(providerErrorMessage(data, response.status));
    return data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : "";
  }

  function consultationNoiseScore(line) {
    const value = String(line || "").trim();
    if (!value) return 0;
    let score = 0;
    if (value.length > 180) score += 1;
    if ((value.match(/[|;{}<>]/g) || []).length >= 4) score += 2;
    if ((value.match(/\d+\s*[-–]\s*/g) || []).length >= 2) score += 3;
    if (/^[\d\s\-–—_,.;:()]+$/.test(value)) score += 4;
    if ((value.match(/[A-Z0-9]{8,}/g) || []).length >= 3) score += 2;
    return score;
  }

  function prepareConsultationDocumentText(text) {
    const lines = String(text || "")
      .replace(/\r/g, "")
      .split("\n")
      .map(function (line) { return line.replace(/\s+/g, " ").trim(); });
    const kept = [];
    let totalLength = 0;
    for (const line of lines) {
      if (!line) continue;
      if (consultationNoiseScore(line) >= 4) continue;
      kept.push(line);
      totalLength += line.length + 1;
      if (totalLength >= 12000) break;
    }
    return kept.join("\n").slice(0, 12000).trim();
  }

  function buildConsultationContext(textFiles, history) {
    let context = "";
    if (textFiles.length) {
      const documentBlocks = textFiles.map(function (file) {
        const preparedText = prepareConsultationDocumentText(file.text);
        return preparedText ? "--- DOCUMENTO: " + file.name + " ---\n" + preparedText : "";
      }).filter(Boolean);
      if (documentBlocks.length) {
        context += "Documenti del fascicolo da leggere integralmente prima di qualsiasi sintesi o analisi:\n" + documentBlocks.join("\n\n") + "\n";
      }
    }
    if (history.length) {
      context += "Conversazione precedente:\n" + history.map(function (message) {
        return String(message.role).toUpperCase() + ": " + String(message.content).slice(0, 900);
      }).join("\n") + "\n";
    }
    return context.trim();
  }

  function splitConsultationDocument(file) {
    const raw = prepareConsultationDocumentText(file && file.text ? file.text : "");
    if (!raw) return [];
    const chunkSize = 5000;
    const chunks = [];
    let start = 0;
    while (start < raw.length) {
      let end = Math.min(raw.length, start + chunkSize);
      if (end < raw.length) {
        const breakAt = raw.lastIndexOf("\n", end);
        if (breakAt > start + 1500) end = breakAt;
      }
      chunks.push({
        fileName: file.name,
        index: chunks.length + 1,
        total: 0,
        text: raw.slice(start, end).trim()
      });
      start = end;
    }
    const total = chunks.length;
    return chunks.map(function (chunk) {
      chunk.total = total;
      return chunk;
    });
  }

  async function extractFactsFromDocumentChunk(caseItem, chunk, prompt) {
    const extractionPrompt = [
      "Leggi integralmente il blocco documentale fornito e solo dopo estrai i fatti.",
      "Non interpretare, non integrare, non colmare lacune e non formulare inferenze sui fatti non scritti nei documenti o nella richiesta.",
      "Riporta i fatti nel modo piu' aderente possibile al testo documentale, distinguendo chiaramente tra dato espresso e punto incerto.",
      "Scarta solo sequenze tecniche chiaramente corrotte, dump illeggibili, OCR gravemente sporco e porzioni materialmente incomprensibili.",
      "Restituisci esclusivamente queste sezioni in testo semplice:",
      "1. Fatti emersi dal blocco",
      "2. Date o passaggi cronologici",
      "3. Parti citate",
      "4. Documenti o allegati menzionati",
      "5. Punti incerti o da verificare"
    ].join("\n");
    const caseLabel = caseItem && caseItem.name ? "Fascicolo: " + caseItem.name + "\n" : "";
    return callLlm(
      extractionPrompt,
      caseLabel +
      "Documento: " + chunk.fileName + " (blocco " + chunk.index + " di " + chunk.total + ")\n\n" +
      chunk.text +
      "\n\nRichiesta dell'utente:\n" + prompt
    );
  }

  async function buildConsultationFactsDossier(caseItem, textFiles, prompt, history) {
    const chunkSummaries = [];
    for (const file of textFiles) {
      const chunks = splitConsultationDocument(file);
      if (!chunks.length) continue;
      for (const chunk of chunks) {
        const summary = await extractFactsFromDocumentChunk(caseItem, chunk, prompt);
        chunkSummaries.push(
          "Documento: " + chunk.fileName + " - blocco " + chunk.index + "/" + chunk.total + "\n" + String(summary || "").trim()
        );
      }
    }
    const historyBlock = history.length
      ? "\nConversazione precedente:\n" + history.map(function (message) {
          return String(message.role).toUpperCase() + ": " + String(message.content).slice(0, 900);
        }).join("\n")
      : "";
    const consolidationPrompt = [
      "Unifica i riepiloghi fattuali dei singoli blocchi documentali in un solo dossier coerente.",
      "Non interpretare oltre il testo dei documenti.",
      "Non eliminare fatti rilevanti solo perche' ripetuti: accorpa le ripetizioni mantenendo la sostanza documentale.",
      "Se ci sono conflitti o ambiguita', segnalarli come punti da verificare.",
      "Restituisci esclusivamente queste sezioni in testo semplice:",
      "1. Cronologia essenziale",
      "2. Parti e ruoli",
      "3. Documenti rilevanti",
      "4. Punti da verificare",
      "5. Obiettivo dell'utente"
    ].join("\n");
    return callLlm(
      consolidationPrompt,
      "Riepiloghi fattuali per blocchi:\n\n" + chunkSummaries.join("\n\n") + historyBlock + "\n\nRichiesta dell'utente:\n" + prompt
    );
  }

  async function extractConsultationFacts(context, prompt, caseItem) {
    const extractionPrompt = [
      "Leggi prima integralmente i documenti forniti nel contesto e solo dopo estrai i fatti.",
      "Non interpretare, non integrare, non colmare lacune e non formulare inferenze sui fatti non scritti nei documenti o nella richiesta.",
      "Riporta i fatti nel modo piu' aderente possibile al testo documentale, distinguendo chiaramente tra dato espresso e punto incerto.",
      "Scarta solo sequenze tecniche chiaramente corrotte, dump illeggibili, OCR gravemente sporco e porzioni materialmente incomprensibili.",
      "Se un fatto non e' sufficientemente chiaro, segnalalo come da verificare e non forzare interpretazioni.",
      "Restituisci esclusivamente queste sezioni in testo semplice:",
      "1. Cronologia essenziale",
      "2. Parti e ruoli",
      "3. Documenti rilevanti",
      "4. Punti da verificare",
      "5. Obiettivo dell'utente"
    ].join("\n");
    const caseLabel = caseItem && caseItem.name ? "Fascicolo: " + caseItem.name + "\n" : "";
    return callLlm(
      extractionPrompt,
      caseLabel + (context ? context + "\n\n" : "") + "Richiesta dell'utente:\n" + prompt
    );
  }

  async function generateConsultationAnswer(caseItem, prompt, extractedFacts, history) {
    const historyBlock = history.length
      ? "\nConversazione recente:\n" + history.map(function (message) {
          return String(message.role).toUpperCase() + ": " + String(message.content).slice(0, 500);
        }).join("\n")
      : "";
    const userPrompt = [
      "Usa soltanto i fatti documentali e i punti da verificare qui sotto.",
      "Non interpretare i documenti oltre il loro contenuto letterale.",
      "Non attribuire intenzioni, cause, conseguenze o cronologie che non risultino esplicitamente dai testi.",
      "Prima ricostruisci i fatti cosi' come emergono dai documenti; solo dopo svolgi l'analisi tecnica richiesta.",
      "Quando riassumi, resta aderente al testo documentale e segnala ogni passaggio non espresso con chiarezza.",
      "Non creare tabelle.",
      "Non usare pseudo-colonne con trattini ripetuti.",
      "Non elencare riferimenti documentali corrotti o seriali numeriche.",
      "Se l'utente chiede una cronologia, scrivi prima una narrazione cronologica fedele ai documenti in prosa o elenco semplice.",
      "",
      "Fatti estratti dai documenti:",
      extractedFacts,
      historyBlock,
      "",
      "Richiesta corrente dell'utente:",
      prompt
    ].join("\n");
    return callLlm(SYSTEM_PROMPT, userPrompt);
  }

  async function consultation(caseItem, prompt) {
    ensureConsultationProviderReady();
    const files = await filesForCase(caseItem.id);
    let textFiles = files.filter(function (file) {
      return file.category === "documenti_cliente" && file.consultationIncluded === true && file.text;
    });
    if (!textFiles.length) {
      textFiles = files.filter(function (file) {
        return file.category === "documenti_cliente" && file.text;
      });
    }
    const history = (caseItem.conversation || []).slice(-4);
    let extractedFacts = "";
    const requiresSequentialRead = textFiles.some(function (file) {
      return prepareConsultationDocumentText(file.text).length > 5000;
    });
    if (requiresSequentialRead) {
      extractedFacts = await buildConsultationFactsDossier(caseItem, textFiles, prompt, history);
    } else {
      const context = buildConsultationContext(textFiles, history);
      extractedFacts = await extractConsultationFacts(context, prompt, caseItem);
    }
    let response = await generateConsultationAnswer(caseItem, prompt, extractedFacts, history);
    if (consultationOutputLooksBroken(response)) {
      response = await regenerateConsultationAnswer(caseItem, prompt, extractedFacts, history, response);
    }
    response = normalizeConsultationOutput(response);
    caseItem.conversation = caseItem.conversation || [];
    caseItem.conversation.push({ role: "utente", content: prompt, timestamp: new Date().toISOString() });
    caseItem.conversation.push({ role: "lexia", content: response, timestamp: new Date().toISOString() });
    await putCase(caseItem);
    return response;
  }

  function consultationOutputLooksBroken(text) {
    const value = String(text || "");
    if (!value.trim()) return true;
    if (/(?:\b\d+\s*[-–]\s*){20,}/.test(value)) return true;
    if (/(?:,\s*)?(?:\d+\s*[-–]\s*){20,}/.test(value)) return true;
    if (/Riferimento documentale[\s\S]{0,120}(?:\d+\s*[-–]\s*){10,}/i.test(value)) return true;
    const noisyLines = value.split("\n").filter(function (line) {
      return consultationNoiseScore(line) >= 4;
    });
    return noisyLines.length >= 3;
  }

  async function regenerateConsultationAnswer(caseItem, prompt, extractedFacts, history, previousAnswer) {
    const repairPrompt = [
      "La risposta precedente e' difettosa e non deve essere ripetuta.",
      "Elimina ogni sequenza numerica spuria, ogni pseudo-tabella e ogni riferimento documentale corrotto.",
      "Scrivi in testo lineare chiaro.",
      "Se utile, usa solo elenchi semplici con pochi punti.",
      "",
      "Risposta da correggere:",
      previousAnswer,
      "",
      "Fatti estratti e ripuliti:",
      extractedFacts,
      "",
      "Richiesta dell'utente:",
      prompt
    ].join("\n");
    return generateConsultationAnswer(caseItem, repairPrompt, extractedFacts, history);
  }

  function normalizeConsultationOutput(text) {
    return String(text || "")
      .replace(/\r/g, "")
      .replace(/```[\s\S]*?```/g, function (block) {
        return block.replace(/```/g, "");
      })
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function cleanJsonResponse(text) {
    return String(text || "")
      .replace(/^```(?:json)?\s*/i, "")
      .replace(/\s*```$/, "")
      .trim();
  }

  async function extractCaseProfile(caseItem, allowCloud) {
    const files = await filesForCase(caseItem.id);
    const extractionErrors = [];
    for (const file of files) {
      if (file.category !== "documenti_cliente" || String(file.text || "").trim()) continue;
      if (!/\.(pdf|docx)$/i.test(file.name) || !file.blob) continue;
      try {
        file.text = await documentText(file.blob, file.name);
        if (String(file.text || "").trim()) await putFile(file);
      } catch (error) {
        extractionErrors.push(file.name + ": " + (error && error.message ? error.message : "testo non estraibile"));
      }
    }

    const refreshedFiles = await filesForCase(caseItem.id);
    const readable = refreshedFiles
      .filter(function (file) { return file.category === "documenti_cliente" && String(file.text || "").trim(); })
      .slice(-12);
    if (!readable.length) {
      const detail = extractionErrors.length ? " Dettagli: " + extractionErrors.join("; ") : "";
      throw new Error("Nessun testo estraibile. I PDF scansione richiedono OCR; DOC e immagini non sono ancora supportati." + detail);
    }

    const source = readable.map(function (file) {
      return "--- DOCUMENTO: " + file.name + " ---\n" + String(file.text).slice(0, 12000);
    }).join("\n\n").slice(0, 60000);
    const prompt = [
      "Analizza esclusivamente i documenti forniti e restituisci solo JSON valido.",
      "Non inventare dati. Per ogni valore non trovato usa una stringa vuota.",
      "Campi richiesti:",
      "querelante_nome, querelante_codice_fiscale, querelante_indirizzo, querelante_pec,",
      "controparte_nome, controparte_codice_fiscale, controparte_indirizzo, controparte_pec,",
      "ente_destinatario_nome, ente_destinatario_indirizzo, ente_destinatario_pec, note.",
      "Nelle note indica brevemente documenti e incertezze usate per l'estrazione.",
      "",
      source
    ].join("\n");
    const raw = await callLlm(
      "Sei un estrattore di dati legali. Devi copiare fedelmente i dati dai documenti, senza inferenze non dimostrate.",
      prompt,
      { allowCloud: Boolean(allowCloud) }
    );
    let extracted;
    try {
      extracted = JSON.parse(cleanJsonResponse(raw));
    } catch (_) {
      throw new Error("Il modello locale non ha restituito dati strutturati validi.");
    }

    const allowed = [
      "querelante_nome", "querelante_codice_fiscale", "querelante_indirizzo", "querelante_pec",
      "controparte_nome", "controparte_codice_fiscale", "controparte_indirizzo", "controparte_pec",
      "ente_destinatario_nome", "ente_destinatario_indirizzo", "ente_destinatario_pec", "note"
    ];
    const profile = {};
    allowed.forEach(function (key) { profile[key] = String(extracted[key] || "").trim(); });
    return { profile: profile, sources: readable.map(function (file) { return file.name; }) };
  }

  function actTemplate(type, values) {
    const kind = String(type || "atto").toLowerCase();
    const value = function (key, fallback) {
      return String(values[key] || "").trim() || fallback;
    };
    const destination = [
      value("TRIBUNALE", value("DESTINATION_NAME", "Destinatario da indicare")),
      value("DESTINATION_ADDRESS", ""),
      values.DESTINATION_PEC ? "PEC: " + values.DESTINATION_PEC : ""
    ].filter(Boolean).join("\n");
    const client = [
      value("CLIENT_NAME", "Persona interessata da indicare"),
      values.CLIENT_BORN ? "nata/o a/il: " + values.CLIENT_BORN : "",
      values.CLIENT_FC ? "C.F.: " + values.CLIENT_FC : "",
      values.CLIENT_ADDRESS ? "residente/con sede in: " + values.CLIENT_ADDRESS : ""
    ].filter(Boolean).join(", ");
    const opponent = [
      value("OPPONENT_NAME", "soggetto da identificare"),
      values.OPPONENT_ADDRESS ? "con recapito/sede in " + values.OPPONENT_ADDRESS : ""
    ].filter(Boolean).join(", ");
    const lawyer = values.LAWYER_NAME
      ? "\nAssistita/o dall'Avv. " + values.LAWYER_NAME + (values.LAWYER_ADDRESS ? ", con studio in " + values.LAWYER_ADDRESS : "") + "."
      : "";
    const facts = value("FACTS", "[Descrivere cronologicamente i fatti, indicando date, luoghi, condotte e documenti di riscontro.]");
    const law = value("ARTICLES", "[Indicare le norme applicabili dopo verifica.]");
    const common = {
      querela: {
        title: "ATTO DI QUERELA",
        intro: "La/Il sottoscritta/o " + client + lawyer + ", in qualita' di persona offesa, espone quanto segue.",
        lawTitle: "QUALIFICAZIONE GIURIDICA E VOLONTA' PUNITIVA",
        request: "Tutto cio' premesso, propone formale querela nei confronti di " + opponent + " e di chiunque altro risulti responsabile, manifestando espressamente la volonta' che si proceda penalmente e che siano applicate le sanzioni previste dalla legge.\nChiede di essere avvisata/o dell'eventuale richiesta di archiviazione ai sensi dell'art. 408, comma 2, c.p.p.",
        close: "Si indicano quali fonti di prova e allegati: [elencare documenti, persone informate e ulteriori elementi].\nLuogo e data: [da completare]\nFirma della persona offesa: ____________________"
      },
      denuncia: {
        title: "DENUNCIA",
        intro: "La/Il sottoscritta/o " + client + lawyer + " porta a conoscenza dell'Autorita' i seguenti fatti, affinche' ne valuti l'eventuale rilevanza penale.",
        lawTitle: "POSSIBILE RILEVANZA GIURIDICA",
        request: "Si chiede all'Autorita' competente di svolgere gli accertamenti ritenuti opportuni e di procedere nei confronti di " + opponent + " e di ogni altro eventuale responsabile, qualora ne ricorrano i presupposti.",
        close: "Documenti e fonti di prova: [elencare].\nLuogo e data: [da completare]\nFirma: ____________________"
      },
      esposto: {
        title: "ESPOSTO",
        intro: "La/Il sottoscritta/o " + client + lawyer + " sottopone all'attenzione dell'Autorita' la situazione di seguito descritta.",
        lawTitle: "PROFILI DA VALUTARE",
        request: "Si chiede di valutare i fatti esposti e di adottare, nell'ambito delle rispettive competenze, gli interventi ritenuti opportuni.",
        close: "Allegati: [elencare].\nLuogo e data: [da completare]\nFirma: ____________________"
      },
      diffida: {
        title: "DIFFIDA E MESSA IN MORA",
        intro: "La/Il sottoscritta/o " + client + lawyer + " con la presente si rivolge a " + opponent + ".",
        lawTitle: "TITOLO E FONDAMENTO DELLA PRETESA",
        request: "Pertanto, si diffida formalmente la controparte ad adempiere a quanto dovuto entro [indicare termine congruo] dal ricevimento della presente, con espresso avvertimento che, in difetto, saranno intraprese le opportune iniziative a tutela dei diritti e per il risarcimento dei danni, senza ulteriore avviso.",
        close: "La presente vale quale costituzione in mora nei limiti e ricorrendone i presupposti di legge.\nLuogo e data: [da completare]\nFirma: ____________________"
      },
      istanza: {
        title: "ISTANZA",
        intro: "La/Il sottoscritta/o " + client + lawyer + ", quale soggetto interessato al procedimento, espone quanto segue.",
        lawTitle: "PRESUPPOSTI DELL'ISTANZA",
        request: "Per tali ragioni, chiede che l'Ufficio voglia [indicare con precisione il provvedimento o l'attivita' richiesta] e comunicare l'esito al recapito indicato.",
        close: "Documenti allegati: [elencare].\nLuogo e data: [da completare]\nFirma: ____________________"
      },
      memoria: {
        title: "MEMORIA DIFENSIVA",
        intro: "Nell'interesse di " + client + lawyer + ", nel procedimento [numero/ruolo da indicare], si espongono le seguenti difese.",
        lawTitle: "MOTIVI IN DIRITTO",
        request: "Alla luce dei fatti e delle ragioni esposte, si chiede l'accoglimento delle conclusioni di seguito precisate: [formulare conclusioni coerenti con rito e fase].",
        close: "Produzioni documentali: [elencare].\nLuogo e data: [da completare]\nFirma del difensore: ____________________"
      },
      "atto di citazione": {
        title: "ATTO DI CITAZIONE",
        intro: "Nell'interesse di " + client + lawyer + ", si espongono i fatti e i motivi posti a fondamento della domanda nei confronti di " + opponent + ".",
        lawTitle: "MOTIVI IN DIRITTO",
        request: "Tutto cio' premesso, cita " + opponent + " a comparire dinanzi all'Autorita' giudiziaria indicata, all'udienza del [data da determinare nel rispetto dei termini], con gli avvertimenti prescritti dalla legge, per ivi sentir accogliere le seguenti conclusioni: [formulare domande e richieste istruttorie].",
        close: "Valore della controversia e contributo unificato: [verificare].\nMezzi di prova e documenti: [elencare].\nLuogo, data e firma del difensore: ____________________"
      },
      ricorso: {
        title: "RICORSO",
        intro: "La/Il ricorrente " + client + lawyer + " espone quanto segue nei confronti di " + opponent + ".",
        lawTitle: "MOTIVI DEL RICORSO",
        request: "Per questi motivi, chiede all'Autorita' adita di [formulare il provvedimento richiesto], previa adozione degli adempimenti previsti dal rito applicabile.",
        close: "Documenti e mezzi di prova: [elencare].\nLuogo, data e firma: ____________________"
      },
      comparsa: {
        title: "COMPARSA DI COSTITUZIONE E RISPOSTA",
        intro: "Nell'interesse di " + client + lawyer + ", convenuta/o nel procedimento promosso da " + opponent + ", ci si costituisce esponendo quanto segue.",
        lawTitle: "DIFESE, ECCEZIONI E DOMANDE",
        request: "Si chiede il rigetto delle domande avversarie per i motivi esposti e l'accoglimento delle seguenti conclusioni: [indicare eccezioni, eventuali riconvenzionali e richieste istruttorie].",
        close: "Documenti e mezzi di prova: [elencare].\nLuogo, data e firma del difensore: ____________________"
      },
      "parere pro veritate": {
        title: "PARERE PRO VERITATE",
        intro: "Richiedente: " + client + ".\nQuesito: [formulare con precisione il quesito sottoposto].",
        lawTitle: "INQUADRAMENTO NORMATIVO E ANALISI",
        request: "Valutazione: distinguere gli elementi documentati, le interpretazioni possibili, gli orientamenti giurisprudenziali verificati e i rischi delle diverse opzioni.",
        close: "CONCLUSIONI\n[Esprimere la soluzione motivata, i limiti del parere e gli ulteriori accertamenti necessari.]\nLuogo, data e firma: ____________________"
      }
    };
    const preset = common[kind] || common.istanza;
    return [
      destination,
      "",
      preset.title,
      "",
      preset.intro,
      "",
      "FATTI",
      facts,
      "",
      preset.lawTitle,
      law,
      "",
      "RICHIESTE / CONCLUSIONI",
      preset.request,
      "",
      preset.close,
      "",
      "AVVERTENZA: bozza preparatoria. Verificare competenza, rito, termini, fatti, qualificazione giuridica, norme vigenti, allegati, procura, notificazione/deposito e sottoscrizioni prima dell'uso."
    ].join("\n");
  }

  async function route(input, init) {
    const requestUrl = new URL(input instanceof Request ? input.url : String(input), location.href);
    const apiBase = APP_BASE + "/api/";
    if (!requestUrl.pathname.startsWith(apiBase) && !requestUrl.pathname.startsWith("/api/")) return null;
    const method = String((init && init.method) || (input instanceof Request && input.method) || "GET").toUpperCase();
    const normalizedPath = requestUrl.pathname.startsWith(APP_BASE + "/")
      ? requestUrl.pathname.slice(APP_BASE.length)
      : requestUrl.pathname;
    const parts = normalizedPath.split("/").filter(Boolean);

    try {
      if (parts[1] === "settings") {
        if (method === "GET") return json(readSettings());
        if (method === "POST") return json(saveSettings(await parseBody(input, init)));
      }

      if (parts[1] !== "cases") return failure(404, "Endpoint non disponibile.");

      if (parts.length === 2) {
        if (method === "GET") return json(await listCases());
        if (method === "POST") {
          const payload = await parseBody(input, init);
          if (!String(payload.name || "").trim()) return failure(422, "Il nome del fascicolo e' obbligatorio.");
          const item = newCase(payload, false);
          await putCase(item);
          return json(metadataOnly(item));
        }
      }

      if (parts[2] === "temp_case" && parts[3] === "reset" && method === "POST") {
        return json(await resetTempCase());
      }

      if (parts[2] === "temp_case" && parts[3] === "convert" && method === "POST") {
        const payload = await parseBody(input, init);
        const temp = await getCase("temp_case");
        const item = newCase(payload, false);
        item.conversation = temp && temp.conversation ? temp.conversation : [];
        await putCase(item);
        await resetTempCase();
        return json(metadataOnly(item));
      }

      if (parts[2] === "temp_case" && parts[3] === "extract-details" && method === "POST") {
        const temp = await getCase("temp_case");
        const history = temp && temp.conversation ? temp.conversation : [];
        const text = await callLlm(
          "Restituisci esclusivamente JSON valido con le chiavi name, client e description.",
          history.map(function (message) { return message.role + ": " + message.content; }).join("\n")
        );
        const cleaned = text.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
        try {
          return json(JSON.parse(cleaned));
        } catch (_) {
          return json({ name: "Consulenza da definire", client: "Da definire", description: text });
        }
      }

      const caseId = safeSegment(parts[2]);
      const item = await getCase(caseId);
      if (!item) return failure(404, "Fascicolo non trovato.");

      if (parts.length === 3) {
        if (method === "GET") {
          return json({
            metadata: metadataOnly(item),
            structure: structureFromFiles(await filesForCase(caseId)),
            conversation: item.conversation || []
          });
        }
        if (method === "DELETE") {
          await deleteCaseAndFiles(caseId);
          return json({ status: "success" });
        }
      }

      if (parts[3] === "profile") {
        if (method === "GET") return json({ profile: item.profile || {} });
        if (method === "POST") {
          const payload = await parseBody(input, init);
          item.profile = payload && typeof payload === "object" ? clone(payload) : {};
          await putCase(item);
          return json({ status: "success", profile: item.profile });
        }
      }

      if (parts[3] === "extract-profile" && method === "POST") {
        const payload = await parseBody(input, init);
        return json(await extractCaseProfile(item, payload.allow_cloud));
      }

      if (parts[3] === "notes" && method === "POST") {
        const payload = await parseBody(input, init);
        const name = uniqueName(await filesForCase(caseId), "note_utente", String(payload.title || "nota") + ".txt");
        const blob = new Blob([String(payload.content || "")], { type: "text/plain" });
        await putFile({ key: caseId + "/note_utente/" + name, caseId: caseId, category: "note_utente", name: name, size: blob.size, modified: new Date().toISOString(), blob: blob, text: String(payload.content || "") });
        return json({ status: "success", filename: name });
      }

      if (parts[3] === "consult" && method === "POST") {
        const payload = await parseBody(input, init);
        return json({ response: await consultation(item, String(payload.prompt || "")) });
      }
      if (parts[3] === "consult" && method === "DELETE") {
        item.conversation = [];
        await putCase(item);
        return json({ status: "success" });
      }

      if (parts[3] === "doc-generate" && method === "POST") {
        const payload = await parseBody(input, init);
        const documentText = actTemplate(payload.doc_type, payload.variables || {});
        const name = uniqueName(await filesForCase(caseId), "documenti_generati", String(payload.doc_type || "atto").replace(/\s+/g, "_") + ".txt");
        const blob = new Blob([documentText], { type: "text/plain" });
        await putFile({ key: caseId + "/documenti_generati/" + name, caseId: caseId, category: "documenti_generati", name: name, size: blob.size, modified: new Date().toISOString(), blob: blob, text: documentText });
        return json({ document: documentText, filename: name });
      }

      if (parts[3] === "strategy" && method === "POST") {
        const payload = await parseBody(input, init);
        const strategy = await callLlm(SYSTEM_PROMPT + " Produci una matrice strategica prudente e una tabella di marcia.", String(payload.case_summary || ""));
        return json({ strategy: strategy });
      }

      if (parts[3] === "witness" && method === "POST") {
        const p = await parseBody(input, init);
        const sheet = "# Scheda Testimone\n\n- Nome: " + (p.name || "") + "\n- Ruolo: " + (p.role || "") + "\n- Contatti: " + (p.contact || "") + "\n- Rilevanza: " + (p.relevance || "") + "\n\n## Fatti\n" + (p.facts || "");
        const name = uniqueName(await filesForCase(caseId), "schede_testimoni", "testimone_" + (p.name || "senza_nome") + ".txt");
        const blob = new Blob([sheet], { type: "text/plain" });
        await putFile({ key: caseId + "/schede_testimoni/" + name, caseId: caseId, category: "schede_testimoni", name: name, size: blob.size, modified: new Date().toISOString(), blob: blob, text: sheet });
        return json({ sheet: sheet, filename: name });
      }

      if (parts[3] === "pec-search" && method === "POST") {
        return failure(503, "Ricerca PEC remota disattivata in modalita' locale privata.");
      }

      if (parts[3] === "people-search" && method === "POST") {
        return failure(503, "Ricerca anagrafica remota disattivata in modalita' locale privata.");
      }

      if (parts[3] === "transcribe" && method === "POST") {
        return failure(501, "La trascrizione audio remota e' disattivata in modalita' locale privata.");
      }

      if (parts[3] === "documents") {
        const existing = await filesForCase(caseId);
        if (parts.length === 4 && method === "GET") {
          return json({ documents: existing.filter(function (file) { return file.category === "documenti_cliente"; }).map(function (file) {
            return { name: file.name, archivePath: file.archivePath || "", sourceArchive: file.sourceArchive || "", size: file.size, modified: file.modified, ext: "." + (file.name.split(".").pop() || ""), consultationIncluded: file.consultationIncluded === true };
          }) });
        }
        if (parts.length === 4 && method === "POST") {
          const form = init && init.body instanceof FormData ? init.body : await input.clone().formData();
          const uploaded = [];
          const errors = [];
          for (const file of form.getAll("files")) {
            try {
              if (!(file instanceof File)) continue;
              if (/\.zip$/i.test(file.name)) {
                const extracted = await extractZip(file);
                if (!extracted.length) throw new Error("Lo ZIP non contiene documenti supportati.");
                for (const entry of extracted) {
                  const currentFiles = await filesForCase(caseId);
                  const name = uniqueName(currentFiles, "documenti_cliente", entry.safeName);
                  let text = await documentText(entry.blob, name);
                  let migrationNotice = "";
                  let storedBlob = entry.blob;
                  let category = "documenti_cliente";
                  let html = "";
                  let topic = "";
                  if (/\.json$/i.test(name)) {
                    const migration = await importLegacyJson(item, entry, file.name);
                    text = migration.text;
                    migrationNotice = migration.notice || "";
                    if (migration.kind === "conversation") {
                      category = "conversazioni_importate";
                      html = migration.html || "";
                      topic = migration.topic || "";
                      storedBlob = new Blob([html], { type: "text/html" });
                    } else {
                      storedBlob = new Blob([text], { type: "application/json" });
                    }
                  }
                  const storedName = category === "conversazioni_importate"
                    ? uniqueName(currentFiles, category, name.replace(/\.json$/i, "") + ".html")
                    : name;
                  await putFile({
                    key: caseId + "/" + category + "/" + storedName,
                    caseId: caseId,
                    category: category,
                    name: storedName,
                    archivePath: entry.archivePath,
                    sourceArchive: file.name,
                    migrationNotice: migrationNotice,
                    html: html,
                    topic: topic,
                    size: storedBlob.size,
                    modified: new Date().toISOString(),
                    blob: storedBlob,
                    text: text,
                    consultationIncluded: category === "documenti_cliente"
                  });
                  uploaded.push({
                    file: storedName,
                    archivePath: entry.archivePath,
                    sourceArchive: file.name,
                    size: storedBlob.size,
                    preview: text.slice(0, 500),
                    notice: migrationNotice
                  });
                }
              } else {
                const name = uniqueName(await filesForCase(caseId), "documenti_cliente", file.name);
                let text = await documentText(file, name);
                let migrationNotice = "";
                let storedBlob = file;
                let category = "documenti_cliente";
                let html = "";
                let topic = "";
                if (/\.json$/i.test(name)) {
                  const migration = await importLegacyJson(item, {
                    archivePath: file.name,
                    safeName: file.name,
                    blob: file
                  }, file.name);
                  text = migration.text;
                  migrationNotice = migration.notice || "";
                  if (migration.kind === "conversation") {
                    category = "conversazioni_importate";
                    html = migration.html || "";
                    topic = migration.topic || "";
                    storedBlob = new Blob([html], { type: "text/html" });
                  } else {
                    storedBlob = new Blob([text], { type: "application/json" });
                  }
                }
                const storedName = category === "conversazioni_importate"
                  ? uniqueName(await filesForCase(caseId), category, name.replace(/\.json$/i, "") + ".html")
                  : name;
                await putFile({ key: caseId + "/" + category + "/" + storedName, caseId: caseId, category: category, name: storedName, migrationNotice: migrationNotice, html: html, topic: topic, size: storedBlob.size, modified: new Date().toISOString(), blob: storedBlob, text: text, consultationIncluded: category === "documenti_cliente" });
                uploaded.push({ file: storedName, size: storedBlob.size, preview: text.slice(0, 500), notice: migrationNotice });
              }
            } catch (error) {
              errors.push({ file: file.name, error: error.message });
            }
          }
          return json({ uploaded: uploaded, errors: errors });
        }
        if (parts.length === 5 && method === "DELETE") {
          const name = safeSegment(parts[4]);
          await deleteFile(caseId + "/documenti_cliente/" + name);
          return json({ status: "success" });
        }
        if (parts.length === 6 && parts[5] === "consultation" && method === "POST") {
          const name = safeSegment(parts[4]);
          const payload = await parseBody(input, init);
          const file = existing.find(function (candidate) {
            return candidate.category === "documenti_cliente" && candidate.name === name;
          });
          if (!file) return failure(404, "Documento non trovato.");
          file.consultationIncluded = payload.included === true;
          await putFile(file);
          return json({ status: "success", consultationIncluded: file.consultationIncluded });
        }
      }

      if (parts[3] === "legacy-conversations") {
        if (method === "GET" && parts.length === 4) {
          const files = (await filesForCase(caseId)).filter(function (file) {
            return file.category === "conversazioni_importate";
          });
          return json({ documents: files.map(function (file) {
            return { name: file.name, topic: file.topic || file.name.replace(/\.html$/i, ""), sourceArchive: file.sourceArchive || "", archivePath: file.archivePath || "", modified: file.modified, size: file.size };
          }) });
        }
        if (parts.length === 5 && method === "GET") {
          const name = safeSegment(parts[4]);
          const file = (await filesForCase(caseId)).find(function (candidate) {
            return candidate.category === "conversazioni_importate" && candidate.name === name;
          });
          if (!file) return failure(404, "Conversazione importata non trovata.");
          return json({ name: file.name, topic: file.topic || "", html: file.html || "", sourceArchive: file.sourceArchive || "", archivePath: file.archivePath || "" });
        }
        if (parts.length === 5 && method === "POST") {
          const name = safeSegment(parts[4]);
          const payload = await parseBody(input, init);
          const file = (await filesForCase(caseId)).find(function (candidate) {
            return candidate.category === "conversazioni_importate" && candidate.name === name;
          });
          if (!file) return failure(404, "Conversazione importata non trovata.");
          file.html = String(payload.html || "").slice(0, 1000000);
          file.text = String(payload.text || "").slice(0, 500000);
          file.modified = new Date().toISOString();
          file.blob = new Blob([file.html], { type: "text/html" });
          file.size = file.blob.size;
          await putFile(file);
          return json({ status: "success", modified: file.modified });
        }
      }

      if (parts[3] === "document-editor" && parts.length === 5) {
        const name = safeSegment(parts[4]);
        const file = (await filesForCase(caseId)).find(function (candidate) {
          return candidate.category === "documenti_cliente" && candidate.name === name;
        });
        if (!file) return failure(404, "Documento non trovato.");
        if (method === "GET") {
          if (!file.text && file.blob) {
            file.text = await documentText(file.blob, file.name);
            if (file.text) await putFile(file);
          }
          const extension = (file.name.split(".").pop() || "").toLowerCase();
          if (extension === "eml" && !file.editorModified && file.blob) {
            file.editorHtml = extractEmlHtml(await file.blob.text());
            file.editorText = file.text || "";
            await putFile(file);
          }
          if (extension === "pdf" && !file.editorModified) {
            const emailHtml = extractedEmailHtml(file.text || "");
            if (emailHtml && file.editorHtml !== emailHtml) {
              file.editorHtml = emailHtml;
              file.editorText = file.text || "";
              await putFile(file);
            }
          }
          const editable = Boolean(file.editorHtml || file.text || ["txt", "md", "csv", "rtf", "json", "eml", "html", "htm", "xml", "log", "docx", "odt", "pdf"].includes(extension));
          return json({
            name: file.name,
            extension: extension,
            editable: editable,
            html: file.editorHtml || "",
            text: file.editorText || file.text || "",
            originalPreserved: true,
            modified: file.modified
          });
        }
        if (method === "POST") {
          const payload = await parseBody(input, init);
          file.editorHtml = String(payload.html || "").slice(0, 1000000);
          file.editorText = String(payload.text || "").slice(0, 500000);
          file.editorModified = new Date().toISOString();
          await putFile(file);
          return json({ status: "success", editorModified: file.editorModified });
        }
      }

      if (parts[3] === "files" && method === "GET") {
        const category = safeSegment(parts[4]);
        let name = safeSegment(parts.slice(5).join("/"));
        const files = await filesForCase(caseId);
        if (name.endsWith(".estratto.txt")) {
          name = name.slice(0, -".estratto.txt".length);
          const source = files.find(function (file) { return file.category === category && file.name === name; });
          if (!source || !source.text) return new Response("Anteprima non disponibile.", { status: 404 });
          return new Response(source.text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
        }
        const file = files.find(function (candidate) { return candidate.category === category && candidate.name === name; });
        if (!file) return new Response("File non trovato.", { status: 404 });
        return new Response(file.blob, {
          headers: {
            "Content-Type": file.blob.type || "application/octet-stream",
            "Content-Disposition": "inline; filename=\"" + file.name.replace(/"/g, "") + "\""
          }
        });
      }

      return failure(404, "Endpoint non disponibile nella modalita' browser.");
    } catch (error) {
      console.error("LexIA browser API:", error);
      return failure(500, error && error.message ? error.message : "Errore interno.");
    }
  }

  window.fetch = async function (input, init) {
    const response = await route(input, init);
    return response || nativeFetch(input, init);
  };
  window.LexiaBrowserApi = {
    active: true,
    mode: "local-private",
    transport: "fetch-intercept",
    settingsKey: SETTINGS_KEY,
    dbName: DB_NAME,
    exportLocalBackup: exportLocalBackup,
    restoreLocalBackup: restoreLocalBackup
  };
})();
