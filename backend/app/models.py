# backend/app/models.py
from __future__ import annotations
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# ---- Requests ----
class OrchestrateRequest(BaseModel):
    ruc: str = Field(..., min_length=8)
    tiktok: Optional[str] = ""
    gmaps: Optional[str] = ""
    run_scrapers: bool = False
    mock: bool = True
    headless: bool = True
    video_limit: int = 10
    comments_per_video: int = 5
    comment_pages: int = 3
    use_solver: bool = False
    weights: Optional[Dict[str, float]] = None  # {"fin":0.6,"maps":0.25,"tt":0.15}

class FinancialData(BaseModel):
    activos: float | None = None
    expediente: float | None = None
    impuesto_renta: float | None = None
    ingresos_ventas: float | None = None
    n_empleados: int | None = None
    nombre: str | None = None
    patrimonio: float | None = None
    ruc: str | None = None
    utilidad_neta: float | None = None
    liquidez_corriente: float | None = None
    deuda_total: float | None = None
    gastos_financieros: float | None = None
    margen_bruto: float | None = None
    rent_neta_ventas: float | None = None
    roe: float | None = None
    roa: float | None = None

class EvaluateRequest(BaseModel):
    financialData: FinancialData

# ---- Responses ----
class ScoreResponse(BaseModel):
    score: int
    level: str
    creditLimit: float
    details: Dict[str, Any]

class OrchestrateResponse(BaseModel):
    ruc: str
    used_files: Dict[str, Optional[str]]
    component_scores: Dict[str, Optional[float]]
    final_score: float
    risk_label: str
    _generated_at: str
