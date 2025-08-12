import argparse, json
from app.scrapers.tiktok import scrape_tiktok

ap = argparse.ArgumentParser()
ap.add_argument("--user", required=True)
ap.add_argument("--mock", action="store_true")
args = ap.parse_args()

print(json.dumps(scrape_tiktok(args.user, mock=args.mock), ensure_ascii=False))