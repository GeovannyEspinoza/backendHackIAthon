import argparse, json
from app.scrapers.gmaps import scrape_gmaps

ap = argparse.ArgumentParser()
ap.add_argument("--q", required=True)
ap.add_argument("--mock", action="store_true")
args = ap.parse_args()

print(json.dumps(scrape_gmaps(args.q, mock=args.mock), ensure_ascii=False))