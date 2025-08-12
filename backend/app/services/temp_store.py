from __future__ import annotations
from pathlib import Path
from datetime import datetime
import tempfile, os, json
from typing import Dict, Any

from app.config import DATA_DIR

TMP_DIR = DATA_DIR / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
TXT_PATH = TMP_DIR / "ultimo_resultado.txt"


def write_temp_txt(payload: Dict[str, Any]) -> str:
    comp = payload.get("component_scores", {})
    resumen = [
        f"[{datetime.now().isoformat(timespec='seconds')}] Resultado de evaluación",
        f"RUC: {payload.get('ruc')}",
        f"Score final: {payload.get('final_score')}",
        f"Riesgo: {payload.get('risk_label')}",
        "",
        "Componentes:",
        f"  - Maps:   {comp.get('maps')}",
        f"  - TikTok: {comp.get('tt')}",
        "",
        "JSON crudo:",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    ]
    text = "\n".join(resumen)

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        tmp.write(text)
        tmp_path = tmp.name
    os.replace(tmp_path, TXT_PATH)
    return str(TXT_PATH)


def read_temp_txt() -> str:
    return TXT_PATH.read_text(encoding="utf-8")