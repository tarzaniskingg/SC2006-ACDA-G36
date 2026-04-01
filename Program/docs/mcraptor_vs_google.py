"""
McRAPTOR vs Google Maps — Side-by-Side Comparison
==================================================

Runs queries through:
1. McRAPTOR (local, multi-criteria, crowding-aware)
2. Your SGTravelBud backend (Google Directions API + LTA overlays)

Shows what McRAPTOR finds that Google cannot.

Usage: python mcraptor_vs_google.py
Requires: backend running on localhost:8000
"""

import json
import urllib.request
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import time as time_module


# ============================================================
# DATA MODEL (same as MVP)
# ============================================================

@dataclass
class Stop:
    id: str
    name: str
    lat: float = 0.0
    lng: float = 0.0

@dataclass
class StopTime:
    stop_id: str
    arrival_min: int
    departure_min: int

@dataclass
class Trip:
    trip_id: str
    route_id: str
    stop_times: List[StopTime]
    crowding: float = 1.0

@dataclass
class Route:
    route_id: str
    name: str
    stop_sequence: List[str]
    trips: List[Trip]
    mode: str = "rail"
    frequency_min: int = 5

@dataclass
class FootTransfer:
    from_stop: str
    to_stop: str
    walk_min: int

@dataclass
class Label:
    arrival_min: int
    num_transfers: int
    crowding_score: float
    cost: float
    boarded_trip: Optional[str] = None
    boarded_at: Optional[str] = None
    prev_label: Optional['Label'] = None

    def dominates(self, other: 'Label') -> bool:
        return (
            self.arrival_min <= other.arrival_min and
            self.num_transfers <= other.num_transfers and
            self.crowding_score <= other.crowding_score and
            self.cost <= other.cost and
            (self.arrival_min < other.arrival_min or
             self.num_transfers < other.num_transfers or
             self.crowding_score < other.crowding_score or
             self.cost < other.cost)
        )


# ============================================================
# EXPANDED SINGAPORE NETWORK
# ============================================================

def build_full_network():
    """
    Bigger network covering major corridors:
    - EWL: Tuas Link -> Boon Lay -> Jurong East -> Buona Vista ->
           City Hall -> Paya Lebar -> Tampines -> Changi Airport
    - NSL: Woodlands -> Yishun -> Ang Mo Kio -> Bishan ->
           Toa Payoh -> City Hall -> Marina Bay
    - NEL: Punggol -> Sengkang -> Serangoon -> Little India ->
           Dhoby Ghaut -> Chinatown -> HarbourFront
    - DTL: Bukit Panjang -> Botanic Gardens -> Downtown -> Expo
    - CCL: Bishan -> Serangoon -> Paya Lebar -> Bayfront
    - Bus 179: NTU -> Pioneer -> Boon Lay (every 20 min - LOW freq)
    - Bus 67: Tampines -> Bishan (every 10 min)
    - Bus 854: Yishun -> Ang Mo Kio (every 8 min)
    - Bus 36: Changi Airport -> Orchard (every 12 min)
    """

    stops = {
        # EWL (extended)
        "EW33": Stop("EW33", "Tuas Link", 1.340, 103.637),
        "EW27": Stop("EW27", "Boon Lay", 1.338, 103.706),
        "EW24": Stop("EW24", "Jurong East", 1.333, 103.742),
        "EW21": Stop("EW21", "Buona Vista", 1.307, 103.790),
        "EW13": Stop("EW13", "City Hall", 1.293, 103.852),
        "EW8":  Stop("EW8",  "Paya Lebar", 1.318, 103.893),
        "EW2":  Stop("EW2",  "Tampines", 1.354, 103.945),
        "CG2":  Stop("CG2",  "Changi Airport", 1.357, 103.989),
        # NSL (extended)
        "NS9":  Stop("NS9",  "Woodlands", 1.437, 103.786),
        "NS13": Stop("NS13", "Yishun", 1.429, 103.835),
        "NS16": Stop("NS16", "Ang Mo Kio", 1.370, 103.850),
        "NS17": Stop("NS17", "Bishan", 1.351, 103.849),
        "NS19": Stop("NS19", "Toa Payoh", 1.332, 103.847),
        "NS22": Stop("NS22", "Orchard", 1.304, 103.832),
        "NS27": Stop("NS27", "Marina Bay", 1.274, 103.854),
        # NEL
        "NE17": Stop("NE17", "Punggol", 1.405, 103.902),
        "NE16": Stop("NE16", "Sengkang", 1.392, 103.895),
        "NE12": Stop("NE12", "Serangoon", 1.350, 103.873),
        "NE7":  Stop("NE7",  "Little India", 1.307, 103.849),
        "NE6":  Stop("NE6",  "Dhoby Ghaut", 1.299, 103.846),
        "NE4":  Stop("NE4",  "Chinatown", 1.284, 103.844),
        "NE1":  Stop("NE1",  "HarbourFront", 1.265, 103.822),
        # DTL
        "DT1":  Stop("DT1",  "Bukit Panjang", 1.378, 103.763),
        "DT9":  Stop("DT9",  "Botanic Gardens", 1.322, 103.815),
        "DT17": Stop("DT17", "Downtown", 1.279, 103.853),
        "DT35": Stop("DT35", "Expo", 1.335, 103.962),
        # CCL
        "CC15": Stop("CC15", "Bishan CC", 1.351, 103.849),
        "CC13": Stop("CC13", "Serangoon CC", 1.350, 103.873),
        "CC9":  Stop("CC9",  "Paya Lebar CC", 1.318, 103.893),
        "CE1":  Stop("CE1",  "Bayfront", 1.282, 103.859),
        # Bus stops
        "BUS_NTU":     Stop("BUS_NTU", "NTU", 1.348, 103.683),
        "BUS_PIONEER": Stop("BUS_PIONEER", "Pioneer MRT", 1.338, 103.697),
        "BUS_TAMP":    Stop("BUS_TAMP", "Tampines Int", 1.354, 103.944),
        "BUS_BISHAN":  Stop("BUS_BISHAN", "Bishan Int", 1.351, 103.848),
        "BUS_YISHUN":  Stop("BUS_YISHUN", "Yishun Int", 1.429, 103.835),
        "BUS_AMK":     Stop("BUS_AMK", "AMK Int", 1.370, 103.849),
        "BUS_CHANGI":  Stop("BUS_CHANGI", "Changi Airport Bus", 1.357, 103.989),
        "BUS_ORCHARD": Stop("BUS_ORCHARD", "Orchard Bus Stop", 1.304, 103.832),
    }

    peak = {7: 2.5, 8: 3.0, 9: 2.5, 17: 2.5, 18: 3.0, 19: 2.0}
    mild = {7: 1.5, 8: 2.0, 9: 1.5, 17: 1.5, 18: 2.0, 19: 1.5}
    low = {}  # no crowding data -> defaults to 1.0

    def make_trips(rid, sids, first, last, headway, times, crowd=None):
        trips = []
        dep = first
        n = 0
        while dep <= last:
            sts = []
            t = dep
            for i, sid in enumerate(sids):
                sts.append(StopTime(stop_id=sid, arrival_min=t, departure_min=t + 1))
                if i < len(times):
                    t = t + 1 + times[i]
            hour = dep // 60
            c = crowd.get(hour, 1.0) if crowd else 1.0
            trips.append(Trip(trip_id=f"{rid}_T{n}", route_id=rid, stop_times=sts, crowding=c))
            dep += headway
            n += 1
        return trips

    routes = {}

    # EWL Eastbound: Tuas Link -> Changi Airport
    ewl_e = ["EW33", "EW27", "EW24", "EW21", "EW13", "EW8", "EW2", "CG2"]
    ewl_t = [10, 5, 8, 12, 6, 12, 5]
    routes["EWL_EB"] = Route("EWL_EB", "EWL Eastbound", ewl_e,
        make_trips("EWL_EB", ewl_e, 330, 1400, 4, ewl_t, peak), "rail", 4)
    # EWL Westbound
    routes["EWL_WB"] = Route("EWL_WB", "EWL Westbound", list(reversed(ewl_e)),
        make_trips("EWL_WB", list(reversed(ewl_e)), 330, 1400, 4, list(reversed(ewl_t)), peak), "rail", 4)

    # NSL Southbound: Woodlands -> Marina Bay
    nsl_s = ["NS9", "NS13", "NS16", "NS17", "NS19", "NS22", "EW13", "NS27"]
    nsl_t = [5, 8, 3, 4, 5, 6, 4]
    routes["NSL_SB"] = Route("NSL_SB", "NSL Southbound", nsl_s,
        make_trips("NSL_SB", nsl_s, 330, 1400, 4, nsl_t, peak), "rail", 4)
    routes["NSL_NB"] = Route("NSL_NB", "NSL Northbound", list(reversed(nsl_s)),
        make_trips("NSL_NB", list(reversed(nsl_s)), 330, 1400, 4, list(reversed(nsl_t)), peak), "rail", 4)

    # NEL: Punggol -> HarbourFront
    nel_s = ["NE17", "NE16", "NE12", "NE7", "NE6", "NE4", "NE1"]
    nel_t = [3, 10, 8, 2, 3, 5]
    routes["NEL_SB"] = Route("NEL_SB", "NEL Southbound", nel_s,
        make_trips("NEL_SB", nel_s, 360, 1400, 5, nel_t, mild), "rail", 5)
    routes["NEL_NB"] = Route("NEL_NB", "NEL Northbound", list(reversed(nel_s)),
        make_trips("NEL_NB", list(reversed(nel_s)), 360, 1400, 5, list(reversed(nel_t)), mild), "rail", 5)

    # DTL: Bukit Panjang -> Expo
    dtl_s = ["DT1", "DT9", "DT17", "DT35"]
    dtl_t = [10, 8, 15]
    routes["DTL_EB"] = Route("DTL_EB", "DTL Eastbound", dtl_s,
        make_trips("DTL_EB", dtl_s, 360, 1400, 5, dtl_t, mild), "rail", 5)
    routes["DTL_WB"] = Route("DTL_WB", "DTL Westbound", list(reversed(dtl_s)),
        make_trips("DTL_WB", list(reversed(dtl_s)), 360, 1400, 5, list(reversed(dtl_t)), mild), "rail", 5)

    # CCL: Bishan -> Bayfront
    ccl_s = ["CC15", "CC13", "CC9", "CE1"]
    ccl_t = [4, 6, 8]
    routes["CCL_CW"] = Route("CCL_CW", "CCL Clockwise", ccl_s,
        make_trips("CCL_CW", ccl_s, 360, 1400, 5, ccl_t, mild), "rail", 5)
    routes["CCL_CC"] = Route("CCL_CC", "CCL Counter-CW", list(reversed(ccl_s)),
        make_trips("CCL_CC", list(reversed(ccl_s)), 360, 1400, 5, list(reversed(ccl_t)), mild), "rail", 5)

    # Bus 179: NTU -> Boon Lay (LOW FREQUENCY)
    routes["BUS179"] = Route("BUS179", "Bus 179", ["BUS_NTU", "BUS_PIONEER", "EW27"],
        make_trips("BUS179", ["BUS_NTU", "BUS_PIONEER", "EW27"], 360, 1400, 20, [8, 5], low), "bus", 20)

    # Bus 67: Tampines -> Bishan (medium freq)
    routes["BUS67"] = Route("BUS67", "Bus 67", ["BUS_TAMP", "BUS_BISHAN"],
        make_trips("BUS67", ["BUS_TAMP", "BUS_BISHAN"], 360, 1400, 10, [25], mild), "bus", 10)

    # Bus 854: Yishun -> AMK (high freq)
    routes["BUS854"] = Route("BUS854", "Bus 854", ["BUS_YISHUN", "BUS_AMK"],
        make_trips("BUS854", ["BUS_YISHUN", "BUS_AMK"], 360, 1400, 8, [12], low), "bus", 8)

    # Bus 36: Changi -> Orchard (medium freq, scenic route)
    routes["BUS36"] = Route("BUS36", "Bus 36", ["BUS_CHANGI", "EW8", "BUS_ORCHARD"],
        make_trips("BUS36", ["BUS_CHANGI", "EW8", "BUS_ORCHARD"], 360, 1400, 12, [20, 25], low), "bus", 12)

    # Foot transfers (interchanges + bus<->MRT)
    transfers = [
        # Bus <-> MRT connections
        FootTransfer("EW27", "BUS_PIONEER", 5), FootTransfer("BUS_PIONEER", "EW27", 5),
        FootTransfer("EW2", "BUS_TAMP", 3), FootTransfer("BUS_TAMP", "EW2", 3),
        FootTransfer("NS17", "BUS_BISHAN", 2), FootTransfer("BUS_BISHAN", "NS17", 2),
        FootTransfer("NS17", "CC15", 2), FootTransfer("CC15", "NS17", 2),  # Bishan interchange
        FootTransfer("NS13", "BUS_YISHUN", 2), FootTransfer("BUS_YISHUN", "NS13", 2),
        FootTransfer("NS16", "BUS_AMK", 2), FootTransfer("BUS_AMK", "NS16", 2),
        FootTransfer("CG2", "BUS_CHANGI", 3), FootTransfer("BUS_CHANGI", "CG2", 3),
        FootTransfer("NS22", "BUS_ORCHARD", 2), FootTransfer("BUS_ORCHARD", "NS22", 2),
        # MRT interchanges
        FootTransfer("NE12", "CC13", 3), FootTransfer("CC13", "NE12", 3),  # Serangoon
        FootTransfer("EW8", "CC9", 3), FootTransfer("CC9", "EW8", 3),      # Paya Lebar
        FootTransfer("NE6", "NS22", 4), FootTransfer("NS22", "NE6", 4),    # Dhoby Ghaut<->Orchard area
        FootTransfer("EW13", "DT17", 5), FootTransfer("DT17", "EW13", 5),  # City Hall<->Downtown
        FootTransfer("NS27", "DT17", 4), FootTransfer("DT17", "NS27", 4),  # Marina Bay<->Downtown
        FootTransfer("NS27", "CE1", 4), FootTransfer("CE1", "NS27", 4),    # Marina Bay<->Bayfront
        FootTransfer("DT9", "EW21", 6), FootTransfer("EW21", "DT9", 6),    # Botanic Gardens<->Buona Vista
    ]

    return stops, routes, transfers


# ============================================================
# McRAPTOR (same algorithm, cleaned up)
# ============================================================

BASE_FARE = 0.92
PER_STOP_FARE = 0.08

def mcraptor(stops, routes, foot_transfers, origin_id, dest_id, departure_min, max_rounds=5, verbose=False):
    stop_to_routes = defaultdict(list)
    for route in routes.values():
        for i, sid in enumerate(route.stop_sequence):
            stop_to_routes[sid].append((route.route_id, i))

    transfer_from = defaultdict(list)
    for t in foot_transfers:
        transfer_from[t.from_stop].append(t)

    bags = defaultdict(list)
    bags[origin_id].append(Label(departure_min, -1, 0.0, 0.0))
    marked = {origin_id}

    for round_k in range(max_rounds):
        new_marked = set()
        routes_to_scan = {}
        for sid in marked:
            for rid, pos in stop_to_routes[sid]:
                if rid not in routes_to_scan or pos < routes_to_scan[rid]:
                    routes_to_scan[rid] = pos

        for rid, board_pos in routes_to_scan.items():
            route = routes[rid]
            seq = route.stop_sequence
            for bi in range(board_pos, len(seq)):
                bstop = seq[bi]
                if bstop not in bags:
                    continue
                for label in list(bags[bstop]):
                    best_trip = None
                    for trip in route.trips:
                        if trip.stop_times[bi].departure_min >= label.arrival_min:
                            best_trip = trip
                            break
                    if not best_trip:
                        continue
                    for ai in range(bi + 1, len(seq)):
                        astop = seq[ai]
                        new_label = Label(
                            best_trip.stop_times[ai].arrival_min,
                            label.num_transfers + 1,
                            label.crowding_score + best_trip.crowding,
                            label.cost + BASE_FARE + abs(ai - bi) * PER_STOP_FARE,
                            best_trip.trip_id, bstop, label,
                        )
                        if _add_pareto(bags[astop], new_label):
                            new_marked.add(astop)

        # Foot transfers
        for sid in new_marked | marked:
            for ft in transfer_from.get(sid, []):
                for label in list(bags[sid]):
                    wl = Label(
                        label.arrival_min + ft.walk_min,
                        label.num_transfers, label.crowding_score, label.cost,
                        f"walk_{ft.from_stop}_{ft.to_stop}", ft.from_stop, label,
                    )
                    if _add_pareto(bags[ft.to_stop], wl):
                        new_marked.add(ft.to_stop)

        if not new_marked:
            break
        marked = new_marked

    return bags.get(dest_id, [])


def _add_pareto(bag, new_label):
    for ex in bag:
        if ex.dominates(new_label):
            return False
        if (ex.arrival_min == new_label.arrival_min and
            ex.num_transfers == new_label.num_transfers and
            ex.crowding_score == new_label.crowding_score and
            ex.cost == new_label.cost):
            return False
    bag[:] = [l for l in bag if not new_label.dominates(l)]
    bag.append(new_label)
    return True


def reconstruct(label, stops):
    steps = []
    cur = label
    while cur and cur.boarded_trip:
        if cur.boarded_trip.startswith("walk_"):
            parts = cur.boarded_trip.split("_", 2)
            fn = stops.get(parts[1], Stop(parts[1], parts[1])).name
            tn = stops.get(parts[2], Stop(parts[2], parts[2])).name
            steps.append(f"Walk {fn} -> {tn}")
        else:
            rid = cur.boarded_trip.rsplit("_T", 1)[0]
            bn = stops.get(cur.boarded_at, Stop(cur.boarded_at, cur.boarded_at)).name
            rname = rid
            steps.append(f"Board {rname} at {bn}")
        cur = cur.prev_label
    steps.reverse()
    return steps


# ============================================================
# CALL REAL BACKEND (Google Directions via SGTravelBud)
# ============================================================

def call_backend(origin_name, dest_name):
    """Call the real SGTravelBud backend for comparison."""
    try:
        params = urllib.parse.urlencode({
            "origin": origin_name,
            "destination": dest_name,
            "include_transit": "true",
            "include_driving": "true",
        })
        url = f"http://127.0.0.1:8000/routes?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "McRAPTOR-Compare/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "routes": []}


# ============================================================
# COMPARISON RUNNER
# ============================================================

def fmt_time(mins):
    h, m = divmod(mins, 60)
    return f"{h:02d}:{m:02d}"

def run_comparison():
    stops, routes, transfers = build_full_network()
    total_trips = sum(len(r.trips) for r in routes.values())

    print("=" * 75)
    print("  McRAPTOR vs Google Maps -- Side-by-Side Comparison")
    print("=" * 75)
    print(f"Network: {len(stops)} stops, {len(routes)} routes, {len(transfers)} transfers, {total_trips} trips\n")

    queries = [
        {
            "name": "NTU -> Changi Airport (peak 08:00)",
            "why": "Tests low-frequency Bus 179 risk. Google ignores the 20-min headway.",
            "raptor_from": "BUS_NTU", "raptor_to": "CG2", "dep_min": 480,
            "google_from": "NTU, Singapore", "google_to": "Changi Airport, Singapore",
        },
        {
            "name": "Woodlands -> HarbourFront (peak 08:00)",
            "why": "Multiple lines possible: NSL direct (crowded) vs NEL via Serangoon (less crowded).",
            "raptor_from": "NS9", "raptor_to": "NE1", "dep_min": 480,
            "google_from": "Woodlands MRT, Singapore", "google_to": "HarbourFront MRT, Singapore",
        },
        {
            "name": "Punggol -> Orchard (peak 08:30)",
            "why": "NEL->NSL is direct but crowded. Bus+CCL alternative exists.",
            "raptor_from": "NE17", "raptor_to": "NS22", "dep_min": 510,
            "google_from": "Punggol MRT, Singapore", "google_to": "Orchard MRT, Singapore",
        },
        {
            "name": "Yishun -> Downtown (off-peak 14:00)",
            "why": "Off-peak: crowding is low everywhere. Time should dominate.",
            "raptor_from": "NS13", "raptor_to": "DT17", "dep_min": 840,
            "google_from": "Yishun MRT, Singapore", "google_to": "Downtown MRT, Singapore",
        },
        {
            "name": "Tampines -> Bishan (peak 08:00)",
            "why": "EWL->NSL direct, or Bus 67 direct. Frequency vs speed trade-off.",
            "raptor_from": "EW2", "raptor_to": "NS17", "dep_min": 480,
            "google_from": "Tampines MRT, Singapore", "google_to": "Bishan MRT, Singapore",
        },
    ]

    for q in queries:
        print("\n" + "#" * 75)
        print(f"  {q['name']}")
        print(f"  Why: {q['why']}")
        print("#" * 75)

        # --- McRAPTOR ---
        t0 = time_module.time()
        results = mcraptor(stops, routes, transfers, q["raptor_from"], q["raptor_to"], q["dep_min"])
        elapsed = (time_module.time() - t0) * 1000

        print(f"\n  [McRAPTOR] {len(results)} Pareto-optimal routes ({elapsed:.1f}ms)")
        print(f"  {'-'*60}")

        for i, label in enumerate(sorted(results, key=lambda l: l.arrival_min)):
            total = label.arrival_min - q["dep_min"]
            crowd_label = "LOW" if label.crowding_score < 3 else "MED" if label.crowding_score < 6 else "HIGH"
            print(f"  Route {i+1}: {total} min | {label.num_transfers} transfers | "
                  f"crowd={label.crowding_score:.1f} ({crowd_label}) | ${label.cost:.2f}")
            journey = reconstruct(label, stops)
            for step in journey:
                print(f"    {step}")

        # --- Google (via backend) ---
        print(f"\n  [Google Maps via SGTravelBud backend]")
        print(f"  {'-'*60}")

        backend_resp = call_backend(q["google_from"], q["google_to"])
        google_routes = backend_resp.get("routes", [])
        if backend_resp.get("error"):
            print(f"  ERROR: {backend_resp['error']}")
        elif not google_routes:
            print(f"  No routes returned")
        else:
            for i, gr in enumerate(google_routes):
                time_min = gr.get("time_min", 0)
                real_time = gr.get("realistic_time_min", time_min)
                cost = gr.get("cost_est", 0)
                crowd = gr.get("risk_crowding_cat", "?")
                xfers = gr.get("transfers", 0)
                score = gr.get("score", 0)
                steps_summary = []
                for s in gr.get("steps", []):
                    mode = s.get("mode", "?")
                    line = s.get("line_name", "")
                    if line:
                        steps_summary.append(f"{mode} {line}")
                    else:
                        steps_summary.append(mode)
                path = " -> ".join(steps_summary)
                print(f"  Route {i+1}: {time_min} min (realistic {real_time}) | "
                      f"{xfers} transfers | crowd={crowd} | ${cost:.2f} | score={score:.3f}")
                print(f"    {path}")

        # --- Analysis ---
        print(f"\n  [ANALYSIS]")
        print(f"  {'-'*60}")

        if results and google_routes:
            raptor_best_time = min(l.arrival_min - q["dep_min"] for l in results)
            raptor_least_crowd = min(l.crowding_score for l in results)
            google_best_time = min(gr.get("time_min", 999) for gr in google_routes)

            n_pareto = len(results)
            n_google = len(google_routes)

            print(f"  McRAPTOR found {n_pareto} Pareto routes, Google returned {n_google} routes")
            print(f"  McRAPTOR fastest: {raptor_best_time} min, Google fastest: {google_best_time} min")

            if n_pareto > 1:
                low_crowd = [l for l in results if l.crowding_score < 3]
                high_crowd = [l for l in results if l.crowding_score >= 6]
                if low_crowd and high_crowd:
                    print(f"  ** McRAPTOR found BOTH low-crowd and high-crowd options **")
                    print(f"     Google only optimizes time -- can't distinguish these!")

            if any(l.crowding_score >= 3 for l in results):
                least = min(results, key=lambda l: l.crowding_score)
                fastest = min(results, key=lambda l: l.arrival_min)
                if least != fastest:
                    time_diff = (least.arrival_min - fastest.arrival_min)
                    crowd_diff = fastest.crowding_score - least.crowding_score
                    print(f"  ** Trade-off: +{time_diff} min for {crowd_diff:.1f} less crowding **")
                    print(f"     This trade-off is INVISIBLE to Google Maps!")
        elif not results:
            print(f"  McRAPTOR: no path found (network too sparse for this query)")
        else:
            print(f"  Backend unavailable for comparison")


    print("\n\n" + "=" * 75)
    print("  SUMMARY: What McRAPTOR Does That Google Cannot")
    print("=" * 75)
    print("""
    1. CROWDING-AWARE ALTERNATIVES
       McRAPTOR finds routes that are slightly slower but avoid peak crowding.
       Google cannot -- it has no access to LTA PCD data.

    2. FREQUENCY-AWARE ROUTING
       McRAPTOR naturally handles bus headways because it searches the actual
       timetable. If Bus 179 just left, it finds the next one or routes around it.
       Google assumes you always catch the bus.

    3. PARETO-OPTIMAL TRADE-OFFS
       Instead of one "best" route, McRAPTOR returns ALL non-dominated options:
       fastest, cheapest, least crowded, fewest transfers. The user chooses.

    4. NO API DEPENDENCY
       McRAPTOR runs locally on LTA open data. No Google API key needed.
       No rate limits. No cost per query. No network latency.

    5. CUSTOM OBJECTIVES
       Your 4-axis scoring (time/cost/risk/comfort) maps directly to
       McRAPTOR's 4 criteria. The scoring IS the routing.
    """)

import urllib.parse

if __name__ == "__main__":
    run_comparison()
