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
    # Add short timeouts to avoid hanging; allow caller to catch exceptions
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)

    response.raise_for_status()
    data = response.json()
    return data

#bus arrival
def get_bus_arrival(bus_stop_code):
    return get(
        "v3/BusArrival",
        params={"BusStopCode": bus_stop_code})

#carpark availability 
def get_carpark_availability():
    return get("CarParkAvailabilityv2")

#est travel times
def get_est_travel_time():
    return get("EstTravelTimes")

#taxi availability
def get_taxi_availability():
    return get("Taxi-Availability")

#PCDForecast (station crowd density) — requires TrainLine param
def get_pcd_forecast(train_line=None):
    params = {}
    if train_line:
        params["TrainLine"] = train_line
    return get("PCDForecast", params=params or None)

#TrainServiceAlerts (disruptions/delays)
def get_train_service_alerts():
    return get("TrainServiceAlerts")

#traffic speed bands
def get_traffic_speed_bands():
    return get("v4/TrafficSpeedBands")

#bus stops (full list with codes, names, lat/lng)
def get_bus_stops():
    all_stops = []
    skip = 0
    while True:
        data = get("BusStops", params={"$skip": skip})
        batch = data.get("value", [])
        if not batch:
            break
        all_stops.extend(batch)
        skip += len(batch)
    return all_stops
