import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(BASE_DIR, "cases")


def safe_segment(value: str, label: str = "percorso") -> str:
    value = str(value or "")
    if (
        not value
        or value in {".", ".."}
        or value != os.path.basename(value)
        or "/" in value
        or "\\" in value
        or "\x00" in value
    ):
        raise ValueError(f"{label.capitalize()} non valido.")
    return value


def case_path(case_id: str, *segments: str) -> str:
    root = os.path.realpath(CASES_DIR)
    candidate = os.path.realpath(os.path.join(
        root,
        safe_segment(case_id, "identificativo fascicolo"),
        *(safe_segment(item) for item in segments),
    ))
    if os.path.commonpath([root, candidate]) != root:
        raise ValueError("Percorso fascicolo non valido.")
    return candidate
