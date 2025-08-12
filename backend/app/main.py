# backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import OrchestrateRequest, OrchestrateResponse, EvaluateRequest, ScoreResponse
from app.pipeline import orchestrate

app = FastAPI(title="Backend — Scraping + Finanzas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- root & health ---
@app.get("/")
def root():
    return {"ok": True, "message": "Backend running 🚀"}

@app.get("/healthz")
def healthz_root():
    return {"ok": True}

# --- namespaced /api ---
from fastapi import APIRouter
api = APIRouter(prefix="/api")

@api.get("/healthz")
def healthz_api():
    return {"ok": True}

@api.post("/orchestrate", response_model=OrchestrateResponse)
def api_orchestrate(body: OrchestrateRequest):
    try:
        res = orchestrate(
            ruc=body.ruc,
            tiktok=body.tiktok or "",
            gmaps=body.gmaps or body.gmaps,  # alias seguro
            run_scrapers=body.run_scrapers,
            mock=body.mock,
            weights=body.weights or {"fin":0.6,"maps":0.25,"tt":0.15},
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"orchestrate failed: {e}")

# (opcional) endpoint para score directo con data financiera/LLM
@api.post("/evaluate", response_model=ScoreResponse)
def api_evaluate(body: EvaluateRequest):
    d = body.financialData.dict()
    # Heurística muy simple (placeholder) — reemplaza con tu LLM si quieres
    ventas = d.get("ingresos_ventas") or 0
    utilidad = d.get("utilidad_neta") or 0
    deuda = d.get("deuda_total") or 0
    liquidez = d.get("liquidez_corriente") or 1

    # Menos riesgo si utilidad y liquidez son altos; más riesgo si deuda alta
    raw = 0.5
    try:
        if ventas > 0:
            margen = (utilidad / max(1.0, ventas))
            raw -= 0.3 * max(0.0, min(0.5, margen))       # mejor margen → reduce riesgo
        raw += 0.2 * min(1.0, deuda / max(1.0, ventas))    # deuda/ventas alto → sube riesgo
        raw -= 0.2 * max(0.0, min(1.0, (liquidez - 1.0)))  # liquidez >1 reduce riesgo
    except Exception:
        pass

    raw = max(0.0, min(1.0, raw))
    score_0_100 = round(100 * raw)
    level = "low" if score_0_100 < 30 else "medium" if score_0_100 < 70 else "high"
    credit = max(0.0, 100000 - score_0_100 * 1000)

    return {
        "score": score_0_100,
        "level": level,
        "creditLimit": credit,
        "details": d,
    }

app.include_router(api)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
