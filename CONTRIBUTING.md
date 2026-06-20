# Contributing to LexIA

## Before you start

- Read `README.md` and `PROJECT_STATE.md`.
- Treat LexIA as a browser-first privacy-first application unless a task explicitly targets backend development.
- Do not introduce real credentials, case data, or personal data into version control.

## Development rules

- Keep changes scoped and reviewable.
- Prefer explicit behavior over hidden fallbacks.
- Avoid duplicating logic between FastAPI and `browser-api.js` unless there is a clear migration reason.
- When adding a new case/document category, update every canonical source that depends on it.

## Pull requests

Each PR should include:
- a short problem statement;
- the chosen approach;
- any architectural tradeoff;
- validation performed.

## Validation

Minimum expected checks:
- Python syntax/tests when Python files change
- manual browser verification when `templates/index.html` or `static/browser-api.js` changes
- no secrets or local state files added to the diff

## Commit style

Use direct, technical commit messages, for example:

- `Fix LexIA case storage consistency`
- `Clarify LexIA browser-first runtime`

