import os
from pathlib import Path
from core.prompts import SYSTEM_PROMPT
from config.manager import ConfigManager
from tools.conv_logger import ConversationLogger
from tools import paths
from tools.file_manager import CASE_SUBDIRS

class LexiaAgent:
    @classmethod
    def get_case_text_context(cls, case_id: str, query: str = "") -> str:
        """
        Scans all case subdirectories, lists all files, and embeds the most relevant file contents
        based on keyword relevance to the user's query.
        """
        case_path = paths.case_path(case_id)
        if not os.path.exists(case_path):
            return ""
            
        context_parts = []
        subdirs = [subdir for subdir in CASE_SUBDIRS if subdir != "documenti_generati"]
        all_files = []
        
        for subdir in subdirs:
            dir_path = os.path.join(case_path, subdir)
            if not os.path.exists(dir_path):
                continue
            for fname in os.listdir(dir_path):
                fpath = os.path.join(dir_path, fname)
                if not os.path.isfile(fpath):
                    continue
                # Skip raw files if sidecar txt exists
                if fname.endswith((".pdf", ".docx", ".doc", ".odt")):
                    if os.path.exists(fpath + ".estratto.txt"):
                        continue
                if fname.endswith(".estratto.txt") or fname.endswith((".txt", ".md", ".csv")):
                    all_files.append({
                        "subdir": subdir,
                        "name": fname,
                        "path": fpath,
                        "modified": os.path.getmtime(fpath)
                    })

        if not all_files:
            return ""

        # Build list of files for the agent's general awareness
        file_list_str = "Elenco di tutti i documenti presenti nel fascicolo:\n"
        for f in all_files:
            display_name = f["name"].replace(".estratto.txt", "")
            file_list_str += f"- [{f['subdir']}] {display_name}\n"

        # Rank files by keyword relevance
        keywords = [w.lower() for w in query.split() if len(w) > 2]
        stop_words = {"con", "del", "della", "dello", "nei", "nella", "nello", "per", "che", "non", "sul", "sulla", "tra", "fra"}
        keywords = [k for k in keywords if k not in stop_words]

        ranked_files = []
        for f in all_files:
            score = 0
            try:
                content = Path(f["path"]).read_text(encoding="utf-8", errors="replace").lower()
            except Exception:
                content = ""

            name_lower = f["name"].lower()
            for kw in keywords:
                if kw in name_lower:
                    score += 15
                score += content.count(kw) * 2
            
            ranked_files.append((score, f))

        # Sort by score (descending), then by modification time (newest first)
        ranked_files.sort(key=lambda x: (x[0], x[1]["modified"]), reverse=True)
        top_files = ranked_files[:3]
        
        content_str = "CONTENUTO DEI DOCUMENTI PIÙ RILEVANTI NEL FASCICOLO:\n"
        for score, f in top_files:
            try:
                content = Path(f["path"]).read_text(encoding="utf-8", errors="replace")
                display_name = f["name"].replace(".estratto.txt", "")
                content_str += f"\n--- DOCUMENTO: {display_name} ({f['subdir']}) ---\n"
                content_str += content[:1000]
                if len(content) > 1000:
                    content_str += "\n[... Testo troncato per limiti di spazio ...]"
                content_str += "\n"
            except Exception:
                pass

        return f"\n{file_list_str}\n{content_str}\n"

    @classmethod
    async def consult(cls, case_id: str, prompt: str) -> str:
        """
        Consult LexIA core agent regarding a case. Logs the interaction automatically.
        """
        # Load previous history if available to give context
        history = ConversationLogger.get_conversation(case_id)
        
        # Load case files text context based on the current user query
        files_context = cls.get_case_text_context(case_id, prompt)
        
        # Build chat context
        context_str = ""
        if files_context:
            context_str += files_context + "\n"
            
        if history:
            context_str += "Cronologia delle conversazioni precedenti per questo caso:\n"
            # Limit history to last 3 messages and truncate each to 800 chars to avoid blowing local context limit
            for msg in history[-3:]:
                msg_content = msg['content']
                if len(msg_content) > 800:
                    msg_content = msg_content[:800] + "\n[... Testo risposta precedente troncato per limiti di spazio ...]"
                context_str += f"- {msg['role'].upper()}: {msg_content}\n"
            context_str += "\nRichiesta corrente dell'utente:\n"
            
        user_prompt_with_history = f"{context_str}{prompt}"
        
        # Log user request
        ConversationLogger.log_interaction(case_id, "utente", prompt)
        
        # Call LLM
        response = await ConfigManager.call_active_llm(SYSTEM_PROMPT, user_prompt_with_history)
        
        # Log agent response
        ConversationLogger.log_interaction(case_id, "lexia", response)
        
        return response

    @classmethod
    async def generate_strategy_only(cls, case_summary: str) -> str:
        """
        Directly asks the model to formulate a procedural strategy and risk analysis.
        """
        strategy_system = SYSTEM_PROMPT + "\nFornisci un'analisi focalizzata esclusivamente sulla Strategia Forense e sulla Valutazione dei Rischi del caso descritto."
        response = await ConfigManager.call_active_llm(strategy_system, case_summary)
        return response
