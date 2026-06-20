"""
tools/doc_ingestor.py
Acquisizione e indicizzazione di documenti del fascicolo.
Supporta: PDF, DOCX, TXT, MD, JPG, PNG (OCR-free), RTF.
"""
import os
import shutil
import mimetypes
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Tuple
from tools import paths
CATEGORY   = "documenti_cliente"
MAX_ZIP_MEMBER_SIZE = 25 * 1024 * 1024
MAX_ZIP_TOTAL_SIZE = 150 * 1024 * 1024
MAX_ZIP_COMPRESSION_RATIO = 150

# Accepted MIME prefixes / suffixes
ACCEPTED_EXTS = {
    ".pdf", ".docx", ".doc",
    ".txt", ".md", ".rtf",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".odt", ".csv", ".zip",
}


class DocumentIngestor:
    """Acquisce documenti dal client e li salva nel fascicolo."""

    # ── public ──────────────────────────────────────────────────────
    @classmethod
    def save_uploaded_file(
        cls,
        case_id: str,
        original_filename: str,
        tmp_path: str,
    ) -> Tuple[str, str, int]:
        """
        Copia il file caricato nella cartella documenti_cliente del fascicolo.
        Ritorna (filename_saved, extracted_text_preview, file_size).
        """
        dest_dir = cls._ensure_dir(case_id)

        # Sanitize & de-duplicate filename
        safe_name = cls._safe_filename(original_filename, dest_dir)
        dest_path = os.path.join(dest_dir, safe_name)

        shutil.copy2(tmp_path, dest_path)

        size = os.path.getsize(dest_path)
        preview = cls._extract_text_preview(dest_path)

        # Also save a txt sidecar with extracted text (for RAG / AI context)
        if preview and not dest_path.endswith(".txt"):
            sidecar = dest_path + ".estratto.txt"
            Path(sidecar).write_text(
                f"=== ESTRATTO DA: {safe_name} ===\n\n{preview}\n",
                encoding="utf-8",
            )

        return safe_name, preview, size

    @classmethod
    def save_uploaded_zip(
        cls,
        case_id: str,
        original_filename: str,
        tmp_path: str,
        max_members: int = 100,
    ) -> list:
        """Estrae un archivio ZIP e salva i documenti supportati nel fascicolo."""
        dest_dir = cls._ensure_dir(case_id)
        saved_items = []
        seen = 0
        total_size = 0

        with zipfile.ZipFile(tmp_path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                seen += 1
                if seen > max_members:
                    raise ValueError("Archivio ZIP troppo grande o contenente troppi file.")
                if info.file_size > MAX_ZIP_MEMBER_SIZE:
                    raise ValueError("Un file nello ZIP supera il limite di 25 MB.")
                total_size += info.file_size
                if total_size > MAX_ZIP_TOTAL_SIZE:
                    raise ValueError("Il contenuto dello ZIP supera il limite di 150 MB.")
                if info.file_size / max(info.compress_size, 1) > MAX_ZIP_COMPRESSION_RATIO:
                    raise ValueError("Archivio ZIP con rapporto di compressione anomalo.")

                inner_name = Path(info.filename).name
                if not inner_name:
                    continue

                ext = Path(inner_name).suffix.lower()
                if ext not in ACCEPTED_EXTS or ext == ".zip":
                    continue

                safe_name = cls._safe_filename(inner_name, dest_dir)
                dest_path = os.path.join(dest_dir, safe_name)

                with zf.open(info) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                size = os.path.getsize(dest_path)
                preview = cls._extract_text_preview(dest_path)
                if preview and not dest_path.endswith(".txt"):
                    sidecar = dest_path + ".estratto.txt"
                    Path(sidecar).write_text(
                        f"=== ESTRATTO DA: {safe_name} (da {original_filename}) ===\n\n{preview}\n",
                        encoding="utf-8",
                    )

                saved_items.append({
                    "file": safe_name,
                    "size": size,
                    "preview": preview[:500] if preview else "",
                })

        return saved_items

    @classmethod
    def delete_document(cls, case_id: str, filename: str) -> bool:
        """Rimuove un documento dal fascicolo (file + eventuale sidecar)."""
        dest_dir = cls._ensure_dir(case_id)
        fp = os.path.join(dest_dir, paths.safe_segment(filename, "nome documento"))
        if not os.path.exists(fp):
            return False
        os.remove(fp)
        sidecar = fp + ".estratto.txt"
        if os.path.exists(sidecar):
            os.remove(sidecar)
        return True

    @classmethod
    def list_documents(cls, case_id: str) -> list:
        """Elenca i documenti presenti nella cartella documenti_cliente."""
        d = cls._ensure_dir(case_id)
        files = []
        for fname in sorted(os.listdir(d)):
            if fname.endswith(".estratto.txt"):
                continue  # hide sidecars
            fp = os.path.join(d, fname)
            if os.path.isfile(fp):
                stat = os.stat(fp)
                files.append({
                    "name": fname,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "ext": Path(fname).suffix.lower(),
                })
        return files

    # ── private ─────────────────────────────────────────────────────
    @classmethod
    def _ensure_dir(cls, case_id: str) -> str:
        d = paths.case_path(case_id, CATEGORY)
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def _safe_filename(original: str, dest_dir: str) -> str:
        """Sanitizza e rende il nome file unico nella cartella."""
        name = os.path.basename(original).replace(" ", "_")
        # Remove dangerous characters
        name = "".join(c for c in name if c.isalnum() or c in "._-")
        if not name:
            name = f"documento_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # De-duplicate
        stem = Path(name).stem
        suffix = Path(name).suffix
        candidate = name
        counter = 1
        while os.path.exists(os.path.join(dest_dir, candidate)):
            candidate = f"{stem}_{counter}{suffix}"
            counter += 1
        return candidate

    @staticmethod
    def _extract_text_preview(path: str, max_chars: int = 4000) -> str:
        """Estrae un'anteprima testuale dal documento."""
        ext = Path(path).suffix.lower()
        try:
            if ext == ".pdf":
                return DocumentIngestor._read_pdf(path, max_chars)
            elif ext in (".docx", ".doc"):
                return DocumentIngestor._read_docx(path, max_chars)
            elif ext in (".txt", ".md", ".rtf", ".csv"):
                return Path(path).read_text(encoding="utf-8", errors="replace")[:max_chars]
            else:
                return ""  # Binary (images, etc.) – no text extraction
        except Exception as e:
            return f"[Errore estrazione testo: {e}]"

    @staticmethod
    def _read_pdf(path: str, max_chars: int) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
                if sum(len(p) for p in parts) >= max_chars:
                    break
            return "\n".join(parts)[:max_chars]
        except ImportError:
            return "[pypdf non installato — installare con: pip install pypdf]"

    @staticmethod
    def _read_docx(path: str, max_chars: int) -> str:
        try:
            from docx import Document
            doc = Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
            return text[:max_chars]
        except ImportError:
            return "[python-docx non installato — installare con: pip install python-docx]"
