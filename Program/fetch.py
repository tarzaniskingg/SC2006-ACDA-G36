import time
from datetime import datetime
from googlemaps_api import *
from lta_api import *

IMPORTANCE_LEVELS = {
    'travel_time': 2,  # Decreased from 3
    'reliability': 2,
    'comfort': 1,
    'budget': 3
}

DATASETS = {
    "bus_arrival":{
        "enabled": True,
        "bus_stops": ["27211"]
    },
    "carpark_availability":{
        "enabled": True
    },
    "travel_time":{
        "enabled": True
    },
    "taxi_availability":{
        "enabled": True
    },
    "pcd_forecast":{
        "enabled": True
    },
    "traffic_speed_band":{
        "enabled": True
    },
}

def transform_pcd_to_risk(pcd_data):
    """
    Implements FR 3.5: Converts PCD (Passenger Crowd Density) to Risk Scores
    LTA DataMall typically returns 'Low', 'Moderate', 'High' or color codes.
    """
    status = pcd_data.get('CrowdingLevel', 'Unknown')
    
    mapping = {
        "Low": {"label": "Low", "val": 1},
        "Moderate": {"label": "Medium", "val": 2},
        "High": {"label": "High", "val": 3},
        "Unknown": {"label": "Unknown", "val": 2} #default
    }
    return mapping.get(status, mapping["Unknown"])

def calculate_fare(route, mode):
    #total dist in m
    distance_m = route['legs'][0]['distance']['value']
    distance_km = distance_m / 1000
    
    if mode == "driving":
        #calculate taxi fare
        duration_mins = route['legs'][0]['duration']['value'] / 60
        fare = 4.10 + (distance_km * 0.70) + (duration_mins * 0.14)
        return round(fare, 2)
    else:
        #calculate train/bus fare
        fare = 0.95 + (distance_km * 0.10)
        return round(fare, 2)

def get_fallback_status(last_updated_str):
    """
    Implements FR 5.1 & 5.2: Data Freshness Management
    """
    fmt = "%Y-%m-%d %H:%M:%S"
    last_updated = datetime.strptime(last_updated_str, fmt)
    diff = (datetime.now() - last_updated).total_seconds() / 60
    
    return diff > 5

def run_assessment(stop_id):
    raw_bus = get_bus_arrival(stop_id) 
    
    try:
        load_status = raw_bus['Services'][0]['NextBus']['Load']
    except (KeyError, IndexError):
        load_status = "Unknown"

    mapping = {
        "SEA": {"label": "Low", "val": 1},
        "SDA": {"label": "Medium", "val": 2},
        "LSD": {"label": "High", "val": 3}
    }
    
    risk = mapping.get(load_status, {"label": "Unknown", "val": 2})

    return {
        "crowding_val": risk['val'],
        "is_fallback": False 
    }

def calculate_composite_score(route_attr, weights):
    """
    Formula: wt*T' + wR*R' + wC*C' + wB*B'
    Note: Attributes must be normalized (0.0 to 1.0) before calling this.
    """
    total_w = sum(weights.values())
    score = (
        ((weights['travel_time'] / total_w) * route_attr['normalized_time']) +
        ((weights['reliability'] / total_w) * route_attr['normalized_delay']) +
        ((weights['comfort'] / total_w) * route_attr['normalized_crowd']) +
        ((weights['budget'] / total_w) * route_attr['normalized_cost'])
    )
    return score

def get_trip_recommendations(origin, destination):
    raw_data = get_all_route_options(origin, destination)
    candidate_routes = process_google_with_lta(raw_data)
    normalized_routes = normalize_attributes(candidate_routes)

    for route in normalized_routes:
        route['score'] = calculate_composite_score(route, IMPORTANCE_LEVELS)

    grouped_results = {"Public Transit": [], "Taxi/Private Hire": []}

    ranked = sorted(normalized_routes, key=lambda x: x['score'])

    for route in ranked:
        cat = route['category']
        if len(grouped_results[cat]) < 3:
            grouped_results[cat].append(route)

    return grouped_results

def process_google_with_lta(google_routes):
    processed_routes = []
    
    for route in google_routes:
        duration = route['legs'][0]['duration']['value'] / 60 
        route_risk_scores = []
        specific_modes = []
        transfer_count = 0  
        
        mode_type = route.get('requested_mode', 'transit')
        
        if mode_type == 'driving':
            mode_summary = "Taxi / Private Hire"
            cost = calculate_fare(route, mode_type)
            comfort_val = 3 
            reliability_val = 2 
            route_risk_scores.append(1) 
        else:
            cost = calculate_fare(route, mode_type)
            comfort_val = 2 
            reliability_val = 1 
            
            for step in route['legs'][0]['steps']:
                if step['travel_mode'] == 'TRANSIT':
                    transfer_count += 1
                    details = step['transit_details']
                    line = details['line'].get('short_name', details['line'].get('name'))
                    specific_modes.append(f"{details['line']['vehicle']['type'].title()} {line}")
                    
                    stop_id = lookup_lta_stop_code(details['departure_stop']['name'])
                    segment_info = run_assessment(stop_id) 
                    route_risk_scores.append(segment_info['crowding_val'])
                else:
                    specific_modes.append("Walk")
            
            mode_summary = " -> ".join(specific_modes)
            comfort_val = max(1, comfort_val - (0.5 * (transfer_count - 1)))

        final_risk = max(route_risk_scores) if route_risk_scores else 1
        
        processed_routes.append({
            "time": duration,
            "delay_risk": final_risk,
            "cost": cost,
            "comfort": comfort_val, 
            "mode_summary": mode_summary,
            "category": "Taxi/Private Hire" if mode_type == "driving" else "Public Transit"
        })
        
    return processed_routes

def normalize_attributes(routes):
    comforts = [r['comfort'] for r in routes if 'comfort' in r]
    if not comforts: comforts = [1.0]
    
    def norm(val, val_list, invert=False):
        v_min, v_max = min(val_list), max(val_list)
        if v_max == v_min: return 0.5
        res = (val - v_min) / (v_max - v_min)
        return 1 - res if invert else res

    times = [r['time'] for r in routes]
    risks = [r['delay_risk'] for r in routes]
    costs = [r['cost'] for r in routes]
    comforts = [r['comfort'] for r in routes]

    for r in routes:
        r['normalized_time'] = norm(r['time'], times)
        r['normalized_delay'] = norm(r['delay_risk'], risks)
        r['normalized_cost'] = norm(r['cost'], costs)
        r['normalized_crowd'] = norm(r['comfort'], comforts, invert=True) 
        
    return routes

def lookup_lta_stop_code(stop_name):

    mapping = {
        "Jurong East Stn": "28009",
        "Aft Clementi Ave 1": "17091",
        "Opp Somerset Stn": "09038"
    }
    return mapping.get(stop_name, "28009")

if __name__ == "__main__":
    results = get_trip_recommendations("NTU North Spine", "Jurong Point") #start,end
    
    for mode, recommendations in results.items():
        print(f"\n>>> TOP 3 OPTIONS FOR: {mode.upper()} <<<")
        print(f"{'Rank':<5} | {'Score':<6} | {'Time':<7} | {'Cost':<7} | {'Risk':<5} | {'Path'}")
        print("-" * 105)
        
        for i, rec in enumerate(recommendations):
            risk_text = {1: "Low", 2: "Med", 3: "High"}.get(rec['delay_risk'], "???")
            print(f"{i+1:<5} | {rec['score']:<6.2f} | {rec['time']:<4.0f}m | ${rec['cost']:<5.2f} | {risk_text:<5} | {rec['mode_summary']}")