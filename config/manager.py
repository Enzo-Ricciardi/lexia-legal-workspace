import os
import json
import httpx
from typing import Dict, Any, Tuple

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "active_provider": "gemini",
    "providers": {
        "gemini": {"api_key": "", "model": "gemini-3.5-flash", "url": "https://generativelanguage.googleapis.com/v1beta/models"},
        "openai": {"api_key": "", "model": "gpt-4o", "url": "https://api.openai.com/v1"},
        "ollama": {"api_key": "", "model": "llama3", "url": "http://localhost:11434"},
        "lm_studio": {"api_key": "", "model": "meta-llama-3-8b-instruct", "url": "http://localhost:1234/v1"},
        "copilot": {"api_key": "", "model": "copilot-codex", "url": "https://api.githubcopilot.com"},
        "openrouter": {"api_key": "", "model": "qwen/qwen3-next-80b-a3b-instruct:free", "url": "https://openrouter.ai/api/v1"}
    }
}

class ConfigManager:
    @staticmethod
    def load_settings() -> Dict[str, Any]:
        if not os.path.exists(SETTINGS_PATH):
            return json.loads(json.dumps(DEFAULT_SETTINGS))
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Merge missing defaults so the UI always has a complete provider set.
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        for key, value in data.items():
            if key not in {"active_provider", "providers"}:
                merged[key] = value
        merged["active_provider"] = data.get("active_provider", merged["active_provider"])
        providers = data.get("providers", {})
        for key, defaults in merged["providers"].items():
            incoming = providers.get(key, {})
            defaults.update({k: incoming.get(k, v) for k, v in defaults.items()})
        return merged

    @staticmethod
    def save_settings(settings: Dict[str, Any]) -> None:
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        for key, value in settings.items():
            if key not in {"active_provider", "providers"}:
                merged[key] = value
        merged["active_provider"] = settings.get("active_provider", merged["active_provider"])
        incoming_providers = settings.get("providers", {})
        for key, defaults in merged["providers"].items():
            incoming = incoming_providers.get(key, {})
            defaults.update({k: incoming.get(k, v) for k, v in defaults.items()})
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

    @classmethod
    async def get_lm_studio_active_model(cls, base_url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{base_url}/models")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    # Prefer first non-embedding model
                    for m in models:
                        m_id = m.get("id", "")
                        if "embed" not in m_id.lower():
                            return m_id
                    if models:
                        return models[0].get("id", "")
        except Exception:
            pass
        return None

    @classmethod
    async def call_active_llm(cls, system_prompt: str, user_prompt: str) -> str:
        settings = cls.load_settings()
        active = settings.get("active_provider", "gemini")
        provider_settings = settings.get("providers", {}).get(active, {})
        
        api_key = provider_settings.get("api_key", "")
        model = provider_settings.get("model", "")
        base_url = provider_settings.get("url", "")
        
        if active == "lm_studio":
            detected_model = await cls.get_lm_studio_active_model(base_url)
            if detected_model and detected_model != model:
                model = detected_model
                settings["providers"]["lm_studio"]["model"] = detected_model
                cls.save_settings(settings)
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                if active == "gemini":
                    # Direct Gemini API Call
                    url = f"{base_url}/{model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": f"System Instruction:\n{system_prompt}\n\nUser Request:\n{user_prompt}"}]
                            }
                        ]
                    }
                    headers = {"Content-Type": "application/json"}
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code != 200:
                        try:
                            err_msg = response.json()["error"]["message"]
                        except Exception:
                            err_msg = response.text
                        raise ValueError(f"Gemini API Error ({response.status_code}): {err_msg}")
                    res_data = response.json()
                    try:
                        return res_data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        raise ValueError(f"Errore nell'interpretazione della risposta Gemini: {json.dumps(res_data)}")

                elif active in ["openai", "lm_studio", "copilot", "openrouter"]:
                    # Standard OpenAI Chat Completions endpoint
                    url = f"{base_url}/chat/completions"
                    headers = {"Content-Type": "application/json"}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"
                    if active == "openrouter":
                        headers["HTTP-Referer"] = "https://github.com/enzo/LexIA"
                        headers["X-Title"] = "LexIA Legal Agent"
                    
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2
                    }
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code != 200:
                        try:
                            err_msg = response.json()["error"]["message"]
                        except Exception:
                            err_msg = response.text
                        raise ValueError(f"{active.upper()} API Error ({response.status_code}): {err_msg}")
                    res_data = response.json()
                    try:
                        return res_data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        raise ValueError(f"Errore nell'interpretazione della risposta da {active}: {json.dumps(res_data)}")

                elif active == "ollama":
                    # Ollama Chat API Call
                    url = f"{base_url}/api/chat"
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "options": {"temperature": 0.2}
                    }
                    headers = {"Content-Type": "application/json"}
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code != 200:
                        try:
                            err_msg = response.json()["error"]["message"]
                        except Exception:
                            err_msg = response.text
                        raise ValueError(f"Ollama API Error ({response.status_code}): {err_msg}")
                    res_data = response.json()
                    try:
                        return res_data["message"]["content"]
                    except KeyError:
                        raise ValueError(f"Errore nell'interpretazione della risposta Ollama: {json.dumps(res_data)}")

                else:
                    raise ValueError(f"Provider sconosciuto: {active}")
        except httpx.RequestError as e:
            raise ValueError(f"Errore di connessione di rete verso {active}: {str(e)}")
