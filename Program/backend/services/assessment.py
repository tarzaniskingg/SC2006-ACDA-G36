import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
from ..models.schemas import SegmentAssessment, RiskIndicator, RiskCategory
from ..clients import lta as lta_client


LOAD_TO_CROWD = {
    "SEA": "Low",
    "SDA": "Medium",
    "LSD": "High",
}

# Singapore MRT station name -> (code, line_api_key)
# line_api_key is what LTA PCDForecast expects as TrainLine param
_MRT_STATIONS = {
    # East-West Line (EWL)
    "pasir ris": ("EW1", "EWL"), "tampines": ("EW2", "EWL"), "simei": ("EW3", "EWL"),
    "tanah merah": ("EW4", "EWL"), "bedok": ("EW5", "EWL"), "kembangan": ("EW6", "EWL"),
    "eunos": ("EW7", "EWL"), "paya lebar": ("EW8", "EWL"), "aljunied": ("EW9", "EWL"),
    "kallang": ("EW10", "EWL"), "lavender": ("EW11", "EWL"), "bugis": ("EW12", "EWL"),
    "city hall": ("EW13", "EWL"), "raffles place": ("EW14", "EWL"), "tanjong pagar": ("EW15", "EWL"),
    "outram park": ("EW16", "EWL"), "tiong bahru": ("EW17", "EWL"), "redhill": ("EW18", "EWL"),
    "queenstown": ("EW19", "EWL"), "commonwealth": ("EW20", "EWL"), "buona vista": ("EW21", "EWL"),
    "dover": ("EW22", "EWL"), "clementi": ("EW23", "EWL"), "jurong east": ("EW24", "EWL"),
    "chinese garden": ("EW25", "EWL"), "lakeside": ("EW26", "EWL"), "boon lay": ("EW27", "EWL"),
    "pioneer": ("EW28", "EWL"), "joo koon": ("EW29", "EWL"), "gul circle": ("EW30", "EWL"),
    "tuas crescent": ("EW31", "EWL"), "tuas west road": ("EW32", "EWL"), "tuas link": ("EW33", "EWL"),
    "expo": ("CG1", "EWL"), "changi airport": ("CG2", "EWL"),
    # North-South Line (NSL)
    "jurong east ns": ("NS1", "NSL"), "bukit batok": ("NS2", "NSL"), "bukit gombak": ("NS3", "NSL"),
    "choa chu kang": ("NS4", "NSL"), "yew tee": ("NS5", "NSL"), "kranji": ("NS7", "NSL"),
    "marsiling": ("NS8", "NSL"), "woodlands": ("NS9", "NSL"), "admiralty": ("NS10", "NSL"),
    "sembawang": ("NS11", "NSL"), "canberra": ("NS12", "NSL"), "yishun": ("NS13", "NSL"),
    "khatib": ("NS14", "NSL"), "ang mo kio": ("NS16", "NSL"), "bishan": ("NS17", "NSL"),
    "braddell": ("NS18", "NSL"), "toa payoh": ("NS19", "NSL"), "novena": ("NS20", "NSL"),
    "newton": ("NS21", "NSL"), "orchard": ("NS22", "NSL"), "somerset": ("NS23", "NSL"),
    "dhoby ghaut": ("NS24", "NSL"), "marina bay": ("NS27", "NSL"),
    "marina south pier": ("NS28", "NSL"),
    # North-East Line (NEL)
    "harbourfront": ("NE1", "NEL"), "outram park ne": ("NE3", "NEL"),
    "chinatown": ("NE4", "NEL"), "clarke quay": ("NE5", "NEL"),
    "dhoby ghaut ne": ("NE6", "NEL"), "little india": ("NE7", "NEL"),
    "farrer park": ("NE8", "NEL"), "boon keng": ("NE9", "NEL"),
    "potong pasir": ("NE10", "NEL"), "woodleigh": ("NE11", "NEL"),
    "serangoon": ("NE12", "NEL"), "kovan": ("NE13", "NEL"),
    "hougang": ("NE14", "NEL"), "buangkok": ("NE15", "NEL"),
    "sengkang": ("NE16", "NEL"), "punggol": ("NE17", "NEL"),
    # Circle Line (CCL)
    "dhoby ghaut cc": ("CC1", "CCL"), "bras basah": ("CC2", "CCL"),
    "esplanade": ("CC3", "CCL"), "promenade": ("CC4", "CCL"),
    "nicoll highway": ("CC5", "CCL"), "stadium": ("CC6", "CCL"),
    "mountbatten": ("CC7", "CCL"), "dakota": ("CC8", "CCL"),
    "paya lebar cc": ("CC9", "CCL"), "macpherson": ("CC10", "CCL"),
    "tai seng": ("CC11", "CCL"), "bartley": ("CC12", "CCL"),
    "serangoon cc": ("CC13", "CCL"), "lorong chuan": ("CC14", "CCL"),
    "bishan cc": ("CC15", "CCL"), "marymount": ("CC16", "CCL"),
    "caldecott": ("CC17", "CCL"), "botanic gardens": ("CC19", "CCL"),
    "farrer road": ("CC20", "CCL"), "holland village": ("CC21", "CCL"),
    "buona vista cc": ("CC22", "CCL"), "one-north": ("CC23", "CCL"),
    "kent ridge": ("CC24", "CCL"), "haw par villa": ("CC25", "CCL"),
    "pasir panjang": ("CC26", "CCL"), "labrador park": ("CC27", "CCL"),
    "telok blangah": ("CC28", "CCL"), "harbourfront cc": ("CC29", "CCL"),
    "bayfront": ("CE1", "CCL"), "marina bay cc": ("CE2", "CCL"),
    # Downtown Line (DTL)
    "bukit panjang": ("DT1", "DTL"), "cashew": ("DT2", "DTL"),
    "hillview": ("DT3", "DTL"), "hume": ("DT4", "DTL"),
    "beauty world": ("DT5", "DTL"), "king albert park": ("DT6", "DTL"),
    "sixth avenue": ("DT7", "DTL"), "tan kah kee": ("DT8", "DTL"),
    "botanic gardens dt": ("DT9", "DTL"), "stevens": ("DT10", "DTL"),
    "newton dt": ("DT11", "DTL"), "little india dt": ("DT12", "DTL"),
    "rochor": ("DT13", "DTL"), "bugis dt": ("DT14", "DTL"),
    "promenade dt": ("DT15", "DTL"), "bayfront dt": ("DT16", "DTL"),
    "downtown": ("DT17", "DTL"), "telok ayer": ("DT18", "DTL"),
    "chinatown dt": ("DT19", "DTL"), "fort canning": ("DT20", "DTL"),
    "bencoolen": ("DT21", "DTL"), "jalan besar": ("DT22", "DTL"),
    "bendemeer": ("DT23", "DTL"), "geylang bahru": ("DT24", "DTL"),
    "mattar": ("DT25", "DTL"), "macpherson dt": ("DT26", "DTL"),
    "ubi": ("DT27", "DTL"), "kaki bukit": ("DT28", "DTL"),
    "bedok north": ("DT29", "DTL"), "bedok reservoir": ("DT30", "DTL"),
    "tampines west": ("DT31", "DTL"), "tampines dt": ("DT32", "DTL"),
    "tampines east": ("DT33", "DTL"), "upper changi": ("DT34", "DTL"),
    "expo dt": ("DT35", "DTL"),
    # Thomson-East Coast Line (TEL)
    "woodlands north": ("TE1", "TEL"), "woodlands te": ("TE2", "TEL"),
    "woodlands south": ("TE3", "TEL"), "springleaf": ("TE4", "TEL"),
    "lentor": ("TE5", "TEL"), "mayflower": ("TE6", "TEL"),
    "bright hill": ("TE7", "TEL"), "upper thomson": ("TE8", "TEL"),
    "caldecott te": ("TE9", "TEL"), "mount pleasant": ("TE10", "TEL"),
    "stevens te": ("TE11", "TEL"), "napier": ("TE12", "TEL"),
    "orchard boulevard": ("TE13", "TEL"), "orchard te": ("TE14", "TEL"),
    "great world": ("TE15", "TEL"), "havelock": ("TE16", "TEL"),
    "outram park te": ("TE17", "TEL"), "maxwell": ("TE18", "TEL"),
    "shenton way": ("TE19", "TEL"), "marina bay te": ("TE20", "TEL"),
    "marina south": ("TE21", "TEL"), "gardens by the bay": ("TE22", "TEL"),
    "tanjong rhu": ("TE23", "TEL"), "katong park": ("TE24", "TEL"),
    "tanjong katong": ("TE25", "TEL"), "marine parade": ("TE26", "TEL"),
    "marine terrace": ("TE27", "TEL"), "siglap": ("TE28", "TEL"),
    "bayshore": ("TE29", "TEL"),
}

# Also build a reverse lookup: station code -> line
_CODE_TO_LINE = {}
for _name, (_code, _line) in _MRT_STATIONS.items():
    _CODE_TO_LINE[_code] = _line


def _normalize_station_name(name: str) -> str:
    """Normalize Google-provided MRT station name for lookup."""
    n = name.lower().strip()
    for suffix in [" mrt/bus int", " mrt station", " mrt stn", " mrt",
                   " station", " stn", " int", " interchange", " terminal"]:
        if n.endswith(suffix):
            n = n[: -len(suffix)].strip()
    return n


def _lookup_station(station_name: str) -> Optional[Tuple[str, str]]:
    """Resolve station name to (code, line). Returns None if not found."""
    normalized = _normalize_station_name(station_name)

    # Direct match
    if normalized in _MRT_STATIONS:
        return _MRT_STATIONS[normalized]

    # Substring match (e.g. "jurong east" matches "jurong east ns" entry too)
    for key, val in _MRT_STATIONS.items():
        if normalized in key or key in normalized:
            return val

    return None


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Bus stop lookup
# ---------------------------------------------------------------------------

_bus_stops_cache: Optional[List[Dict]] = None


def _get_bus_stops_list() -> List[Dict]:
    global _bus_stops_cache
    if _bus_stops_cache is not None:
        return _bus_stops_cache
    stops, _ts, _fb = lta_client.get_bus_stops()
    if stops:
        _bus_stops_cache = stops
    return stops or []


def _lookup_bus_stop_code(stop_name: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Optional[str]:
    stops = _get_bus_stops_list()
    if not stops:
        return None

    name_lower = stop_name.lower().strip()

    if lat is not None and lng is not None:
        best_code = None
        best_dist = 300.0
        for s in stops:
            try:
                slat = float(s.get("Latitude", 0))
                slng = float(s.get("Longitude", 0))
            except (TypeError, ValueError):
                continue
            d = _haversine_m(lat, lng, slat, slng)
            if d < best_dist:
                best_dist = d
                best_code = str(s.get("BusStopCode", ""))
        if best_code:
            return best_code

    for s in stops:
        desc = (s.get("Description") or "").lower().strip()
        road = (s.get("RoadName") or "").lower().strip()
        if name_lower == desc or name_lower in desc or desc in name_lower:
            return str(s.get("BusStopCode", ""))
        if name_lower == road or name_lower in road:
            return str(s.get("BusStopCode", ""))

    return None


# ---------------------------------------------------------------------------
# Risk indicator helper
# ---------------------------------------------------------------------------

def make_risk(cat: str, source: str = "realtime", is_fallback: bool = False, timestamp: str | None = None) -> RiskIndicator:
    num = {"Low": 1, "Medium": 2, "High": 3}.get(cat, 2)
    category = RiskCategory(cat) if cat in ["Low", "Medium", "High"] else RiskCategory.unknown
    return RiskIndicator(category=category, numeric=num, source=source, is_fallback=is_fallback, timestamp=timestamp)


# ---------------------------------------------------------------------------
# Bus crowding
# ---------------------------------------------------------------------------

def _bus_crowding_for_stop_and_service(stop_name: str, service_no: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Tuple[RiskIndicator, Dict]:
    stop_code = _lookup_bus_stop_code(stop_name, lat, lng)
    if not stop_code:
        return make_risk("Unknown", source="none"), {}

    data, ts, was_fallback = lta_client.get_bus_arrival(stop_code)
    try:
        services = data.get("Services") or []
        for svc in services:
            if str(svc.get("ServiceNo", "")).strip() == service_no.strip():
                load = svc["NextBus"]["Load"]
                cat = LOAD_TO_CROWD.get(load, "Unknown")
                return make_risk(cat, source="fallback" if was_fallback else "realtime", is_fallback=was_fallback, timestamp=str(ts) if ts else None), data
        if services:
            load = services[0]["NextBus"]["Load"]
            cat = LOAD_TO_CROWD.get(load, "Unknown")
        else:
            cat = "Unknown"
    except Exception:
        cat = "Unknown"
    return make_risk(cat, source="fallback" if was_fallback else "realtime", is_fallback=was_fallback, timestamp=str(ts) if ts else None), data


# ---------------------------------------------------------------------------
# MRT crowding — uses PCDForecast with TrainLine param + station code matching
# ---------------------------------------------------------------------------

def _mrt_crowding_for_station(station_name: str, query_time: Optional[datetime] = None) -> Tuple[RiskIndicator, Dict]:
    lookup = _lookup_station(station_name)
    if not lookup:
        return make_risk("Unknown", source="none"), {}

    station_code, train_line = lookup

    pcd, ts, was_fallback = lta_client.get_pcd_forecast(train_line=train_line)
    cat = "Unknown"

    try:
        values = pcd.get("value") or []
        # The response is a list with one item containing Stations array
        if not values or values[0] is None:
            return make_risk("Unknown", source="fallback", is_fallback=True), pcd

        stations_data = values[0].get("Stations") or []

        # Find our station by code
        for st in stations_data:
            if st.get("Station") == station_code:
                intervals = st.get("Interval") or []
                if not intervals:
                    break

                # Find the interval matching the query time (or current time)
                # Compare by time-of-day only (HH:MM) since PCD intervals
                # have today's date but query_time might be tomorrow
                now = query_time or datetime.now(timezone(timedelta(hours=8)))  # SGT
                now_minutes = now.hour * 60 + now.minute
                best_interval = intervals[0]  # default to first
                for iv in intervals:
                    try:
                        iv_start = datetime.fromisoformat(iv["Start"])
                        iv_minutes = iv_start.hour * 60 + iv_start.minute
                        if iv_minutes <= now_minutes:
                            best_interval = iv
                        else:
                            break
                    except Exception:
                        continue

                level = (best_interval.get("CrowdLevel") or "").strip().lower()
                if level in ("l", "low"):
                    cat = "Low"
                elif level in ("m", "moderate", "medium", "mod"):
                    cat = "Medium"
                elif level in ("h", "high"):
                    cat = "High"
                break
    except Exception:
        cat = "Unknown"

    return make_risk(cat, source="fallback" if was_fallback else "realtime", is_fallback=was_fallback, timestamp=str(ts) if ts else None), pcd


# ---------------------------------------------------------------------------
# Train delay — uses TrainServiceAlerts
# ---------------------------------------------------------------------------

def _train_delay_for_segment(station_name: str) -> RiskIndicator:
    """Check if there are active service alerts affecting this station's line."""
    lookup = _lookup_station(station_name)

    alerts_data, ts, was_fallback = lta_client.get_train_service_alerts()

    try:
        alert_value = alerts_data.get("value") or {}
        status = alert_value.get("Status", 1)  # 1=normal, 2=disrupted

        if status == 1:
            # Normal service across all lines
            return make_risk("Low", source="fallback" if was_fallback else "realtime",
                             is_fallback=was_fallback, timestamp=str(ts) if ts else None)

        # There's a disruption — check if it affects our line
        affected = alert_value.get("AffectedSegments") or []
        if not affected:
            # Disruption exists but no specific segments listed — medium as precaution
            return make_risk("Medium", source="fallback" if was_fallback else "realtime",
                             is_fallback=was_fallback, timestamp=str(ts) if ts else None)

        if lookup:
            station_code, train_line = lookup
            # Map line API keys to alert line names
            line_name_map = {"EWL": "EWL", "NSL": "NSL", "NEL": "NEL", "CCL": "CCL", "DTL": "DTL", "TEL": "TEL"}
            our_line = line_name_map.get(train_line, train_line)

            for seg in affected:
                seg_line = seg.get("Line", "")
                if seg_line == our_line:
                    return make_risk("High", source="fallback" if was_fallback else "realtime",
                                     is_fallback=was_fallback, timestamp=str(ts) if ts else None)

            # Disruption exists but not on our line
            return make_risk("Low", source="fallback" if was_fallback else "realtime",
                             is_fallback=was_fallback, timestamp=str(ts) if ts else None)

        # Can't determine line — medium as precaution
        return make_risk("Medium", source="fallback" if was_fallback else "realtime",
                         is_fallback=was_fallback, timestamp=str(ts) if ts else None)

    except Exception:
        return make_risk("Unknown", source="fallback", is_fallback=True)


# ---------------------------------------------------------------------------
# Bus frequency risk — uses BusArrival next-bus gaps
# ---------------------------------------------------------------------------

def _bus_frequency_for_stop_and_service(
    stop_name: str, service_no: str,
    lat: Optional[float] = None, lng: Optional[float] = None,
) -> Optional[Dict]:
    """
    Return bus frequency data for a specific service at a stop.
    Uses the gap between NextBus and NextBus2 to estimate headway.
    """
    stop_code = _lookup_bus_stop_code(stop_name, lat, lng)
    if not stop_code:
        return None

    data, ts, was_fallback = lta_client.get_bus_arrival(stop_code)
    try:
        services = data.get("Services") or []
        svc_data = None
        for svc in services:
            if str(svc.get("ServiceNo", "")).strip() == service_no.strip():
                svc_data = svc
                break
        if not svc_data:
            return None

        next1_str = (svc_data.get("NextBus") or {}).get("EstimatedArrival", "")
        next2_str = (svc_data.get("NextBus2") or {}).get("EstimatedArrival", "")

        if not next1_str or not next2_str:
            return None

        next1 = datetime.fromisoformat(next1_str)
        next2 = datetime.fromisoformat(next2_str)
        frequency_min = max(1, round((next2 - next1).total_seconds() / 60))

        # Classify frequency
        if frequency_min <= 8:
            frequency_cat = "High"     # High frequency = Low risk
        elif frequency_min <= 15:
            frequency_cat = "Medium"
        else:
            frequency_cat = "Low"      # Low frequency = High risk

        # miss_penalty_min = frequency (you wait a full cycle if you miss it)
        miss_penalty_min = frequency_min

        # Time until next arrival from now
        now = datetime.now(timezone(timedelta(hours=8)))
        mins_to_next = max(0, round((next1 - now).total_seconds() / 60))

        return {
            "frequency_min": frequency_min,
            "frequency_cat": frequency_cat,
            "next_arrival_min": mins_to_next,
            "miss_penalty_min": miss_penalty_min,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Driving delay — uses TrafficSpeedBands
# ---------------------------------------------------------------------------

def _delay_risk_for_driving_segment(start_lat: Optional[float], start_lng: Optional[float],
                                     end_lat: Optional[float], end_lng: Optional[float]) -> RiskIndicator:
    speed_data, ts, was_fallback = lta_client.get_traffic_speed_bands()
    cat = "Unknown"

    if start_lat is None or start_lng is None:
        return make_risk(cat, source="fallback" if was_fallback else "realtime", is_fallback=was_fallback, timestamp=str(ts) if ts else None)

    try:
        items = speed_data.get("value") or []
        relevant_speeds = []
        for band in items:
            loc = band.get("Location") or ""
            try:
                parts = loc.split()
                if len(parts) >= 2:
                    blat, blng = float(parts[0]), float(parts[1])
                    d = _haversine_m(start_lat, start_lng, blat, blng)
                    if d < 1000:
                        speed = float(band.get("SpeedBand", 0))
                        relevant_speeds.append(speed)
                    elif end_lat is not None and end_lng is not None:
                        d2 = _haversine_m(end_lat, end_lng, blat, blng)
                        if d2 < 1000:
                            speed = float(band.get("SpeedBand", 0))
                            relevant_speeds.append(speed)
            except (ValueError, IndexError):
                continue

        if relevant_speeds:
            avg_speed = sum(relevant_speeds) / len(relevant_speeds)
            if avg_speed >= 6:
                cat = "Low"
            elif avg_speed >= 3:
                cat = "Medium"
            else:
                cat = "High"
    except Exception:
        cat = "Unknown"

    return make_risk(cat, source="fallback" if was_fallback else "realtime", is_fallback=was_fallback, timestamp=str(ts) if ts else None)


# ---------------------------------------------------------------------------
# Main assessment: parse Google route into assessed segments
# ---------------------------------------------------------------------------

def assess_segments_from_google_route(route: Dict, departure_time: Optional[datetime] = None) -> Tuple[List[SegmentAssessment], List[Optional[Dict]]]:
    """
    Assess segments from a Google route.
    Returns (segments, bus_frequencies) where bus_frequencies is a parallel list
    with frequency dicts for bus steps and None for others.
    """
    segments: List[SegmentAssessment] = []
    bus_frequencies: List[Optional[Dict]] = []
    mode = route.get("requested_mode")

    if mode == "driving":
        leg = (route.get("legs") or [{}])[0]
        start_addr = leg.get("start_address", "")
        end_addr = leg.get("end_address", "")
        start_loc = leg.get("start_location") or {}
        end_loc = leg.get("end_location") or {}
        crowd = make_risk("Unknown")
        delay = _delay_risk_for_driving_segment(
            start_loc.get("lat"), start_loc.get("lng"),
            end_loc.get("lat"), end_loc.get("lng"),
        )
        segments.append(
            SegmentAssessment(mode="DRIVING", from_name=start_addr, to_name=end_addr, crowding=crowd, delay=delay)
        )
        bus_frequencies.append(None)
        return segments, bus_frequencies

    try:
        steps = route["legs"][0]["steps"]
    except Exception:
        return segments, bus_frequencies

    for step in steps:
        if step.get("travel_mode") != "TRANSIT":
            continue
        details = step.get("transit_details", {})
        vehicle = ((details.get("line", {}).get("vehicle", {}) or {}).get("type") or "").upper()
        dep_stop = details.get("departure_stop", {})
        arr_stop = details.get("arrival_stop", {})
        dep_name = dep_stop.get("name", "")
        arr_name = arr_stop.get("name", "")
        dep_loc = dep_stop.get("location") or {}
        dep_lat = dep_loc.get("lat")
        dep_lng = dep_loc.get("lng")

        line = details.get("line", {})
        service_no = line.get("short_name") or line.get("name") or ""

        freq_data = None
        if vehicle == "BUS":
            crowd, _ = _bus_crowding_for_stop_and_service(dep_name, service_no, dep_lat, dep_lng)
            delay = make_risk("Low", source="default")
            freq_data = _bus_frequency_for_stop_and_service(dep_name, service_no, dep_lat, dep_lng)
        elif vehicle in ("SUBWAY", "HEAVY_RAIL", "RAIL"):
            crowd, _ = _mrt_crowding_for_station(dep_name, query_time=departure_time)
            delay = _train_delay_for_segment(dep_name)
        else:
            crowd = make_risk("Unknown")
            delay = make_risk("Unknown")

        seg = SegmentAssessment(
            mode=vehicle or "TRANSIT",
            from_name=dep_name,
            to_name=arr_name,
            crowding=crowd,
            delay=delay,
        )
        segments.append(seg)
        bus_frequencies.append(freq_data)

    return segments, bus_frequencies
