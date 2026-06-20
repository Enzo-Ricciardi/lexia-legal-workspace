# LexIA Roadmap

## Objective

Stabilize LexIA as a privacy-first, browser-first legal workspace and make external contribution easier and safer.

## Priority areas

1. Remove duplicated browser/server flows where possible
2. Improve contributor onboarding and local development
3. Strengthen test coverage for core workflows
4. Clarify the long-term architecture for browser runtime vs backend services
5. Improve deployment and configuration hygiene

## Workstreams

### Architecture

- document the browser-first runtime more explicitly
- identify which backend endpoints are still required
- reduce ambiguity between public runtime and development backend

### Testing

- add workflow coverage for:
  - document upload
  - consultation flow
  - people search
  - transcription flow
  - temporary-case conversion
- add regression checks for case storage categories

### Security and hygiene

- keep secrets out of version control
- improve config examples
- document safe contributor practices for legal and personal data

### UX and product

- refine fail-fast behavior when the local runtime is unavailable
- improve clarity around local-only storage and provider usage
- streamline drafting and document review flows

## Notes for contributors

Keep PRs focused, avoid introducing secrets or local case data, and explain architectural tradeoffs clearly.
