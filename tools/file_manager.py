import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from tools import paths

CASE_SUBDIRS = [
    "documenti_cliente",
    "documenti_generati",
    "trascrizioni_audio",
    "ricerche_pec",
    "ricerche_investigative",
    "schede_testimoni",
    "note_utente",
]

class CaseFileManager:
    @staticmethod
    def _ensure_cases_dir() -> str:
        if not os.path.exists(paths.CASES_DIR):
            os.makedirs(paths.CASES_DIR, exist_ok=True)
        return paths.CASES_DIR

    @classmethod
    def create_case(cls, name: str, client: str, description: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        root = cls._ensure_cases_dir()
        case_id = str(uuid.uuid4())[:8] + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        case_path = os.path.join(root, case_id)

        for subdir in CASE_SUBDIRS:
            os.makedirs(os.path.join(case_path, subdir), exist_ok=True)
            
        metadata = {
            "id": case_id,
            "name": name,
            "client": client,
            "description": description,
            "profile": {},
            "created_at": datetime.now().isoformat(),
            "status": "attivo"
        }
        
        with open(os.path.join(case_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        # Initialize conversation log file with either empty list or pre-existing history
        conv_data = history if history is not None else []
        with open(os.path.join(case_path, "conversazione.json"), "w", encoding="utf-8") as f:
            json.dump(conv_data, f, indent=2, ensure_ascii=False)
            
        return metadata

    @classmethod
    def list_cases(cls) -> List[Dict[str, Any]]:
        root = cls._ensure_cases_dir()
        cases = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, "metadata.json")):
                try:
                    with open(os.path.join(path, "metadata.json"), "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        if not meta.get("temporary", False):
                            cases.append(meta)
                except Exception:
                    pass
        # Sort by creation date descending
        cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return cases

    @classmethod
    def get_case(cls, case_id: str) -> Dict[str, Any]:
        root = cls._ensure_cases_dir()
        path = paths.case_path(case_id)
        if not os.path.exists(path) or not os.path.isdir(path):
            raise FileNotFoundError(f"Fascicolo {case_id} non trovato.")
            
        metadata_path = os.path.join(path, "metadata.json")
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        return metadata

    @classmethod
    def get_case_structure(cls, case_id: str) -> Dict[str, Any]:
        root = cls._ensure_cases_dir()
        path = paths.case_path(case_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fascicolo {case_id} non trovato.")
            
        structure = {}
        for subdir in CASE_SUBDIRS:
            subdir_path = os.path.join(path, subdir)
            files = []
            if os.path.exists(subdir_path):
                for fname in os.listdir(subdir_path):
                    fpath = os.path.join(subdir_path, fname)
                    if os.path.isfile(fpath):
                        stat = os.stat(fpath)
                        files.append({
                            "name": fname,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            structure[subdir] = files
            
        return structure

    @classmethod
    def add_note(cls, case_id: str, title: str, content: str) -> str:
        root = cls._ensure_cases_dir()
        note_dir = paths.case_path(case_id, "note_utente")
        if not os.path.exists(note_dir):
            raise FileNotFoundError(f"Fascicolo {case_id} non esistente.")
            
        safe_title = "".join(
            char for char in title.lower().replace(" ", "_")
            if char.isalnum() or char in "._-"
        ).strip("._") or "nota"
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(note_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filename

    @classmethod
    def delete_case(cls, case_id: str) -> None:
        root = cls._ensure_cases_dir()
        path = paths.case_path(case_id)
        if not os.path.exists(path) or not os.path.isdir(path):
            raise FileNotFoundError(f"Fascicolo {case_id} non trovato.")
        import shutil
        shutil.rmtree(path)

    @classmethod
    def create_temporary_case(cls) -> Dict[str, Any]:
        root = cls._ensure_cases_dir()
        case_id = "temp_case"
        case_path = os.path.join(root, case_id)
        
        # Clean folder if it exists
        if os.path.exists(case_path):
            import shutil
            try:
                shutil.rmtree(case_path)
            except Exception:
                pass
                
        for subdir in CASE_SUBDIRS:
            os.makedirs(os.path.join(case_path, subdir), exist_ok=True)
            
        metadata = {
            "id": case_id,
            "name": "Consulenza Preliminare",
            "client": "Temporaneo",
            "description": "Fascicolo temporaneo per consultazione libera",
            "profile": {},
            "created_at": datetime.now().isoformat(),
            "status": "temporaneo",
            "temporary": True
        }
        
        with open(os.path.join(case_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        with open(os.path.join(case_path, "conversazione.json"), "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
            
        return metadata

    @classmethod
    def convert_temporary_case(cls, name: str, client: str, description: str) -> Dict[str, Any]:
        root = cls._ensure_cases_dir()
        temp_path = os.path.join(root, "temp_case")
        if not os.path.exists(temp_path):
            cls.create_temporary_case()
            
        new_id = str(uuid.uuid4())[:8] + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        new_path = os.path.join(root, new_id)
        
        # Rename the folder on disk, but fall back to a clean creation if needed.
        try:
            os.rename(temp_path, new_path)
        except Exception:
            import shutil
            if os.path.exists(new_path):
                shutil.rmtree(new_path, ignore_errors=True)
            try:
                shutil.move(temp_path, new_path)
            except Exception:
                os.makedirs(new_path, exist_ok=True)
                for subdir in CASE_SUBDIRS:
                    os.makedirs(os.path.join(new_path, subdir), exist_ok=True)
                with open(os.path.join(new_path, "conversazione.json"), "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)

        # Update metadata.json
        metadata_path = os.path.join(new_path, "metadata.json")
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}
            
        metadata.update({
            "id": new_id,
            "name": name,
            "client": client,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "attivo"
        })
        metadata.pop("temporary", None)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        # Recreate the temporary case folder immediately
        cls.create_temporary_case()
        
        return metadata
