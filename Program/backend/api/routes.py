import json
import os
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Optional
from ..models.schemas import (
    TripRequest,
    RoutesResponse,
    AssessmentResponse,
    DatasetsStatusResponse,
    Settings,
    AssessmentInput,
)
from ..services.caching import global_cache
from ..models.schemas import DatasetStatus
from ..services.routing import rank_routes, add_explanations
from ..services.scoring import RISK_NUMERIC
from ..services.assessment import assess_segments_from_google_route
from ..services.routing import aggregate_route_risks, build_route_steps, estimate_cost
from ..clients.google import get_directions


router = APIRouter()


@router.get("/routes", response_model=RoutesResponse)
def get_routes(
    origin: str,
    destination: str,
    departure_time: Optional[str] = None,
    mrt_only: bool = False,
    public_only: bool = False,
    taxi: bool = True,
    drive: bool = False,
    hybrid_taxi: bool = False,
    include_transit: Optional[bool] = None,
    include_driving: Optional[bool] = None,
    max_walk_min: Optional[int] = None,
    max_transfers: Optional[int] = None,
    max_budget: Optional[float] = None,
    wt_time: float = 0.25,
    wt_cost: float = 0.25,
    wt_risk: float = 0.25,
    wt_comfort: float = 0.25,
):
    trip = TripRequest(
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        mrt_only=mrt_only,
        public_only=public_only,
        taxi=taxi,
        drive=drive,
        hybrid_taxi=hybrid_taxi,
        max_walk_min=max_walk_min,
        max_transfers=max_transfers,
        max_budget=max_budget,
        wt_time=wt_time,
        wt_cost=wt_cost,
        wt_risk=wt_risk,
        wt_comfort=wt_comfort,
    )

    weights = {
        "time": wt_time,
        "cost": wt_cost,
        "risk": wt_risk,
        "comfort": wt_comfort,
    }
    # New explicit toggle params take priority if provided.
    # Default: both transit and driving are ON.
    if include_transit is not None or include_driving is not None:
        modes = []
        if include_transit is not False:
            modes.append("transit")
        if include_driving is not False:
            modes.append("driving")
    elif mrt_only:
        modes = ["transit"]
    elif public_only:
        modes = ["transit"]
    else:
        modes = ["transit", "driving"]
    if not modes:
        modes = ["transit", "driving"]

    raw_routes = get_directions(origin, destination, modes=modes, departure_time=departure_time, alternatives=True)
    candidates = []
    for r in raw_routes:
        legs = r.get("legs", [])
        if not legs:
            continue
        leg = legs[0]
        duration_s = (leg.get("duration") or {}).get("value", 0)
        distance_m = (leg.get("distance") or {}).get("value", 0)
        mode = r.get("requested_mode", "transit")

        # Assess segments
        segs = assess_segments_from_google_route(r)
        crowd_cat, crowd_num, delay_cat, delay_num, uses_fallback = aggregate_route_risks(segs)

        # Build rich step-by-step breakdown
        route_steps, path_summary, transfers = build_route_steps(r, segs)

        cost_info = estimate_cost(distance_m, duration_s, "driving" if mode == "driving" else "transit")

        # Compute walking minutes from steps
        walk_min = sum(s.duration_min for s in route_steps if s.mode == "Walk")

        # Extract overview polyline from Google response if available
        overview_polyline = None
        try:
            overview_polyline = r.get("overview_polyline", {}).get("points")
        except Exception:
            pass

        candidates.append({
            "category": "Taxi/Private Hire" if mode == "driving" else "Public Transit",
            "path_summary": path_summary or ("Drive" if mode == "driving" else ""),
            "time_min": round(duration_s / 60.0, 1),
            "cost_est": cost_info["total"],
            "cost_breakdown": cost_info,
            "distance_km": round(distance_m / 1000.0, 2),
            "walk_min": round(walk_min, 1),
            "transfers": transfers if mode != "driving" else 0,
            "steps": [s.model_dump() for s in route_steps],
            "overview_polyline": overview_polyline,
            "risk_crowding_cat": crowd_cat.value,
            "risk_crowding_num": crowd_num,
            "risk_delay_cat": delay_cat.value,
            "risk_delay_num": delay_num,
            "risk_cat": max(crowd_cat.value, delay_cat.value, key=lambda c: {"Low": 1, "Medium": 2, "High": 3, "Unknown": 2}.get(c, 2)),
            "uses_fallback": uses_fallback,
        })

    # Deduplicate routes that use the same sequence of modes + stops
    def _route_fingerprint(c):
        parts = []
        for s in c.get("steps", []):
            parts.append(f"{s.get('mode', '')}|{s.get('line_name', '')}|{s.get('from_name', '')}|{s.get('to_name', '')}")
        return ">>".join(parts)

    seen = {}
    unique_candidates = []
    for c in candidates:
        fp = _route_fingerprint(c)
        if fp in seen:
            # Keep the faster one
            existing = seen[fp]
            if c.get("time_min", 0) < existing.get("time_min", 0):
                unique_candidates.remove(existing)
                seen[fp] = c
                unique_candidates.append(c)
        else:
            seen[fp] = c
            unique_candidates.append(c)

    # Apply constraints filters
    filtered = []
    for c in unique_candidates:
        if max_transfers is not None and c.get("transfers", 0) > max_transfers:
            continue
        if max_walk_min is not None and c.get("walk_min", 0.0) > max_walk_min:
            continue
        if max_budget is not None and c.get("cost_est", 0.0) > max_budget:
            continue
        filtered.append(c)

    if not filtered:
        return RoutesResponse(trip=trip, routes=[], message="No routes found or API unavailable")

    ranked = rank_routes(filtered, weights)
    add_explanations(ranked, weights)
    # Select top 3 overall
    top = ranked[:3]
    return RoutesResponse(trip=trip, routes=top)


@router.get("/assessment", response_model=AssessmentResponse)
def get_assessment(
    origin: str,
    destination: str,
    departure_time: Optional[str] = None,
):
    trip = TripRequest(origin=origin, destination=destination, departure_time=departure_time)
    # Prefer transit for segment-level assessment; fall back to driving if needed
    routes = get_directions(origin, destination, modes=["transit"], departure_time=departure_time, alternatives=False)
    if not routes:
        routes = get_directions(origin, destination, modes=["driving"], departure_time=departure_time, alternatives=False)
    if not routes:
        return AssessmentResponse(trip=trip, segments=[], message="No routes found or API unavailable")
    segs = assess_segments_from_google_route(routes[0])
    return AssessmentResponse(trip=trip, segments=segs)


@router.post("/assessment", response_model=AssessmentResponse)
def post_assessment(body: AssessmentInput):
    segs = assess_segments_from_google_route(body.route)
    # Trip fields are unknown here; return placeholders
    trip = TripRequest(origin="", destination="")
    return AssessmentResponse(trip=trip, segments=segs)


@router.get("/datasets", response_model=DatasetsStatusResponse)
def datasets_status():
    status_raw = global_cache.status()
    sources = {}
    for name, s in status_raw.items():
        sources[name] = DatasetStatus(
            last_retrieved=None if s["last_retrieved"] is None else str(s["last_retrieved"]),
            ttl_sec=s["ttl_sec"],
            is_fallback=s["is_fallback"],
            source=s["source"],
        )
    return DatasetsStatusResponse(sources=sources)


SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")


def _load_settings() -> Settings:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Settings(**data)
    except Exception:
        return Settings()


def _save_settings(s: Settings) -> None:
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(s.model_dump(), f, indent=2)
    except Exception:
        pass


_SETTINGS = _load_settings()


@router.get("/settings", response_model=Settings)
def get_settings():
    return _SETTINGS


@router.put("/settings", response_model=Settings)
def update_settings(settings: Settings):
    global _SETTINGS
    _SETTINGS = settings
    _save_settings(_SETTINGS)
    return _SETTINGS


@router.post("/refresh", response_model=DatasetsStatusResponse)
def refresh_datasets():
    # Invalidate all cache; return empty/initial status snapshot
    global_cache.invalidate()
    status_raw = global_cache.status()
    sources = {}
    for name, s in status_raw.items():
        sources[name] = DatasetStatus(
            last_retrieved=None if s["last_retrieved"] is None else str(s["last_retrieved"]),
            ttl_sec=s["ttl_sec"],
            is_fallback=s["is_fallback"],
            source=s["source"],
        )
    return DatasetsStatusResponse(sources=sources)


# --- Minimal Google Maps passthrough (no fallbacks) ---
@router.get("/gmaps/directions")
def gmaps_directions(
    origin: str,
    destination: str,
    mode: str = "transit",
    alternatives: bool = True,
    departure_time: Optional[str] = None,
    raw: bool = False,
    detail: bool = False,
):
    try:
        import googlemaps  # local import to simplify testing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"googlemaps client not available: {e}")

    key = os.getenv("GOOGLE_MAPS_KEY", "")
    if not key:
        raise HTTPException(status_code=400, detail="Missing GOOGLE_MAPS_KEY; set it in .env")

    mode = mode.lower()
    allowed = {"driving", "walking", "bicycling", "transit"}
    if mode not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid mode '{mode}'. Allowed: {sorted(allowed)}")

    # Parse departure_time: ISO8601 or "now"; default to now
    dt: Optional[datetime]
    if departure_time is None or departure_time.lower() == "now":
        dt = datetime.now()
    else:
        try:
            dt = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid departure_time. Use ISO8601 or 'now'.")

    gmaps = googlemaps.Client(key=key)
    try:
        res = gmaps.directions(
            origin,
            destination,
            mode=mode,
            departure_time=dt,
            alternatives=alternatives,
            region="sg",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google Directions error: {e}")

    def _strip_html(text: str) -> str:
        if not text:
            return ""
        # Remove HTML tags and entities
        text = re.sub(r"<[^>]+>", "", text)
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&gt;", ">")
            .replace("&lt;", "<")
        )
        return text.strip()

    def _expand_steps(leg: dict) -> list[dict]:
        out = []
        steps = leg.get("steps") or []
        for idx, st in enumerate(steps):
            tm = st.get("travel_mode") or ""
            dist = (st.get("distance") or {}).get("value", 0)
            dur = (st.get("duration") or {}).get("value", 0)
            start = st.get("start_location") or {}
            end = st.get("end_location") or {}
            item: dict = {
                "index": idx,
                "travel_mode": tm,
                "instruction": _strip_html(st.get("html_instructions", "")),
                "distance_m": dist,
                "duration_s": dur,
                "start": {"lat": start.get("lat"), "lng": start.get("lng")},
                "end": {"lat": end.get("lat"), "lng": end.get("lng")},
            }
            if tm == "TRANSIT":
                td = st.get("transit_details", {})
                line = (td.get("line") or {})
                veh = ((line.get("vehicle") or {}).get("type") or "").title()
                item["transit"] = {
                    "vehicle_type": veh,
                    "line_name": line.get("name"),
                    "line_short_name": line.get("short_name"),
                    "headsign": td.get("headsign"),
                    "departure_stop": (td.get("departure_stop") or {}).get("name"),
                    "departure_time_text": (td.get("departure_time") or {}).get("text"),
                    "arrival_stop": (td.get("arrival_stop") or {}).get("name"),
                    "arrival_time_text": (td.get("arrival_time") or {}).get("text"),
                    "num_stops": td.get("num_stops"),
                }
            # Include sub-steps for walking/driving for clearer instructions
            sub = st.get("steps") or []
            if sub:
                item["substeps"] = [
                    {
                        "travel_mode": s.get("travel_mode"),
                        "instruction": _strip_html(s.get("html_instructions", "")),
                        "distance_m": (s.get("distance") or {}).get("value", 0),
                        "duration_s": (s.get("duration") or {}).get("value", 0),
                    }
                    for s in sub
                ]
            out.append(item)
        return out

    def _compute_mode_segments(leg: dict) -> list[dict]:
        segs: list[dict] = []
        steps = leg.get("steps") or []
        last_anchor = leg.get("start_address") or "Start"
        walk_dur_s = 0
        walk_dist_m = 0

        def flush_walk(next_anchor: str):
            nonlocal walk_dur_s, walk_dist_m, last_anchor
            if walk_dur_s > 0 or walk_dist_m > 0:
                segs.append(
                    {
                        "mode": "Walk",
                        "from": last_anchor,
                        "to": next_anchor,
                        "duration_min": round(walk_dur_s / 60.0, 1),
                        "distance_m": walk_dist_m,
                    }
                )
                walk_dur_s = 0
                walk_dist_m = 0
                last_anchor = next_anchor

        for st in steps:
            tm = st.get("travel_mode")
            dur_s = (st.get("duration") or {}).get("value", 0)
            dist_m = (st.get("distance") or {}).get("value", 0)
            if tm == "WALKING":
                walk_dur_s += dur_s
                walk_dist_m += dist_m
                continue
            if tm == "TRANSIT":
                td = st.get("transit_details", {})
                dep = (td.get("departure_stop") or {}).get("name") or "Departure"
                arr = (td.get("arrival_stop") or {}).get("name") or "Arrival"
                # Close out preceding walk to the departure stop
                flush_walk(dep)
                line = (td.get("line") or {})
                veh_raw = ((line.get("vehicle") or {}).get("type") or "").upper()
                mode_name = "Train" if veh_raw in {"SUBWAY", "HEAVY_RAIL", "RAIL"} else ("Bus" if veh_raw == "BUS" else veh_raw.title() or "Transit")
                segs.append(
                    {
                        "mode": mode_name,
                        "from": dep,
                        "to": arr,
                        "duration_min": round(dur_s / 60.0, 1),
                        "distance_m": dist_m,
                        "line": line.get("short_name") or line.get("name"),
                        "headsign": td.get("headsign"),
                        "num_stops": td.get("num_stops"),
                        "departure_time": (td.get("departure_time") or {}).get("text"),
                        "arrival_time": (td.get("arrival_time") or {}).get("text"),
                    }
                )
                last_anchor = arr
                continue
            # For other modes (driving/bicycling), treat as single segment
            flush_walk(last_anchor)
            segs.append(
                {
                    "mode": tm.title() if tm else "Unknown",
                    "from": last_anchor,
                    "to": leg.get("end_address") or "End",
                    "duration_min": round(dur_s / 60.0, 1),
                    "distance_m": dist_m,
                }
            )
            last_anchor = leg.get("end_address") or last_anchor

        # Trailing walk to the final destination
        if walk_dur_s > 0 or walk_dist_m > 0:
            segs.append(
                {
                    "mode": "Walk",
                    "from": last_anchor,
                    "to": leg.get("end_address") or "End",
                    "duration_min": round(walk_dur_s / 60.0, 1),
                    "distance_m": walk_dist_m,
                }
            )
        return segs

    def simplify(route: dict) -> dict:
        leg = (route.get("legs") or [{}])[0]
        duration_s = (leg.get("duration") or {}).get("value", 0)
        distance_m = (leg.get("distance") or {}).get("value", 0)
        steps_out = []
        for st in leg.get("steps", []) or []:
            tm = st.get("travel_mode")
            if tm == "TRANSIT":
                td = st.get("transit_details", {})
                line = (td.get("line") or {})
                veh = ((line.get("vehicle") or {}).get("type") or "").title()
                short = line.get("short_name") or line.get("name") or ""
                steps_out.append(f"{veh} {short}".strip())
            else:
                # Add duration mins for walks to improve clarity
                durm = round(((st.get("duration") or {}).get("value", 0)) / 60.0)
                if tm == "WALKING" and durm:
                    steps_out.append(f"Walk ~{durm} min")
                else:
                    steps_out.append(tm.title())
        result = {
            "summary": route.get("summary") or "",
            "mode": mode,
            "duration_min": round(duration_s / 60.0, 1),
            "distance_km": round(distance_m / 1000.0, 2),
            "steps": steps_out,
            "leg_start_address": leg.get("start_address"),
            "leg_end_address": leg.get("end_address"),
        }
        if detail:
            result["detailed_steps"] = _expand_steps(leg)
        # Add concise mode-change segments with anchors and durations
        result["mode_segments"] = _compute_mode_segments(leg)
        return result

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "alternatives": alternatives,
        "count": len(res),
        "routes": res if raw else [simplify(r) for r in res],
        "source": "live",
    }
