import os
import googlemaps
from datetime import datetime
from dotenv import load_dotenv

# Ensure env is loaded for local scripts too
load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_MAPS_KEY", "")
if not GOOGLE_KEY:
    raise RuntimeError("Missing GOOGLE_MAPS_KEY in environment or .env")

gmaps = googlemaps.Client(key=GOOGLE_KEY)

def get_all_route_options(origin, destination, modes=None, departure_time=None, alternatives=True):
    if modes is None:
        modes = ["transit", "driving"]
    if departure_time is None:
        departure_time = datetime.now()
    all_raw_routes = []

    for m in modes:
        res = gmaps.directions(
            origin,
            destination,
            mode=m,
            departure_time=departure_time,
            alternatives=alternatives,
            region="sg",
        )
        for route in res:
            route['requested_mode'] = m
        all_raw_routes.extend(res)

    return all_raw_routes

def process_google_with_lta(google_routes):
    processed_routes = []
    
    for route in google_routes:
        duration = route['legs'][0]['duration']['value'] / 60 
        
        route_risk_scores = []
        for step in route['legs'][0]['steps']:
            if step['travel_mode'] == 'TRANSIT':
                stop_name = step['transit_details']['departure_stop']['name']
                
                route_risk_scores.append(2) 
        
        final_risk = max(route_risk_scores) if route_risk_scores else 1
        
        processed_routes.append({
            "time": duration,
            "risk_val": final_risk,
            "google_raw": route
        })
        
    return processed_routes
