"""Zero-cost watchdog for the whole portfolio. Runs on GitHub Actions (no AI, no tokens), pings the owner's phone via ntfy.sh on trouble.
Checks: (1) newest run of every workflow in every repo failed within the last WINDOW minutes, (2) public demo URLs answer.
Stateless de-duplication: a failed run only alerts if it finished inside the window since the previous check."""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

OWNER = "alfiochoa"
REPOS = ["ai-business-data-assistant", "payment-reconciliation-pipeline", "ai-invoice-intake", "order-ops-automation",
         "price-stock-monitor", "docs-support-assistant", "executive-bi-dashboard", "fx-rate-monitor",
         "prediction-market-tracker", "sp500-tracker", "n8n-automation-hub", "market-desk", "streamlit-keepalive", "alfiochoa.github.io"]
URLS = {  # name -> (url, timeout s). Streamlit apps are visited by the keep-alive job itself, so only static/hosted ones here.
    "market-desk": ("https://alfiochoa.github.io/market-desk/", 30),
    "executive-bi-dashboard": ("https://alfiochoa.github.io/executive-bi-dashboard/", 30),
    "n8n demo page": ("https://alfiochoa.github.io/n8n-automation-hub/", 30),
    "portfolio site": ("https://alfiochoa.github.io/", 30),
    "portfolio project page": ("https://alfiochoa.github.io/projects/n8n-automation-hub/", 30),
    "n8n backend /healthz": (os.environ.get("N8N_BASE_URL", "").rstrip("/") + "/healthz", 100),  # free Render service can take ~60-90 s to wake
}
WINDOW = int(os.environ.get("WINDOW_MIN", "45"))
TOKEN = os.environ.get("GITHUB_TOKEN", "")
TOPIC = os.environ.get("NTFY_TOPIC", "")

def get(url, timeout=30, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-monitor", **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)

def gh(path):
    h = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return json.load(get(f"https://api.github.com/{path}", 30, h))

problems = []
now = datetime.now(timezone.utc)
for repo in REPOS:
    try:
        runs = gh(f"repos/{OWNER}/{repo}/actions/runs?per_page=30&branch=main")["workflow_runs"]
    except Exception as e:
        problems.append(f"{repo}: cannot read runs ({type(e).__name__})")
        continue
    newest = {}
    for r in runs:                       # runs come newest first
        if r["status"] == "completed" and r["conclusion"] != "cancelled":
            newest.setdefault(r["name"], r)
    for name, r in newest.items():
        done = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
        if r["conclusion"] in ("failure", "timed_out") and (now - done).total_seconds() < WINDOW * 60:
            problems.append(f"{repo}: '{name}' {r['conclusion']} {r['html_url']}")

for name, (url, to) in URLS.items():
    if url.startswith("/"):
        continue
    ok = False
    for attempt in range(2):
        try:
            ok = 200 <= get(url, to).status < 400
        except Exception:
            ok = False
        if ok:
            break
        time.sleep(5)
    if not ok:
        problems.append(f"{name} not answering: {url}")

if not problems:
    print(f"OK   {len(REPOS)} repos and {len(URLS)} URLs healthy")
    sys.exit(0)
text = "\n".join(problems)
print("PROBLEMS\n" + text)
if TOPIC:
    try:
        req = urllib.request.Request(f"https://ntfy.sh/{TOPIC}", data=text.encode()[:3500], method="POST",
                                     headers={"Title": f"Portfolio: {len(problems)} problem(s)", "Priority": "high", "Tags": "warning"})
        urllib.request.urlopen(req, timeout=20)
        print("alert sent")
    except Exception as e:
        print(f"could not send alert: {type(e).__name__}")
sys.exit(1)
