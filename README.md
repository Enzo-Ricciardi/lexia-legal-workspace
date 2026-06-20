# lexia-legal-workspace
Privacy-first legal workspace with local case management, document handling, AI-assisted consultation, and browser-first architecture.
# LexIA

LexIA is a privacy-first legal workspace for local case management, document handling, AI-assisted legal consultation, and guided legal drafting.

The current public architecture is browser-first:
- case files, conversations, documents, and provider settings stay on the user's device;
- the browser runtime intercepts `/api/...` flows locally;
- the Python/FastAPI backend is still available for development and selected server-side tools, but it is not the primary public runtime.

## Why LexIA

LexIA is designed for legal workflows where privacy, local control, and structured reasoning matter.

Core goals:
- keep sensitive case data on the user's device whenever possible;
- support practical legal work, not generic chat;
- provide structured workflows for cases, documents, consultation, and drafting;
- remain auditable and extensible for contributors.

## Features

- Local case workspaces with persistent storage
- Document upload, preview, and editing
- Selective document inclusion in legal consultation
- AI-assisted consultation with user-configured providers
- Witness sheets, PEC lookup, people search, and transcription workflows
- Guided drafting workspace for legal acts
- Privacy-first browser runtime

## Architecture

LexIA currently has two layers:

### 1. Browser-first runtime
- `static/browser-api.js`
- IndexedDB/localStorage persistence
- local document processing
- local API interception for the public workflow

### 2. Python backend
- `app.py`
- FastAPI services
- tool modules under `tools/`
- prompt and agent logic under `core/`

The browser-first runtime is currently the reference public flow.

## Repository structure

- `templates/index.html` — main UI
- `static/browser-api.js` — browser runtime and local API layer
- `app.py` — FastAPI backend
- `core/` — prompts and agent logic
- `tools/` — case, document, search, generation, transcription helpers
- `tests/` — Python-side tests
- `deploy_lexia.py` — FTP deployment script

## Local development

### Requirements
- Python 3.13+
- optional virtual environment

### Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
