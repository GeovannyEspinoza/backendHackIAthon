from __future__ import annotations
import argparse, json
from pathlib import Path

from app.services.pipeline import run_pipeline
from app.services.temp_store import write_temp_txt

BASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description="Orquesta scrapers + pipeline + TXT")
    ap.add_argument("--ruc", required=True)
    ap.add_argument("--tiktok", default="")
    ap.add_argument("--gmaps", default="")
    ap.add_argument("--run-scrapers", action="store_true")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    result = run_pipeline(
        ruc=args.ruc,
        tiktok_user=args.tiktok,
        gmaps_query=args.gmaps,
        run_scrapers=args.run_scrapers,
        mock=args.mock,
    )
    txt_path = write_temp_txt(result)

    print(json.dumps({
        "ok": True,
        "txt_path": str(Path(txt_path).as_posix()),
        "summary": {
            "ruc": result.get("ruc"),
            "final_score": result.get("final_score"),
            "risk_label": result.get("risk_label"),
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()