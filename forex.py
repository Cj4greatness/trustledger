import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
_cache = {"rate": None, "fetched_at": 0}
CACHE_SECONDS = 3600  # refresh once an hour, no need to call more often

def get_usd_to_ngn_rate():
    now = time.time()
    if _cache["rate"] and (now - _cache["fetched_at"] < CACHE_SECONDS):
        return _cache["rate"]

    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/USD/NGN"
        response = requests.get(url, timeout=5)
        data = response.json()
        rate = data["conversion_rate"]
        _cache["rate"] = rate
        _cache["fetched_at"] = now
        return rate
    except Exception:
        return _cache["rate"]  # fall back to last known rate, or None if we never got one
