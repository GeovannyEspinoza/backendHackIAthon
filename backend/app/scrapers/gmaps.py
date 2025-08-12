from typing import Dict, Any
from loguru import logger
from app.config import REQUEST_TIMEOUT, PLAYWRIGHT_HEADLESS

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except Exception:
    PLAYWRIGHT_OK = False


def scrape_gmaps(query: str, mock: bool = False) -> Dict[str, Any]:
    if mock or not query:
        logger.info("GMaps en modo MOCK")
        return {"query": query or "sample_business", "rating": 4.3, "reviews": 128}

    if not PLAYWRIGHT_OK:
        logger.warning("Playwright no disponible; usando datos vacíos.")
        return {"query": query, "rating": 0.0, "reviews": 0}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
            page = browser.new_page()
            page.set_default_timeout(REQUEST_TIMEOUT * 1000)
            page.goto("https://www.google.com/maps")
            try:
                page.locator("button:has-text('Aceptar todo')").first.click(timeout=3000)
            except Exception:
                pass

            page.locator("input#searchboxinput").fill(query)
            page.locator("button#searchbox-searchbutton").click()
            page.wait_for_timeout(3000)

            rating = 0.0
            reviews = 0
            try:
                rating_txt = page.locator("span[aria-label*='estrellas']").first.inner_text(timeout=4000)
                rating = _parse_rating(rating_txt)
            except Exception:
                pass
            try:
                reviews_txt = page.locator("button[jsaction*='pane.rating.moreReviews']").first.inner_text(timeout=4000)
                reviews = _parse_reviews(reviews_txt)
            except Exception:
                pass
            finally:
                browser.close()

            return {"query": query, "rating": rating, "reviews": reviews}
    except Exception as e:
        logger.error(f"Fallo scraping GMaps: {e}")
        return {"query": query, "rating": 0.0, "reviews": 0}


def _parse_rating(s: str) -> float:
    s = (s or "").strip().replace(",", ".")
    try:
        return float(s.split(" ")[0])
    except Exception:
        return 0.0


def _parse_reviews(s: str) -> int:
    s = (s or "").lower()
    digits = "".join(ch for ch in s if ch.isdigit())
    try:
        return int(digits) if digits else 0
    except Exception:
        return 0