import os
import threading
import time
import requests
from dotenv import load_dotenv

BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice/"

# Load env for local scripts/runs
load_dotenv()

HEADERS = {
    "AccountKey": os.getenv("LTA_ACCOUNT_KEY", ""),
    "accept": "application/json"
}

# Global rate limiter: max 1 LTA call per 0.15s (~6/sec, well within typical quotas).
# Prevents parallel threads from bursting and hitting the quota.
_rate_lock = threading.Lock()
_last_call_time = 0.0
_MIN_INTERVAL = 0.15  # seconds between LTA API calls


def get(endpoint, params=None):
    global _last_call_time
    url = BASE_URL + endpoint

    with _rate_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL - (now - _last_call_time)
        if wait > 0:
            time.sleep(wait)
        _last_call_time = time.monotonic()

    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _paginated_get(endpoint):
    """Fetch all pages from a paginated LTA endpoint (max 500 per call)."""
    all_items = []
    skip = 0
    while True:
        data = get(endpoint, params={"$skip": skip})
        batch = data.get("value", [])
        if not batch:
            break
        all_items.extend(batch)
        skip += len(batch)
    return all_items


def get_bus_arrival(bus_stop_code):
    return get("v3/BusArrival", params={"BusStopCode": bus_stop_code})


def get_carpark_availability():
    return {"value": _paginated_get("CarParkAvailabilityv2")}



def get_pcd_forecast(train_line=None):
    params = {}
    if train_line:
        params["TrainLine"] = train_line
    return get("PCDForecast", params=params or None)


def get_pcd_realtime(train_line=None):
    params = {}
    if train_line:
        params["TrainLine"] = train_line
    return get("PCDRealTime", params=params or None)


def get_train_service_alerts():
    return get("TrainServiceAlerts")


def get_traffic_speed_bands():
    return {"value": _paginated_get("v4/TrafficSpeedBands")}


def get_bus_stops():
    return _paginated_get("BusStops")
