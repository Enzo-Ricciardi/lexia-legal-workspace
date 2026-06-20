import os
import json
import tempfile
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx

from tools.file_manager import CaseFileManager
from tools.conv_logger import ConversationLogger
from tools.doc_binder import DocumentBinder
from tools.transcriber import AudioTranscriber
from tools.people_search import PeopleSearchEngine
from tools.pec_search import PecSearchEngine
from tools.doc_generator import DocumentGenerator
from tools.witness_builder import WitnessDataBuilder
from tools.doc_ingestor import DocumentIngestor, ACCEPTED_EXTS
from tools import paths

app = FastAPI(title="LexIA API", description="Server per l'applicazione multi-agente LexIA")
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

# Local development origins only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Static files path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Models for request validation
class CaseCreateRequest(BaseModel):
    name: str
    client: str
    description: str
    history: Optional[List[Dict[str, Any]]] = None

class AnonymousConsultRequest(BaseModel):
    prompt: str
    history: List[Dict[str, str]]

class ConsultRequest(BaseModel):
    prompt: str

class NoteRequest(BaseModel):
    title: str
    content: str

class PeopleSearchRequest(BaseModel):
    name: str
    tax_code: Optional[str] = ""
    vat: Optional[str] = ""
    address: Optional[str] = ""

class PecSearchRequest(BaseModel):
    query: str

class DocGenerateRequest(BaseModel):
    doc_type: str
    variables: Dict[str, Any]

class WitnessRequest(BaseModel):
    name: str
    role: str
    contact: str
    relevance: str
    facts: str

class StrategyRequest(BaseModel):
    case_summary: str

class CaseProfileRequest(BaseModel):
    querelante_nome: Optional[str] = ""
    querelante_codice_fiscale: Optional[str] = ""
    querelante_indirizzo: Optional[str] = ""
    querelante_pec: Optional[str] = ""
    controparte_nome: Optional[str] = ""
    controparte_codice_fiscale: Optional[str] = ""
    controparte_indirizzo: Optional[str] = ""
    controparte_pec: Optional[str] = ""
    ente_destinatario_nome: Optional[str] = ""
    ente_destinatario_indirizzo: Optional[str] = ""
    ente_destinatario_pec: Optional[str] = ""
    note: Optional[str] = ""


LOCAL_ONLY_MESSAGE = (
    "LexIA pubblica usa esclusivamente provider configurati sul device dell'utente. "
    "Questo endpoint server-side non e' disponibile."
)

# ----------------- UI ROUTE -----------------
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <head><title>LexIA Dashboard</title></head>
        <body style="font-family:sans-serif; text-align:center; padding:50px; background:#0f172a; color:#f8fafc;">
            <h1>LexIA - Diritto Certo</h1>
            <p>Caricamento interfaccia in corso o template index.html non trovato.</p>
        </body>
    </html>
    """


@app.get("/cases/{case_id}", response_class=HTMLResponse)
async def get_case_workspace(case_id: str):
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Template UI non trovato.")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

# ----------------- CASES ENDPOINTS -----------------
@app.get("/api/cases")
async def get_cases():
    return CaseFileManager.list_cases()

@app.post("/api/cases")
async def create_case(req: CaseCreateRequest):
    try:
        return CaseFileManager.create_case(req.name, req.client, req.description, req.history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases/temp_case/reset")
async def reset_temporary_case():
    try:
        return CaseFileManager.create_temporary_case()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases/temp_case/convert")
async def convert_temporary_case(req: CaseCreateRequest):
    try:
        return CaseFileManager.convert_temporary_case(req.name, req.client, req.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases/{case_id}/extract-details")
async def extract_details(case_id: str):
    raise HTTPException(status_code=410, detail=LOCAL_ONLY_MESSAGE)

@app.get("/api/cases/{case_id}")
async def get_case_details(case_id: str):
    try:
        metadata = CaseFileManager.get_case(case_id)
        structure = CaseFileManager.get_case_structure(case_id)
        conversation = ConversationLogger.get_conversation(case_id)
        return {
            "metadata": metadata,
            "structure": structure,
            "conversation": conversation
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    try:
        CaseFileManager.delete_case(case_id)
        return {"status": "success", "message": f"Fascicolo {case_id} eliminato."}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cases/{case_id}/profile")
async def get_case_profile(case_id: str):
    try:
        metadata = CaseFileManager.get_case(case_id)
        return {"profile": metadata.get("profile", {})}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/cases/{case_id}/profile")
async def save_case_profile(case_id: str, req: CaseProfileRequest):
    try:
        metadata = CaseFileManager.get_case(case_id)
        profile = {
            "querelante_nome": req.querelante_nome or "",
            "querelante_codice_fiscale": req.querelante_codice_fiscale or "",
            "querelante_indirizzo": req.querelante_indirizzo or "",
            "querelante_pec": req.querelante_pec or "",
            "controparte_nome": req.controparte_nome or "",
            "controparte_codice_fiscale": req.controparte_codice_fiscale or "",
            "controparte_indirizzo": req.controparte_indirizzo or "",
            "controparte_pec": req.controparte_pec or "",
            "ente_destinatario_nome": req.ente_destinatario_nome or "",
            "ente_destinatario_indirizzo": req.ente_destinatario_indirizzo or "",
            "ente_destinatario_pec": req.ente_destinatario_pec or "",
            "note": req.note or "",
        }
        metadata["profile"] = profile
        case_path = paths.case_path(case_id)
        with open(os.path.join(case_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return {"status": "success", "profile": profile}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases/{case_id}/notes")
async def add_case_note(case_id: str, req: NoteRequest):
    try:
        filename = CaseFileManager.add_note(case_id, req.title, req.content)
        return {"status": "success", "filename": filename}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- CONSULT ENDPOINT -----------------
@app.post("/api/cases/{case_id}/consult")
async def consult_agent(case_id: str, req: ConsultRequest):
    raise HTTPException(status_code=410, detail=LOCAL_ONLY_MESSAGE)

# ----------------- INVESTIGATIVE SUITE ENDPOINTS -----------------
@app.post("/api/cases/{case_id}/transcribe")
async def transcribe_audio(case_id: str, file: UploadFile = File(...)):
    temp_path = None
    try:
        CaseFileManager.get_case(case_id)
        temp_dir = "/tmp/lexia_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        original_name = os.path.basename(file.filename or "audio")
        suffix = os.path.splitext(original_name)[1][:12]
        fd, temp_path = tempfile.mkstemp(prefix="lexia_audio_", suffix=suffix, dir=temp_dir)
        os.close(fd)
        with open(temp_path, "wb") as buffer:
            size = 0
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    raise ValueError("Il file supera il limite di 50 MB.")
                buffer.write(chunk)
            
        # Perform transcription
        transcription_text = AudioTranscriber.transcribe(temp_path)
        
        # Save results directly in case folder
        base_name = "".join(
            char for char in os.path.splitext(original_name)[0]
            if char.isalnum() or char in "._-"
        ) or "audio"
        report_filename = f"trascrizione_{base_name}.txt"
        
        DocumentBinder.save_raw_to_case(
            case_id=case_id,
            filename=report_filename,
            content=transcription_text,
            category="trascrizioni_audio"
        )
        
        return {"status": "success", "text": transcription_text, "filename": report_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/cases/{case_id}/people-search")
async def people_search(case_id: str, req: PeopleSearchRequest):
    try:
        report_data = PeopleSearchEngine.search_data(
            req.name, req.tax_code, req.vat, req.address,
            openapi_token=""
        )
        report_md = PeopleSearchEngine.generate_markdown_report(report_data)
        
        filename = f"report_soggetto_{req.name.lower().replace(' ', '_')}.md"
        DocumentBinder.save_raw_to_case(
            case_id=case_id,
            filename=filename,
            content=report_md,
            category="ricerche_investigative"
        )
        
        return {"status": "success", "report": report_md, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases/{case_id}/pec-search")
async def pec_search(case_id: str, req: PecSearchRequest):
    try:
        search_result = PecSearchEngine.search(req.query)
        report_md = PecSearchEngine.generate_report(search_result)
        
        filename = f"ricerca_pec_{req.query.lower().replace(' ', '_')}.md"
        DocumentBinder.save_raw_to_case(
            case_id=case_id,
            filename=filename,
            content=report_md,
            category="ricerche_pec"
        )
        
        return {"status": "success", "report": report_md, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- DOCUMENT BUILDER ENDPOINTS -----------------
@app.post("/api/cases/{case_id}/doc-generate")
async def generate_document(case_id: str, req: DocGenerateRequest):
    try:
        metadata = CaseFileManager.get_case(case_id)
        profile = metadata.get("profile", {})
        merged_variables = {
            **profile,
            **req.variables,
            "CLIENT_NAME": req.variables.get("CLIENT_NAME") or profile.get("querelante_nome") or metadata.get("client", ""),
            "CLIENT_FC": req.variables.get("CLIENT_FC") or profile.get("querelante_codice_fiscale", ""),
            "CLIENT_ADDRESS": req.variables.get("CLIENT_ADDRESS") or profile.get("querelante_indirizzo", ""),
            "OPPONENT_NAME": req.variables.get("OPPONENT_NAME") or profile.get("controparte_nome", ""),
            "OPPONENT_FC": req.variables.get("OPPONENT_FC") or profile.get("controparte_codice_fiscale", ""),
            "OPPONENT_ADDRESS": req.variables.get("OPPONENT_ADDRESS") or profile.get("controparte_indirizzo", ""),
            "DESTINATION_NAME": req.variables.get("DESTINATION_NAME") or profile.get("ente_destinatario_nome", ""),
            "DESTINATION_ADDRESS": req.variables.get("DESTINATION_ADDRESS") or profile.get("ente_destinatario_indirizzo", ""),
            "DESTINATION_PEC": req.variables.get("DESTINATION_PEC") or profile.get("ente_destinatario_pec", ""),
        }
        document_text = DocumentGenerator.generate(req.doc_type, merged_variables)
        
        filename = f"atto_{req.doc_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        DocumentBinder.save_raw_to_case(
            case_id=case_id,
            filename=filename,
            content=document_text,
            category="documenti_generati"
        )
        
        return {"status": "success", "document": document_text, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases/{case_id}/witness")
async def add_witness_sheet(case_id: str, req: WitnessRequest):
    try:
        witness_data = WitnessDataBuilder.build_witness(
            req.name, req.role, req.contact, req.relevance, req.facts
        )
        witness_md = WitnessDataBuilder.generate_markdown(witness_data)
        
        filename = f"teste_{req.name.lower().replace(' ', '_')}.md"
        DocumentBinder.save_raw_to_case(
            case_id=case_id,
            filename=filename,
            content=witness_md,
            category="schede_testimoni"
        )
        
        return {"status": "success", "sheet": witness_md, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- STRATEGY ENGINE ENDPOINT -----------------
@app.post("/api/cases/{case_id}/strategy")
async def generate_case_strategy(case_id: str, req: StrategyRequest):
    raise HTTPException(status_code=410, detail=LOCAL_ONLY_MESSAGE)

# ----------------- DOCUMENT ACQUISITION ENDPOINTS -----------------

@app.post("/api/cases/{case_id}/documents")
async def upload_documents(case_id: str, files: List[UploadFile] = File(...)):
    """
    Carica uno o più documenti nel fascicolo.
    Supporta: PDF, DOCX, DOC, TXT, MD, RTF, immagini, CSV.
    """
    # Verify case exists
    try:
        CaseFileManager.get_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fascicolo non trovato.")

    results = []
    errors  = []
    tmp_dir = "/tmp/lexia_uploads"
    os.makedirs(tmp_dir, exist_ok=True)

    for upload in files:
        fname = os.path.basename(upload.filename or "documento_senza_nome")
        ext   = os.path.splitext(fname)[1].lower()

        if ext not in ACCEPTED_EXTS:
            errors.append({"file": fname, "error": f"Formato non supportato: {ext}"})
            continue

        fd, tmp_path = tempfile.mkstemp(prefix="lexia_doc_", suffix=ext[:12], dir=tmp_dir)
        os.close(fd)
        try:
            with open(tmp_path, "wb") as buf:
                size = 0
                while chunk := upload.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_SIZE:
                        raise ValueError("Il file supera il limite di 50 MB.")
                    buf.write(chunk)

            if ext == ".zip":
                zip_results = DocumentIngestor.save_uploaded_zip(case_id, fname, tmp_path)
                results.extend(zip_results)
            else:
                saved, preview, size = DocumentIngestor.save_uploaded_file(
                    case_id, fname, tmp_path
                )
                results.append({
                    "file": saved,
                    "size": size,
                    "preview": preview[:500] if preview else "",
                })
        except Exception as e:
            errors.append({"file": fname, "error": str(e)})
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return {
        "status": "success" if results else "error",
        "uploaded": results,
        "errors": errors,
        "total": len(results),
    }


@app.get("/api/cases/{case_id}/documents")
async def list_documents(case_id: str):
    """Elenca i documenti acquisiti nel fascicolo."""
    try:
        CaseFileManager.get_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fascicolo non trovato.")
    docs = DocumentIngestor.list_documents(case_id)
    return {"documents": docs, "total": len(docs)}


@app.delete("/api/cases/{case_id}/documents/{filename}")
async def delete_document(case_id: str, filename: str):
    """Elimina un documento dal fascicolo."""
    try:
        CaseFileManager.get_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fascicolo non trovato.")
    ok = DocumentIngestor.delete_document(case_id, filename)
    if not ok:
        raise HTTPException(status_code=404, detail="Documento non trovato.")
    return {"status": "deleted", "filename": filename}


# ----------------- SETTINGS ENDPOINTS -----------------
@app.get("/api/settings")
async def get_settings():
    raise HTTPException(status_code=410, detail=LOCAL_ONLY_MESSAGE)

@app.post("/api/settings")
async def save_settings(settings: Dict[str, Any]):
    raise HTTPException(status_code=410, detail=LOCAL_ONLY_MESSAGE)

# ----------------- FILE DOWNLOAD ROUTE -----------------
@app.get("/api/cases/{case_id}/files/{category}/{filename}")
async def download_case_file(case_id: str, category: str, filename: str):
    try:
        file_path = paths.case_path(case_id, category, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File non trovato.")
    return FileResponse(path=file_path, filename=filename)
