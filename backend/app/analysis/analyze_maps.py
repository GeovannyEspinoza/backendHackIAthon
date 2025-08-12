from typing import Dict, Any

def summarize_maps(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not raw:
        return {"reviews": 0, "rating": 0.0}
    reviews = int(raw.get("reviews", 0))
    rating = float(raw.get("rating", 0.0))
    return {"reviews": reviews, "rating": round(rating, 2)}