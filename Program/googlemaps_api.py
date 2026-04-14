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

def _fetch_mode(origin, destination, mode, departure_time, alternatives):
    """Fetch directions for a single mode (called in parallel)."""
    res = gmaps.directions(
        origin,
        destination,
        mode=mode,
        departure_time=departure_time,
        alternatives=alternatives,
        region="sg",
    )
    for route in res:
        route['requested_mode'] = mode
    return res


def get_all_route_options(origin, destination, modes=None, departure_time=None, alternatives=True):
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if modes is None:
        modes = ["transit", "driving"]
    if departure_time is None:
        departure_time = datetime.now()

    if len(modes) == 1:
        return _fetch_mode(origin, destination, modes[0], departure_time, alternatives)

    # Fetch all modes in parallel
    all_raw_routes = []
    with ThreadPoolExecutor(max_workers=len(modes)) as pool:
        futures = {
            pool.submit(_fetch_mode, origin, destination, m, departure_time, alternatives): m
            for m in modes
        }
        for fut in as_completed(futures):
            all_raw_routes.extend(fut.result())

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
