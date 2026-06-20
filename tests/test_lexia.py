import os
import shutil
import sys
import tempfile
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.file_manager import CaseFileManager
from tools.conv_logger import ConversationLogger
from tools.pec_search import PecSearchEngine
from tools.people_search import PeopleSearchEngine
from tools.doc_generator import DocumentGenerator

# Setup test CASES directory to avoid cluttering actual cases
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    test_cases_dir = os.path.join(tempfile.gettempdir(), "lexia_cases_test")
    monkeypatch.setattr("tools.paths.CASES_DIR", test_cases_dir)
    monkeypatch.setattr("tests.test_lexia.TEST_CASES_DIR", test_cases_dir, raising=False)
    if os.path.exists(test_cases_dir):
        shutil.rmtree(test_cases_dir)
    yield
    if os.path.exists(test_cases_dir):
        shutil.rmtree(test_cases_dir)

def test_case_file_management():
    # Test creation
    case = CaseFileManager.create_case("Test Case", "Rossi Mario", "Test description")
    assert case["name"] == "Test Case"
    assert case["client"] == "Rossi Mario"
    
    # Test list
    cases = CaseFileManager.list_cases()
    assert len(cases) == 1
    assert cases[0]["id"] == case["id"]
    
    # Test details retrieval
    retrieved = CaseFileManager.get_case(case["id"])
    assert retrieved["name"] == "Test Case"
    
    # Test adding notes
    filename = CaseFileManager.add_note(case["id"], "Nota Prova", "Contenuto della nota")
    assert filename.startswith("nota_prova_")

def test_case_deletion():
    case = CaseFileManager.create_case("Delete Me", "Test Client", "Desc")
    assert len(CaseFileManager.list_cases()) == 1
    
    # Delete case
    CaseFileManager.delete_case(case["id"])
    assert len(CaseFileManager.list_cases()) == 0
    
    with pytest.raises(FileNotFoundError):
        CaseFileManager.get_case(case["id"])


def test_conversation_logging():
    case = CaseFileManager.create_case("Test Chat", "Bianchi Luigi", "Desc")
    
    ConversationLogger.log_interaction(case["id"], "utente", "Ciao LexIA")
    ConversationLogger.log_interaction(case["id"], "lexia", "Salve, come posso aiutarla?")
    
    conv = ConversationLogger.get_conversation(case["id"])
    assert len(conv) == 2
    assert conv[0]["role"] == "utente"
    assert conv[0]["content"] == "Ciao LexIA"
    assert conv[1]["role"] == "lexia"

def test_pec_search():
    res = PecSearchEngine.search("Tribunale Roma")
    assert res["totale"] >= 1
    assert "prot.tribunale.roma@giustiziacert.it" in [item["pec"] for item in res["risultati"]]
    
    # Test fallback heuristics
    res_fallback = PecSearchEngine.search("Comune di Cuneo")
    assert res_fallback["totale"] >= 1

def test_people_search(monkeypatch):
    import httpx
    from tools import people_search as ps_module

    # Mock a successful VIES response
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "isValid": True,
                "name": "ROSSI COSTRUZIONI SRL",
                "address": "VIA ROMA 1 - 10100 TORINO",
                "requestDate": "2026-06-05"
            }

    class MockClient:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def get(self, url, **kwargs):
            return MockResponse()

    monkeypatch.setattr(ps_module.httpx, "Client", lambda **kwargs: MockClient())

    report = PeopleSearchEngine.search_data("Rossi Costruzioni S.r.l.", vat="01234567890")
    assert report["soggetto"]["denominazione_o_nome"] == "Rossi Costruzioni S.r.l."
    # With VIES returning valid=True the status should not be a fake "ATTIVO / IN REGOLA"
    assert "ATTIVO / IN REGOLA" not in report["stato_soggetto"]
    assert "VIES" in report["stato_soggetto"] or "P.IVA VALIDA" in report["stato_soggetto"]
    # Should contain VIES registry entry
    reg_keys = list(report["registri_consultati"].keys())
    assert any("VIES" in k for k in reg_keys)
    # Verified name must come from the VIES mock, not the user-supplied name
    assert report["soggetto"]["denominazione_verificata"] == "ROSSI COSTRUZIONI SRL"

    md_report = PeopleSearchEngine.generate_markdown_report(report)
    assert "Relazione Investigativa" in md_report
    assert "ROSSI COSTRUZIONI SRL" in md_report
    # Must not contain any simulated/fictional data
    assert "Simulazione" not in md_report
    assert "ALFA COSTRUZIONI" not in md_report

def test_document_generation():
    data = {
        "CLIENT_NAME": "Rossi Mario",
        "TRIBUNALE": "Milano",
        "FACTS": "Il querelato ha commesso truffa..."
    }
    rendered = DocumentGenerator.generate("diffida", data)
    assert "ATTO DI COSTITUZIONE IN MORA" in rendered
    assert "Rossi Mario" in rendered
    assert "Milano" in rendered

def test_case_creation_with_history():
    history = [
        {"role": "utente", "content": "Ho un problema"},
        {"role": "lexia", "content": "Spieghi meglio"}
    ]
    case = CaseFileManager.create_case("Case With History", "Rossi Mario", "Description", history)
    assert case["name"] == "Case With History"
    
    conv = ConversationLogger.get_conversation(case["id"])
    assert len(conv) == 2
    assert conv[0]["content"] == "Ho un problema"
    assert conv[1]["content"] == "Spieghi meglio"

def test_api_endpoints():
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)

    res_reset = client.post("/api/cases/temp_case/reset")
    assert res_reset.status_code == 200

    res_settings = client.get("/api/settings")
    assert res_settings.status_code == 410

    res_extract = client.post("/api/cases/temp_case/extract-details")
    assert res_extract.status_code == 410

    res_consult = client.post("/api/cases/temp_case/consult", json={"prompt": "Test"})
    assert res_consult.status_code == 410

    res_strategy = client.post("/api/cases/temp_case/strategy", json={"case_summary": "Test"})
    assert res_strategy.status_code == 410

def test_audio_transcription(monkeypatch):
    from tools.transcriber import AudioTranscriber
    import subprocess
    import speech_recognition as sr

    # Mock os.path.exists to return True only for our test audio files
    original_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda path: True if "test.wav" in path or "test.mp3" in path else original_exists(path))

    # Mock recognizer record and recognize_google
    monkeypatch.setattr(sr.Recognizer, "record", lambda self, source: "mocked_audio_data")
    monkeypatch.setattr(sr.Recognizer, "recognize_google", lambda self, audio_data, language: "testo trascritto con successo")

    # Mock sr.AudioFile context manager
    class MockAudioFile:
        def __init__(self, filepath):
            self.filepath = filepath
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    monkeypatch.setattr(sr, "AudioFile", MockAudioFile)

    # 1. Test directly supported WAV format
    res_wav = AudioTranscriber.transcribe("test.wav")
    assert res_wav == "testo trascritto con successo"

    # 2. Test format needing conversion (MP3)
    ffmpeg_called = []
    def mock_run(cmd, *args, **kwargs):
        ffmpeg_called.append(cmd)
        # Mock successful subprocess run (returncode = 0)
        class MockCompletedProcess:
            returncode = 0
            stdout = ""
            stderr = ""
        return MockCompletedProcess()

    monkeypatch.setattr(subprocess, "run", mock_run)
    # Mock os.remove to prevent errors when trying to remove the non-existent temp file
    monkeypatch.setattr(os, "remove", lambda path: None)

    res_mp3 = AudioTranscriber.transcribe("test.mp3")
    assert len(ffmpeg_called) == 1
    assert "ffmpeg" in ffmpeg_called[0]
    assert "-i" in ffmpeg_called[0]
    assert "test.mp3" in ffmpeg_called[0]
    assert res_mp3 == "testo trascritto con successo"
