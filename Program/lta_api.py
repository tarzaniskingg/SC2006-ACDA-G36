import os
import requests
from dotenv import load_dotenv

BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice/"

# Load env for local scripts/runs
load_dotenv()

HEADERS = {
    "AccountKey": os.getenv("LTA_ACCOUNT_KEY", ""),
    "accept": "application/json"
}

def get(endpoint, params=None):
    url = BASE_URL + endpoint
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


def get_est_travel_time():
    return get("EstTravelTimes")


def get_taxi_availability():
    return get("Taxi-Availability")


def get_pcd_forecast(train_line=None):
    params = {}
    if train_line:
        params["TrainLine"] = train_line
    return get("PCDForecast", params=params or None)


def get_train_service_alerts():
    return get("TrainServiceAlerts")


def get_traffic_speed_bands():
    return {"value": _paginated_get("v4/TrafficSpeedBands")}


def get_bus_stops():
    return _paginated_get("BusStops")
