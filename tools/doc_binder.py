import os
import shutil
from typing import Dict, Any
from tools import paths

class DocumentBinder:
    @classmethod
    def bind_file_to_case(cls, case_id: str, file_path: str, category: str) -> str:
        """
        Copies a file from any path (e.g., scratch folder) to the active case category directory.
        Categories: 'documenti_generati', 'trascrizioni_audio', 'ricerche_pec', 'schede_testimoni', 'note_utente'
        """
        dest_dir = paths.case_path(case_id, category)
        if not os.path.exists(dest_dir):
            raise FileNotFoundError(f"La cartella {category} del fascicolo {case_id} non esiste.")
            
        filename = os.path.basename(file_path)
        dest_path = os.path.join(dest_dir, filename)
        
        shutil.copy2(file_path, dest_path)
        return dest_path

    @classmethod
    def save_raw_to_case(cls, case_id: str, filename: str, content: str, category: str) -> str:
        """
        Saves text content directly to the case's category subfolder.
        """
        dest_dir = paths.case_path(case_id, category)
        if not os.path.exists(dest_dir):
            raise FileNotFoundError(f"La cartella {category} del fascicolo {case_id} non esiste.")
            
        dest_path = os.path.join(dest_dir, paths.safe_segment(filename, "nome file"))
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return dest_path
