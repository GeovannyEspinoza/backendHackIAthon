from typing import Dict, Any, List
import json
from loguru import logger
from app.config import OPENAI_API_KEY
from app.analysis.finance_rules import rule_based_financials

try:
    from openai import OpenAI
    _OPENAI_OK = True
except Exception:
    _OPENAI_OK = False


PROMPT = """
Eres un analista financiero experto en crédito a PYMEs (contexto Ecuador).
Recibirás un JSON de datos clave.
Usa 5C, DSCR, apalancamiento y rentabilidad para asignar riesgo y límite de crédito.

Responde **exclusivamente** JSON con este formato:
{
  "score": int,                 # 0 (seguro) .. 100 (riesgo alto)
  "creditLimit": float,         # número en dólares
  "comments": ["factor 1", "factor 2", "factor 3"]
}
Si faltan datos, menciónalo en uno de los factores.
"""


def analyze_financials(d: Dict[str, Any]) -> Dict[str, Any]:
    """Usa OpenAI si hay API Key; si no, fallback determinista."""
    if not (OPENAI_API_KEY and _OPENAI_OK):
        return rule_based_financials(d)

    client = OpenAI(api_key=OPENAI_API_KEY)
    user_msg = json.dumps(d, ensure_ascii=False)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un analista financiero que responde únicamente JSON válido."},
                {"role": "user", "content": PROMPT + "\nDatos:\n" + user_msg}
            ],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        parsed = json.loads(raw)
        # normalización / defaults
        score = int(parsed.get("score", 50))
        credit_limit = float(parsed.get("creditLimit", 50000))
        comments: List[str] = list(parsed.get("comments", []))
    except Exception as e:
        logger.warning(f"LLM fallback por error: {e}")
        return rule_based_financials(d)

    while len(comments) < 3:
        comments.append("Información adicional insuficiente para análisis.")

    level = "low" if score < 30 else "medium" if score < 70 else "high"

    return {
        "score": score,
        "level": level,
        "creditLimit": credit_limit,
        "details": d,
        "comments": comments[:3]
    }