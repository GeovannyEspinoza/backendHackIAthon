from typing import Dict, Any

def summarize_tiktok(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not raw:
        return {"videos": 0, "followers": 0, "engagement": 0.0}
    vids = raw.get("videos", [])
    followers = int(raw.get("followers", 0))
    likes = sum(int(v.get("likes", 0)) for v in vids)
    comments = sum(int(v.get("comments", 0)) for v in vids)
    shares = sum(int(v.get("shares", 0)) for v in vids)
    denom = max(1, followers)
    engagement = (likes + comments + shares) / denom
    return {
        "videos": len(vids),
        "followers": followers,
        "engagement": round(engagement, 4),
    }