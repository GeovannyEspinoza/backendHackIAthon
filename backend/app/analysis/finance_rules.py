from typing import Dict, Any, List


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def rule_based_financials(d: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback determinista si no hay LLM: score 0..100, límite crédito simple y 3 comentarios."""
    activos = safe_float(d.get("activos"))
    patrimonio = safe_float(d.get("patrimonio"))
    ingresos = safe_float(d.get("ingresos_ventas"))
    utilidad = safe_float(d.get("utilidad_neta"))
    deuda_total = safe_float(d.get("deuda_total"))
    gastos_fin = safe_float(d.get("gastos_financieros"))
    liquidez = safe_float(d.get("liquidez_corriente"))
    margen_bruto = safe_float(d.get("margen_bruto"))
    rent_ventas = safe_float(d.get("rent_neta_ventas"))
    roe = safe_float(d.get("roe"))
    roa = safe_float(d.get("roa"))

    comments: List[str] = []

    # penalizaciones
    risk = 50.0
    if patrimonio <= 0 or utilidad <= 0:
        risk = 90.0
        comments.append("Patrimonio o utilidad neta negativa.")
    if liquidez < 1:
        risk += 10
        comments.append("Liquidez corriente menor a 1.")
    if deuda_total > 0 and patrimonio > 0:
        leverage = deuda_total / max(patrimonio, 1)
        if leverage > 2:
            risk += 10
            comments.append("Apalancamiento elevado respecto al patrimonio.")
    if rent_ventas < 0.03:
        risk += 5
        comments.append("Rentabilidad neta sobre ventas baja.")
    if roe < 0.05:
        risk += 5
        comments.append("ROE bajo respecto al mercado.")

    risk = max(0, min(100, risk))

    # límite de crédito simple (ecuador-context): 10%-30% del patrimonio, ajustado por riesgo
    base = max(0.1, 0.3 - risk / 500)  # a mayor riesgo, menor porcentaje
    credit_limit = round(patrimonio * base, 2)

    if len(comments) < 3:
        comments += ["Información incompleta o no provista."] * (3 - len(comments))

    level = "low" if risk < 30 else "medium" if risk < 70 else "high"

    return {
        "score": int(round(risk)),
        "level": level,
        "creditLimit": float(credit_limit),
        "details": d,
        "comments": comments[:3]
    }