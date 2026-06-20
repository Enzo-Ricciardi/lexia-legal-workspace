# LexIA

LexIA is a privacy-first legal workspace focused on local case management, document handling, guided legal drafting, and AI-assisted consultation.

The current public runtime is browser-first:
- cases, conversations, documents, and provider settings stay on the user's device;
- `static/browser-api.js` intercepts `/api/...` calls and serves the application locally in the browser;
- the Python/FastAPI backend remains available for development and for selected server-side tools, but it is not the primary public runtime.

## Current scope

- Case workspaces with local persistence
- Document upload, preview, editing, and consultation inclusion flags
- Legal consultation with user-selected LLM providers
- Investigative tools such as PEC lookup, people search, witness sheets, and transcription workflows
- Guided drafting workspace for legal acts

## Repository status

This repository is the standalone public-ready extraction of LexIA from the broader website monorepo.

LexIA is under active architectural cleanup.

The current direction is:
- browser-first public app
- explicit privacy-first behavior
- progressive reduction of duplicated server/browser flows

## Roadmap

### Near term

- stabilize the browser-first runtime
- reduce duplicated browser/server logic
- improve test coverage for core workflows
- harden repository hygiene and contributor safety

### Active priorities

- document upload and editor reliability
- consultation workflow consistency
- case/category storage coherence
- safer configuration and deployment practices
- clearer contributor onboarding

## Project structure

- `templates/index.html`: main UI
- `static/browser-api.js`: local browser runtime and API interception
- `app.py`: FastAPI backend
- `core/`: prompts and agent logic
- `tools/`: case, document, transcription, search, and generation helpers
- `tests/`: pytest coverage for the Python side

## Local development

Requirements:
- Python 3.13+
- optional local virtualenv at `.venv`

Install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run locally:

```bash
./run.sh
```

If the local virtualenv is missing, `run.sh` falls back to `python3 -m uvicorn`.

Open the public UI through:

```text
index.php
```

or serve the repository root locally and load the PHP/front controller path used by your environment.

## Configuration

- Browser runtime provider settings are stored locally on the user's device.
- Server-side settings are read from `config/settings.json`, which must not contain real secrets in version control.
- Deploy credentials must be provided through environment variables:
  - `LEXIA_FTP_HOST`
  - `LEXIA_FTP_USER`
  - `LEXIA_FTP_PASSWORD`

## Contributing

See `CONTRIBUTING.md`.

## Security

See `SECURITY.md`.

## GitHub workflow

- use Issues for bugs and feature requests
- keep pull requests focused and reviewable
- avoid committing secrets, personal data, or local case files
