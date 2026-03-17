from typing import Any, Dict, List
from datetime import datetime
import json
import os


def get_directions(origin: str, destination: str, modes: List[str], departure_time: Any = None, alternatives: bool = True) -> List[Dict]:
    # Parse departure_time string into datetime for the Google client
    dt = None
    if departure_time is not None:
        if isinstance(departure_time, str):
            if departure_time.lower() == "now":
                dt = datetime.now()
            else:
                try:
                    dt = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
                except Exception:
                    dt = datetime.now()
        elif isinstance(departure_time, datetime):
            dt = departure_time

    try:
        import googlemaps_api  # from Program/

        routes = googlemaps_api.get_all_route_options(
            origin, destination,
            modes=modes or None,
            departure_time=dt,
            alternatives=alternatives,
        )
        if modes:
            routes = [r for r in routes if r.get("requested_mode") in modes]
        return routes
    except Exception:
        # Fallback to sample fixture for offline testing
        try:
            fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")
            sample_path = os.path.join(fixtures_dir, "google_routes_sample.json")
            with open(sample_path, "r", encoding="utf-8") as f:
                sample = json.load(f)
            # annotate requested_mode if missing
            out = []
            for r in sample:
                rm = r.get("requested_mode") or "transit"
                r["requested_mode"] = rm
                if not modes or rm in modes:
                    out.append(r)
            return out
        except Exception:
            return []
