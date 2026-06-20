import os
import json
from datetime import datetime
from typing import List, Dict, Any
from tools import paths

class ConversationLogger:
    @classmethod
    def log_interaction(cls, case_id: str, role: str, content: str) -> None:
        conv_path = paths.case_path(case_id, "conversazione.json")
        if not os.path.exists(conv_path):
            # Create if missing
            conversation = []
        else:
            try:
                with open(conv_path, "r", encoding="utf-8") as f:
                    conversation = json.load(f)
            except Exception:
                conversation = []
                
        conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        with open(conv_path, "w", encoding="utf-8") as f:
            json.dump(conversation, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_conversation(cls, case_id: str) -> List[Dict[str, Any]]:
        conv_path = paths.case_path(case_id, "conversazione.json")
        if not os.path.exists(conv_path):
            return []
        try:
            with open(conv_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
