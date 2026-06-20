#!/bin/bash
# Script per avviare LexIA e aprire la dashboard nel browser
CD_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CD_PATH" || exit 1

# Controlla se la porta 8000 è già occupata
if lsof -i :8000 >/dev/null 2>&1; then
    echo "Il server LexIA è già avviato o la porta 8000 è occupata."
    xdg-open http://localhost:8000
    exit 0
fi

# Avvia uvicorn preferendo il virtualenv locale, con fallback a python3 -m uvicorn
if [ -x "$CD_PATH/.venv/bin/uvicorn" ]; then
    UVICORN_CMD=("$CD_PATH/.venv/bin/uvicorn")
else
    UVICORN_CMD=(python3 -m uvicorn)
fi

"${UVICORN_CMD[@]}" app:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# Attendi l'avvio del server
sleep 2

# Apri il browser
xdg-open http://localhost:8000

# Mantieni lo script in attesa per consentire la chiusura corretta
wait $SERVER_PID
