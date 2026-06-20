# Security Policy

## Scope

LexIA handles sensitive legal workflows and must be treated as a privacy-sensitive project.

## Please do not publish

- real API keys
- FTP credentials
- private authentication files
- local case data
- conversation exports containing personal data

## Reporting

If you discover a security issue, do not open a public issue with exploit details or live credentials.

Report it privately to the maintainer with:
- affected file or flow
- impact
- reproduction steps
- suggested mitigation, if available

## Hard rules for contributors

- Never commit secrets to the repository.
- Never commit generated local storage exports or live case files.
- Prefer environment variables or example configuration files over real credentials.

