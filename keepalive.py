"""Visit each Streamlit Community Cloud app in a real browser so it counts as traffic and never hibernates.
Wakes an app that already went to sleep. Exits non-zero if any app is unhealthy."""
import sys, time, urllib.request
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
# Static pages (GitHub Pages) never hibernate, so there is nothing to wake: this only checks that they answer and still contain
# the expected text, so a broken deploy fails this run (GitHub emails the owner) instead of going unnoticed.
STATIC = [
    ("https://alfiochoa.github.io/", "Alfredo Ochoa"),                                 # portfolio site (repo alfiochoa/alfiochoa.github.io)
    ("https://alfiochoa.github.io/projects/n8n-automation-hub/", "n8n Automation Hub"),
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

def check_static(url, expect):
    last = "no answer"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "portfolio-keepalive"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read(400_000).decode("utf-8", "replace")
                if r.status == 200 and expect in body:
                    return True, "ok"
                last = f"HTTP {r.status}, expected text {'found' if expect in body else 'missing'}"
        except Exception as e:
            last = type(e).__name__
        time.sleep(5)
    return False, last

def main():
    bad = []
    for url, expect in STATIC:
        ok, msg = check_static(url, expect)
        print(("OK  " if ok else "FAIL"), url, "-", msg, "(static page)", flush=True)
        if not ok: bad.append(url)
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
