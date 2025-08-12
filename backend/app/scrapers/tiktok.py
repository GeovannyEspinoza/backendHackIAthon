from typing import Dict, Any, List
from loguru import logger
from app.config import REQUEST_TIMEOUT, PLAYWRIGHT_HEADLESS

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except Exception:
    PLAYWRIGHT_OK = False


def scrape_tiktok(username: str, mock: bool = False) -> Dict[str, Any]:
    if mock or not username:
        logger.info("TikTok en modo MOCK")
        return {
            "username": username or "sample_user",
            "followers": 1200,
            "videos": [
                {"id": "v1", "likes": 320, "comments": 12, "shares": 5},
                {"id": "v2", "likes": 110, "comments": 4, "shares": 2},
            ],
        }

    if not PLAYWRIGHT_OK:
        logger.warning("Playwright no disponible; usando datos vacíos.")
        return {"username": username, "followers": 0, "videos": []}

    url = f"https://www.tiktok.com/@{username}"
    logger.info(f"Scrape TikTok real: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
            page = browser.new_page()
            page.set_default_timeout(REQUEST_TIMEOUT * 1000)
            page.goto(url)
            try:
                page.locator("button:has-text('Accept all')").first.click(timeout=3000)
            except Exception:
                pass

            followers = 0
            try:
                counters = page.locator("strong[data-e2e='followers-count']").first
                txt = counters.inner_text(timeout=4000)
                followers = _parse_compact_number(txt)
            except Exception:
                logger.warning("No se pudo leer followers")

            videos: List[Dict[str, Any]] = []
            try:
                thumbs = page.locator("div[data-e2e='user-post-item']").all()[:6]
                for i, item in enumerate(thumbs):
                    like_txt = "0"
                    try:
                        like_txt = item.locator("strong").first.inner_text(timeout=2000)
                    except Exception:
                        pass
                    videos.append({
                        "id": f"v{i+1}",
                        "likes": _parse_compact_number(like_txt),
                        "comments": 0,
                        "shares": 0,
                    })
            except Exception:
                logger.warning("No se pudieron listar videos")
            finally:
                browser.close()

            return {"username": username, "followers": followers, "videos": videos}
    except Exception as e:
        logger.error(f"Fallo scraping TikTok: {e}")
        return {"username": username, "followers": 0, "videos": []}


def _parse_compact_number(s: str) -> int:
    s = (s or "").strip().lower()
    try:
        if s.endswith("k"):
            return int(float(s[:-1].replace(',', '.')) * 1_000)
        if s.endswith("m"):
            return int(float(s[:-1].replace(',', '.')) * 1_000_000)
        return int(s.replace(',', '').replace('.', ''))
    except Exception:
        return 0