"""Visit each Streamlit Community Cloud app in a real browser so it counts as traffic and never hibernates.
Wakes an app that already went to sleep. Exits non-zero if any app is unhealthy."""
import sys, time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

APPS = [
    "https://alfredo-business-assistant.streamlit.app/",
    "https://alfredo-invoice.streamlit.app/",
    "https://alfredo-docs-assistant.streamlit.app/",
    "https://alfredo-ops-automation.streamlit.app/",
    "https://alfredo-price-stock-monitor.streamlit.app/",
    "https://alfredo-fx-monitor.streamlit.app/",
    "https://prediction-market-tracker.streamlit.app/",
    "https://alfredo-sp500-tracker.streamlit.app/",
]
WAKE = "Yes, get this app back up!"

def frames(page):
    return [f for f in page.frames if "streamlit.app" in f.url] or [page.main_frame]

def check(browser, url):
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    try:
        page.goto(url, timeout=90_000)
        woke = False
        for _ in range(12):                      # up to ~2 min for wake-up / cold start
            page.wait_for_timeout(10_000)
            for f in frames(page):
                btn = f.get_by_role("button", name=WAKE)
                if btn.count():
                    btn.first.click(); woke = True; page.wait_for_timeout(5_000)
                if f.locator('[data-testid="stApp"], [data-testid="stAppViewContainer"]').count():
                    body = f.locator("body").inner_text()
                    if "Traceback" in body or "ModuleNotFoundError" in body:
                        return False, "app shows an error"
                    return True, "woken from sleep" if woke else "already awake"
        return False, "app UI never appeared"
    except PWTimeout:
        return False, "timeout"
    finally:
        page.close()

def main():
    bad = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in APPS:
            ok, msg = check(browser, url)
            print(("OK  " if ok else "FAIL"), url, "-", msg, flush=True)
            if not ok: bad.append(url)
        browser.close()
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
