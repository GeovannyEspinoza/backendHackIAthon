# app/pipeline.py
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

BASE = Path(__file__).resolve().parent

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _safe_float(x) -> Optional[float]:
    try:
        if x is None: return None
        return float(x)
    except Exception:
        return None

def _risk_label_from_0_1(x: float) -> str:
    if x < 0.33: return "bajo"
    if x < 0.66: return "medio"
    return "alto"

def _load_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _score_from_maps_features(payload: Dict[str, Any]) -> Optional[float]:
    """Convierte features de Maps a score [0..1] (alto = más riesgo)."""
    try:
        rating = _safe_float(payload.get("rating_meta") or payload.get("rating"))
        n = int(payload.get("user_ratings_total_meta") or payload.get("user_ratings_total") or 0)
        if rating is None:
            return None
        rating_norm = max(0.0, min(1.0, 1.0 - (rating - 3.0)/2.0))  # 5★ ≈ 0 riesgo; 3★ ≈ 1 riesgo
        vol_bonus = 1.0 / (1.0 + math.log10(max(1, n)))             # más reviews → menos riesgo
        return max(0.0, min(1.0, 0.7 * rating_norm * vol_bonus))
    except Exception:
        return None

def _score_from_tiktok_features(payload: Dict[str, Any]) -> Optional[float]:
    """Usa overview.risk_score (0..100) si existe, lo lleva a 0..1."""
    try:
        ov = payload.get("overview") or {}
        rs = _safe_float(ov.get("risk_score"))
        if rs is None:
            return None
        return max(0.0, min(1.0, rs / 100.0))
    except Exception:
        return None

def _score_from_financial_placeholder(ruc: str) -> Optional[float]:
    return 0.6 if ruc else None

def fuse_scores(
    ruc: str,
    maps_payload: Optional[Dict[str, Any]],
    tiktok_payload: Optional[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    w = weights or {"fin": 0.6, "maps": 0.25, "tt": 0.15}

    fin = _score_from_financial_placeholder(ruc)
    mps = _score_from_maps_features(maps_payload or {}) if maps_payload else None
    tts = _score_from_tiktok_features(tiktok_payload or {}) if tiktok_payload else None

    w_fin, w_maps, w_tt = w["fin"], w["maps"], w["tt"]
    if fin is None:
        tot = max(1e-9, w_maps + w_tt)
        w_fin, w_maps, w_tt = 0.0, w_maps/tot, w_tt/tot

    final = 0.0
    totw = 0.0
    if fin is not None:  final += w_fin  * fin;  totw += w_fin
    if mps is not None:  final += w_maps* mps;  totw += w_maps
    if tts is not None:  final += w_tt  * tts;  totw += w_tt
    final = final / totw if totw > 0 else 0.0

    return {
        "component_scores": {"fin": fin, "maps": mps, "tt": tts},
        "final_score": final,
        "risk_label": _risk_label_from_0_1(final),
    }

def orchestrate(
    ruc: str,
    tiktok: str = "",
    gmaps: str = "",
    run_scrapers: bool = False,
    mock: bool = True,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Si mock=True lee:
      - app/sample_gmaps.json
      - app/sample_tiktok.json
    """
    used = {"gmaps": None, "tiktok": None}
    maps_payload = None
    tt_payload = None

    if mock:
        p_maps = BASE / "sample_gmaps.json"
        p_tt   = BASE / "sample_tiktok.json"
        if p_maps.exists():
            maps_payload = _load_json(p_maps)
            used["gmaps"] = str(p_maps)
        if p_tt.exists():
            tt_payload = _load_json(p_tt)
            used["tiktok"] = str(p_tt)
    else:
        # TODO: aquí integrar scrapers reales
        pass

    fused = fuse_scores(ruc, maps_payload, tt_payload, weights)
    return {
        "ruc": ruc,
        "used_files": used,
        **fused,
        "_generated_at": now_iso(),
    }
