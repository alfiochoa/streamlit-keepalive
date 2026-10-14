"""Report the shared Twelve Data key's usage (the /api_usage endpoint is free) and fail loudly if the day's budget is nearly gone.
Several demos share one free key (800 credits/day, 8/min): sp500-tracker and market-desk run scheduled jobs; visitors never spend credits."""
import json, os, sys, urllib.request

WARN = 650   # credits/day: the data jobs themselves stop spending near here (see their guards)
key = os.environ.get("TWELVE_DATA_API_KEY", "")
if not key:
    sys.exit("TWELVE_DATA_API_KEY not set")
u = json.load(urllib.request.urlopen(f"https://api.twelvedata.com/api_usage?apikey={key}", timeout=20))
used, cap = u.get("daily_usage"), u.get("plan_daily_limit")
print(f"OK   twelvedata usage today: {used}/{cap} credits (plan {u.get('plan_category')}, {u.get('plan_limit')}/min) at {u.get('timestamp')} UTC")
if used is None or cap is None:
    sys.exit(f"unexpected response: {u}")
if used >= WARN:
    sys.exit(f"WARN twelvedata usage {used}/{cap} >= {WARN}: check scheduled jobs")
