import argparse
import ftplib
import os
import sys

HOST = os.environ.get("LEXIA_FTP_HOST", "")
USER = os.environ.get("LEXIA_FTP_USER", "")
PASS = os.environ.get("LEXIA_FTP_PASSWORD", "")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REMOTE_BASE = "/LexIA"

FILES_TO_UPLOAD = [
    ".htaccess",
    "app.py",
    "index.html",
    "index.php",
    "manuale-uso.html",
    "PROJECT_STATE.md",
    "lexia-logo-3d.png",
    "requirements.txt",
    "run.sh",
    "config/manager.py",
    "core/agent.py",
    "core/prompts.py",
    "static/browser-api.js",
    "static/vendor/pdf.min.js",
    "static/vendor/pdf.worker.min.js",
    "static/vendor/mammoth.browser.min.js",
    "templates/index.html",
    "tools/conv_logger.py",
    "tools/doc_binder.py",
    "tools/doc_generator.py",
    "tools/doc_ingestor.py",
    "tools/file_manager.py",
    "tools/paths.py",
    "tools/pec_search.py",
    "tools/people_search.py",
    "tools/strategy_engine.py",
    "tools/transcriber.py",
    "tools/witness_builder.py",
    "api/check-source.php",
    "api/ipa-pec.php",
    "lexia-law-preview.png",
    "lexia-law-preview-v2.png",
    "lexia-law-preview-v2.jpg",
]

REMOTE_FILES_TO_DELETE = [
    "/LexIA/.htpasswd",
    "/LexIA/templates/.htaccess",
    "/LexIA/config/private-auth.php",
    "/LexIA/private/.htaccess",
    "/LexIA/private/index.php",
    "/LexIA/private/browser-api.php",
    "/LexIA/private/vendor.php",
    "/LexIA/private/index.html",
    "/LexIA/private-test.html",
]


def ensure_dir(ftp, remote_dir):
    parts = remote_dir.split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current += "/" + part
        try:
            ftp.mkd(current)
        except Exception:
            pass


def upload_file(ftp, local_path, remote_path):
    print(f"Uploading: {remote_path}")
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Deploy LexIA via FTP. By default uploads the full curated file list."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Relative LexIA paths to upload. If omitted, uploads the default curated list.",
    )
    parser.add_argument(
        "--skip-delete",
        action="store_true",
        help="Do not delete obsolete remote files before upload.",
    )
    return parser.parse_args()


def normalize_rel_path(path):
    normalized = os.path.normpath(str(path or "")).replace("\\", "/").lstrip("/")
    if (
        not normalized
        or normalized == "."
        or normalized.startswith("../")
        or normalized == ".."
        or "/../" in normalized
    ):
        raise ValueError(f"Percorso non valido: {path}")
    return normalized


def select_files(requested_paths):
    if not requested_paths:
        return FILES_TO_UPLOAD

    allowed = {normalize_rel_path(path) for path in FILES_TO_UPLOAD}
    selected = []
    seen = set()
    for path in requested_paths:
        normalized = normalize_rel_path(path)
        if normalized not in allowed:
            raise ValueError(
                f"Il file '{normalized}' non e' incluso nella whitelist di deploy."
            )
        if normalized not in seen:
            selected.append(normalized)
            seen.add(normalized)
    return selected


def main():
    args = parse_args()
    if not all((HOST, USER, PASS)):
        raise RuntimeError(
            "Configura LEXIA_FTP_HOST, LEXIA_FTP_USER e LEXIA_FTP_PASSWORD prima del deploy."
        )
    files_to_upload = select_files(args.paths)
    print(f"Connecting to {HOST}...")
    ftp = ftplib.FTP(timeout=30)
    ftp.connect(HOST, 21)
    ftp.login(USER, PASS)
    ftp.set_pasv(True)
    print("Login success.")

    ensure_dir(ftp, REMOTE_BASE)

    if not args.skip_delete:
        for remote_path in REMOTE_FILES_TO_DELETE:
            try:
                ftp.delete(remote_path)
                print(f"Deleted obsolete file: {remote_path}")
            except ftplib.all_errors:
                pass

    for rel_path in files_to_upload:
        local_path = os.path.join(ROOT_DIR, rel_path)
        if not os.path.exists(local_path):
            print(f"Skip (not found): {rel_path}")
            continue
        remote_path = f"{REMOTE_BASE}/{rel_path.replace(os.sep, '/')}"
        ensure_dir(ftp, os.path.dirname(remote_path))
        upload_file(ftp, local_path, remote_path)

    ftp.quit()
    print("LexIA deployment complete.")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
