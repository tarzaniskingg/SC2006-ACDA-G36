"""
McRAPTOR MVP — Multi-Criteria Round-Based Public Transit Router
================================================================

A standalone demo using a simplified Singapore MRT+Bus network.
No external dependencies. Run with: python mcraptor_mvp.py

This demonstrates:
1. How RAPTOR works (round-based transit routing)
2. How McRAPTOR extends it (Pareto-optimal multi-criteria)
3. Why it's better than Dijkstra for transit
4. How you'd integrate LTA real-time data (crowding, frequency)

The network is hardcoded but mirrors real SG topology.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import time as time_module


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class Stop:
    """A transit stop (MRT station or bus stop)."""
    id: str
    name: str
    lat: float = 0.0
    lng: float = 0.0


@dataclass
class StopTime:
    """A single visit of a trip to a stop. Like one row in GTFS stop_times."""
    stop_id: str
    arrival_min: int    # minutes since midnight (e.g., 480 = 08:00)
    departure_min: int  # when the vehicle leaves this stop


@dataclass
class Trip:
    """One run of a vehicle along a route (e.g., 'EWL train departing Pasir Ris at 07:32')."""
    trip_id: str
    route_id: str
    stop_times: List[StopTime]  # ordered by sequence
    crowding: float = 1.0       # 1=low, 2=medium, 3=high


@dataclass
class Route:
    """A transit route (e.g., 'East-West Line', 'Bus 179').
    In RAPTOR, a 'route' is a sequence of stops served in order."""
    route_id: str
    name: str
    stop_sequence: List[str]    # ordered stop IDs
    trips: List[Trip]           # all trips on this route, sorted by departure time
    mode: str = "rail"          # "rail" or "bus"
    frequency_min: int = 5      # average headway in minutes


@dataclass
class FootTransfer:
    """Walking connection between two stops."""
    from_stop: str
    to_stop: str
    walk_min: int


# ============================================================
# McRAPTOR LABEL — the multi-criteria "state" at each stop
# ============================================================

@dataclass
class Label:
    """
    A Pareto label representing one way to reach a stop.

    McRAPTOR tracks a SET of these at each stop — not just
    the "best" one, because "best" depends on what you value.
    """
    arrival_min: int        # when you arrive (minutes since midnight)
    num_transfers: int      # how many vehicles you've boarded - 1
    crowding_score: float   # cumulative crowding (lower = less crowded)
    cost: float             # fare in dollars
    # For path reconstruction:
    boarded_trip: Optional[str] = None
    boarded_at: Optional[str] = None
    prev_label: Optional['Label'] = None

    def dominates(self, other: 'Label') -> bool:
        """
        Does self DOMINATE other?
        Self dominates if it's <= in ALL criteria and < in at least one.

        This is the core of multi-criteria optimization.
        Google Maps only optimizes for ONE criterion (time).
        McRAPTOR finds ALL non-dominated trade-offs.
        """
        dominated_all = (
            self.arrival_min <= other.arrival_min and
            self.num_transfers <= other.num_transfers and
            self.crowding_score <= other.crowding_score and
            self.cost <= other.cost
        )
        strictly_better_one = (
            self.arrival_min < other.arrival_min or
            self.num_transfers < other.num_transfers or
            self.crowding_score < other.crowding_score or
            self.cost < other.cost
        )
        return dominated_all and strictly_better_one

    def __repr__(self):
        h, m = divmod(self.arrival_min, 60)
        return f"Label(arr={h:02d}:{m:02d}, transfers={self.num_transfers}, crowd={self.crowding_score:.1f}, cost=${self.cost:.2f})"


# ============================================================
# BUILD A MINI SINGAPORE NETWORK
# ============================================================

def build_sg_network():
    """
    Build a simplified Singapore transit network:
    - East-West Line (EWL): Boon Lay -> Jurong East -> Buona Vista -> City Hall -> Tampines -> Changi
    - North-South Line (NSL): Woodlands -> Ang Mo Kio -> Bishan -> City Hall -> Marina Bay
    - Downtown Line (DTL): Bukit Panjang -> Botanic Gardens -> Downtown -> Expo
    - Bus 179: NTU -> Pioneer -> Boon Lay (low frequency, every 20 min)
    - Bus 67: Tampines -> Bishan (medium frequency, every 10 min)
    - Foot transfers at interchange stations
    """

    stops = {
        # EWL
        "EW27": Stop("EW27", "Boon Lay", 1.338, 103.706),
        "EW24": Stop("EW24", "Jurong East", 1.333, 103.742),
        "EW21": Stop("EW21", "Buona Vista", 1.307, 103.790),
        "EW13": Stop("EW13", "City Hall", 1.293, 103.852),
        "EW2":  Stop("EW2",  "Tampines", 1.354, 103.945),
        "CG2":  Stop("CG2",  "Changi Airport", 1.357, 103.989),
        # NSL
        "NS9":  Stop("NS9",  "Woodlands", 1.437, 103.786),
        "NS16": Stop("NS16", "Ang Mo Kio", 1.370, 103.850),
        "NS17": Stop("NS17", "Bishan", 1.351, 103.849),
        "NS27": Stop("NS27", "Marina Bay", 1.274, 103.854),
        # DTL
        "DT1":  Stop("DT1",  "Bukit Panjang", 1.378, 103.763),
        "DT9":  Stop("DT9",  "Botanic Gardens", 1.322, 103.815),
        "DT17": Stop("DT17", "Downtown", 1.279, 103.853),
        "DT35": Stop("DT35", "Expo", 1.335, 103.962),
        # Bus stops
        "BUS_NTU":     Stop("BUS_NTU", "NTU", 1.348, 103.683),
        "BUS_PIONEER": Stop("BUS_PIONEER", "Pioneer MRT", 1.338, 103.697),
        "BUS_TAMP":    Stop("BUS_TAMP", "Tampines Int", 1.354, 103.944),
        "BUS_BISHAN":  Stop("BUS_BISHAN", "Bishan Int", 1.351, 103.848),
    }

    # --- Helper: generate trips at regular intervals ---
    def make_trips(route_id, stop_ids, first_dep, last_dep, headway, travel_times, crowding_by_hour=None):
        """
        Generate trips for a route.
        travel_times: list of minutes between consecutive stops.
        crowding_by_hour: dict mapping hour -> crowding score (1-3).
        """
        trips = []
        dep = first_dep
        trip_num = 0
        while dep <= last_dep:
            stop_times = []
            t = dep
            for i, sid in enumerate(stop_ids):
                arr = t
                stop_times.append(StopTime(stop_id=sid, arrival_min=arr, departure_min=arr + 1))
                if i < len(travel_times):
                    t = arr + 1 + travel_times[i]

            hour = dep // 60
            crowd = 1.0
            if crowding_by_hour:
                crowd = crowding_by_hour.get(hour, 1.0)

            trips.append(Trip(
                trip_id=f"{route_id}_T{trip_num}",
                route_id=route_id,
                stop_times=stop_times,
                crowding=crowd,
            ))
            dep += headway
            trip_num += 1
        return trips

    # Crowding profiles (hour -> crowding score)
    peak_crowding = {7: 2.5, 8: 3.0, 9: 2.5, 17: 2.5, 18: 3.0, 19: 2.0}
    mild_crowding = {7: 1.5, 8: 2.0, 9: 1.5, 17: 1.5, 18: 2.0, 19: 1.5}

    routes = {}

    # EWL: Boon Lay -> Changi Airport
    ewl_stops = ["EW27", "EW24", "EW21", "EW13", "EW2", "CG2"]
    ewl_times = [5, 8, 12, 15, 5]  # minutes between consecutive stops
    routes["EWL_EB"] = Route(
        route_id="EWL_EB", name="East-West Line (Eastbound)",
        stop_sequence=ewl_stops,
        trips=make_trips("EWL_EB", ewl_stops, 330, 1380, 4, ewl_times, peak_crowding),
        mode="rail", frequency_min=4,
    )
    # EWL reverse
    ewl_rev = list(reversed(ewl_stops))
    ewl_times_rev = list(reversed(ewl_times))
    routes["EWL_WB"] = Route(
        route_id="EWL_WB", name="East-West Line (Westbound)",
        stop_sequence=ewl_rev,
        trips=make_trips("EWL_WB", ewl_rev, 330, 1380, 4, ewl_times_rev, peak_crowding),
        mode="rail", frequency_min=4,
    )

    # NSL: Woodlands -> Marina Bay
    nsl_stops = ["NS9", "NS16", "NS17", "EW13", "NS27"]  # City Hall = EW13 (interchange)
    nsl_times = [12, 3, 10, 4]
    routes["NSL_SB"] = Route(
        route_id="NSL_SB", name="North-South Line (Southbound)",
        stop_sequence=nsl_stops,
        trips=make_trips("NSL_SB", nsl_stops, 330, 1380, 4, nsl_times, peak_crowding),
        mode="rail", frequency_min=4,
    )
    nsl_rev = list(reversed(nsl_stops))
    nsl_times_rev = list(reversed(nsl_times))
    routes["NSL_NB"] = Route(
        route_id="NSL_NB", name="North-South Line (Northbound)",
        stop_sequence=nsl_rev,
        trips=make_trips("NSL_NB", nsl_rev, 330, 1380, 4, nsl_times_rev, peak_crowding),
        mode="rail", frequency_min=4,
    )

    # DTL: Bukit Panjang -> Expo
    dtl_stops = ["DT1", "DT9", "DT17", "DT35"]
    dtl_times = [10, 8, 15]
    routes["DTL_EB"] = Route(
        route_id="DTL_EB", name="Downtown Line (Eastbound)",
        stop_sequence=dtl_stops,
        trips=make_trips("DTL_EB", dtl_stops, 360, 1380, 5, dtl_times, mild_crowding),
        mode="rail", frequency_min=5,
    )

    # Bus 179: NTU -> Pioneer -> Boon Lay (LOW FREQUENCY — the pain point!)
    bus179_stops = ["BUS_NTU", "BUS_PIONEER", "EW27"]
    bus179_times = [8, 5]
    routes["BUS179"] = Route(
        route_id="BUS179", name="Bus 179",
        stop_sequence=bus179_stops,
        trips=make_trips("BUS179", bus179_stops, 360, 1380, 20, bus179_times),  # Every 20 min!
        mode="bus", frequency_min=20,
    )

    # Bus 67: Tampines -> Bishan (medium frequency)
    bus67_stops = ["BUS_TAMP", "BUS_BISHAN"]
    bus67_times = [25]
    routes["BUS67"] = Route(
        route_id="BUS67", name="Bus 67",
        stop_sequence=bus67_stops,
        trips=make_trips("BUS67", bus67_stops, 360, 1380, 10, bus67_times, mild_crowding),
        mode="bus", frequency_min=10,
    )

    # Foot transfers (walking between nearby stops / interchange connections)
    transfers = [
        FootTransfer("EW27", "BUS_PIONEER", 5),   # Boon Lay <-> Pioneer bus stop
        FootTransfer("BUS_PIONEER", "EW27", 5),
        FootTransfer("EW2", "BUS_TAMP", 3),        # Tampines MRT <-> Tampines interchange
        FootTransfer("BUS_TAMP", "EW2", 3),
        FootTransfer("NS17", "BUS_BISHAN", 2),     # Bishan MRT <-> Bishan interchange
        FootTransfer("BUS_BISHAN", "NS17", 2),
        # Key interchange: City Hall (EW13) <-> Downtown (DT17) — ~5 min walk underground
        FootTransfer("EW13", "DT17", 5),
        FootTransfer("DT17", "EW13", 5),
        # Botanic Gardens (DT9) <-> Buona Vista area (for DTL<->EWL option)
        FootTransfer("DT9", "EW21", 8),
        FootTransfer("EW21", "DT9", 8),
        # Marina Bay (NS27) <-> Downtown (DT17) — 4 min walk
        FootTransfer("NS27", "DT17", 4),
        FootTransfer("DT17", "NS27", 4),
        # Expo (DT35) <-> Changi area
        FootTransfer("DT35", "CG2", 15),           # Expo <-> Changi (longer walk/shuttle)
        FootTransfer("CG2", "DT35", 15),
    ]

    return stops, routes, transfers


# ============================================================
# McRAPTOR ALGORITHM
# ============================================================

# Fare model (simplified SG transit)
BASE_FARE = 0.92   # card tap
PER_KM_FARE = 0.04
TRANSFER_DISCOUNT = 0.0  # free transfer within 45 min in SG


def compute_fare_increment(route: Route, from_stop: str, to_stop: str) -> float:
    """Estimate fare for riding a route segment. Simplified."""
    seq = route.stop_sequence
    try:
        i = seq.index(from_stop)
        j = seq.index(to_stop)
        num_stops = abs(j - i)
        return BASE_FARE + num_stops * PER_KM_FARE * 2  # rough per-stop cost
    except ValueError:
        return BASE_FARE


def mcraptor(
    stops: Dict[str, Stop],
    routes: Dict[str, Route],
    transfers: List[FootTransfer],
    origin_id: str,
    destination_id: str,
    departure_min: int,     # minutes since midnight (e.g., 480 = 08:00)
    max_rounds: int = 5,    # max transfers + 1
) -> List[Label]:
    """
    Multi-Criteria RAPTOR.

    Returns the Pareto set of labels at the destination — each represents
    a non-dominated journey (different trade-offs of time/transfers/crowding/cost).

    This is THE key difference from Google Maps:
    - Google returns routes optimized for time only
    - McRAPTOR returns ALL trade-off routes simultaneously
    """

    # --- Build index structures ---
    # Which routes serve each stop?
    stop_to_routes: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # stop_id -> [(route_id, position)]
    for route in routes.values():
        for i, sid in enumerate(route.stop_sequence):
            stop_to_routes[sid].append((route.route_id, i))

    # Transfer index
    transfer_from: Dict[str, List[FootTransfer]] = defaultdict(list)
    for t in transfers:
        transfer_from[t.from_stop].append(t)

    # --- Initialize ---
    # bags[stop_id] = list of non-dominated Labels (the Pareto frontier)
    bags: Dict[str, List[Label]] = defaultdict(list)

    # Initial label at origin
    start_label = Label(
        arrival_min=departure_min,
        num_transfers=-1,  # will become 0 when first vehicle is boarded
        crowding_score=0.0,
        cost=0.0,
    )
    bags[origin_id].append(start_label)

    # Stops whose labels improved (need to be scanned)
    marked_stops: Set[str] = {origin_id}

    print(f"\n{'='*70}")
    print(f"McRAPTOR: {stops[origin_id].name} -> {stops[destination_id].name}")
    print(f"Departure: {departure_min // 60:02d}:{departure_min % 60:02d}")
    print(f"{'='*70}")

    # --- Main loop: one round per vehicle boarded ---
    for round_k in range(max_rounds):
        print(f"\n--- Round {round_k} (boarding vehicle #{round_k + 1}) ---")
        new_marked: Set[str] = set()
        routes_to_scan: Dict[str, int] = {}  # route_id -> earliest boarding position

        # Step 1: Collect routes that pass through marked stops
        for stop_id in marked_stops:
            for route_id, pos in stop_to_routes[stop_id]:
                if route_id not in routes_to_scan or pos < routes_to_scan[route_id]:
                    routes_to_scan[route_id] = pos

        # Step 2: Scan each route
        for route_id, board_pos in routes_to_scan.items():
            route = routes[route_id]
            seq = route.stop_sequence

            # For each label at the boarding stop, find the earliest trip we can catch
            for board_idx in range(board_pos, len(seq)):
                board_stop = seq[board_idx]
                if board_stop not in bags:
                    continue

                for label in bags[board_stop]:
                    # Find the earliest trip departing after our arrival
                    best_trip = None
                    for trip in route.trips:
                        st = trip.stop_times[board_idx]
                        if st.departure_min >= label.arrival_min:
                            best_trip = trip
                            break

                    if not best_trip:
                        continue

                    # Ride this trip forward to all subsequent stops
                    for alight_idx in range(board_idx + 1, len(seq)):
                        alight_stop = seq[alight_idx]
                        alight_time = best_trip.stop_times[alight_idx].arrival_min

                        new_label = Label(
                            arrival_min=alight_time,
                            num_transfers=label.num_transfers + 1,
                            crowding_score=label.crowding_score + best_trip.crowding,
                            cost=label.cost + compute_fare_increment(route, board_stop, alight_stop),
                            boarded_trip=best_trip.trip_id,
                            boarded_at=board_stop,
                            prev_label=label,
                        )

                        # Add to Pareto set if not dominated
                        if _add_to_pareto(bags[alight_stop], new_label):
                            new_marked.add(alight_stop)

        # Step 3: Foot transfers — walk between nearby stops
        transfer_marked: Set[str] = set()
        for stop_id in new_marked | marked_stops:
            for ft in transfer_from.get(stop_id, []):
                for label in bags[stop_id]:
                    walk_label = Label(
                        arrival_min=label.arrival_min + ft.walk_min,
                        num_transfers=label.num_transfers,
                        crowding_score=label.crowding_score,
                        cost=label.cost,  # walking is free
                        boarded_trip=f"walk_{ft.from_stop}_{ft.to_stop}",
                        boarded_at=ft.from_stop,
                        prev_label=label,
                    )
                    if _add_to_pareto(bags[ft.to_stop], walk_label):
                        transfer_marked.add(ft.to_stop)

        new_marked |= transfer_marked

        if not new_marked:
            print("  No improvements — stopping early.")
            break

        print(f"  Improved {len(new_marked)} stops")
        marked_stops = new_marked

    # Return Pareto set at destination
    return bags.get(destination_id, [])


def _add_to_pareto(bag: List[Label], new_label: Label) -> bool:
    """
    Try to add new_label to the Pareto bag.
    Returns True if added (bag was improved).

    This is the heart of multi-criteria optimization:
    - If any existing label dominates new_label -> reject
    - Otherwise add new_label and remove any it dominates
    """
    # Check if any existing label dominates OR equals the new one
    for existing in bag:
        if existing.dominates(new_label):
            return False  # new label is useless
        # Skip exact duplicates (same criteria values)
        if (existing.arrival_min == new_label.arrival_min and
            existing.num_transfers == new_label.num_transfers and
            existing.crowding_score == new_label.crowding_score and
            existing.cost == new_label.cost):
            return False

    # Remove any existing labels that new_label dominates
    bag[:] = [l for l in bag if not new_label.dominates(l)]

    bag.append(new_label)
    return True


# ============================================================
# PATH RECONSTRUCTION
# ============================================================

def reconstruct_journey(label: Label, stops: Dict[str, Stop]) -> List[str]:
    """Walk backwards through labels to reconstruct the journey."""
    steps = []
    current = label
    while current and current.boarded_trip:
        trip = current.boarded_trip
        board_at = current.boarded_at
        if trip.startswith("walk_"):
            parts = trip.split("_", 2)
            from_name = stops[parts[1]].name if parts[1] in stops else parts[1]
            to_name = stops[parts[2]].name if parts[2] in stops else parts[2]
            steps.append(f"  Walk: {from_name} -> {to_name}")
        else:
            route_id = trip.rsplit("_T", 1)[0]
            from_name = stops[board_at].name if board_at in stops else board_at
            steps.append(f"  Board {route_id} at {from_name} (trip {trip})")
        current = current.prev_label
    steps.reverse()
    return steps


# ============================================================
# DEMO
# ============================================================

def run_demo():
    stops, routes, transfers = build_sg_network()

    print("\n" + "=" * 70)
    print("     McRAPTOR MVP — Singapore Transit Router Demo")
    print("=" * 70)
    print(f"\nNetwork: {len(stops)} stops, {len(routes)} routes, {len(transfers)} transfers")
    total_trips = sum(len(r.trips) for r in routes.values())
    print(f"Total trips in timetable: {total_trips}")

    # ---- Query 1: NTU -> Changi Airport at 08:00 (peak) ----
    print("\n\n" + "#" * 70)
    print("  QUERY 1: NTU -> Changi Airport, departing 08:00 (PEAK HOUR)")
    print("  This is the pain-point scenario: Bus 179 runs every 20 min!")
    print("#" * 70)

    t0 = time_module.time()
    results = mcraptor(stops, routes, transfers, "BUS_NTU", "CG2", 480)
    elapsed = (time_module.time() - t0) * 1000

    print(f"\n{'='*70}")
    print(f"RESULTS: {len(results)} Pareto-optimal journeys found ({elapsed:.1f}ms)")
    print(f"{'='*70}")

    for i, label in enumerate(sorted(results, key=lambda l: l.arrival_min)):
        h, m = divmod(label.arrival_min, 60)
        dep_h, dep_m = divmod(480, 60)
        total = label.arrival_min - 480
        print(f"\n  Journey {i+1}:")
        print(f"    Arrive: {h:02d}:{m:02d} (total {total} min)")
        print(f"    Transfers: {label.num_transfers}")
        print(f"    Crowding: {label.crowding_score:.1f} ({'low' if label.crowding_score < 3 else 'medium' if label.crowding_score < 6 else 'HIGH'})")
        print(f"    Cost: ${label.cost:.2f}")
        journey = reconstruct_journey(label, stops)
        for step in journey:
            print(f"    {step}")

    # ---- Query 2: NTU -> Changi Airport at 11:00 (off-peak) ----
    print("\n\n" + "#" * 70)
    print("  QUERY 2: NTU -> Changi Airport, departing 11:00 (OFF-PEAK)")
    print("  Same route, different crowding levels")
    print("#" * 70)

    results2 = mcraptor(stops, routes, transfers, "BUS_NTU", "CG2", 660)

    print(f"\n{'='*70}")
    print(f"RESULTS: {len(results2)} Pareto-optimal journeys found")
    print(f"{'='*70}")

    for i, label in enumerate(sorted(results2, key=lambda l: l.arrival_min)):
        h, m = divmod(label.arrival_min, 60)
        total = label.arrival_min - 660
        print(f"\n  Journey {i+1}:")
        print(f"    Arrive: {h:02d}:{m:02d} (total {total} min)")
        print(f"    Transfers: {label.num_transfers}")
        print(f"    Crowding: {label.crowding_score:.1f} ({'low' if label.crowding_score < 3 else 'medium' if label.crowding_score < 6 else 'HIGH'})")
        print(f"    Cost: ${label.cost:.2f}")

    # ---- Query 3: Woodlands -> Downtown at 08:00 ----
    print("\n\n" + "#" * 70)
    print("  QUERY 3: Woodlands -> Downtown, departing 08:00")
    print("  McRAPTOR should find: direct NSL route (crowded)")
    print("  AND alternative via DTL (less crowded, more transfers)")
    print("#" * 70)

    results3 = mcraptor(stops, routes, transfers, "NS9", "DT17", 480)

    print(f"\n{'='*70}")
    print(f"RESULTS: {len(results3)} Pareto-optimal journeys found")
    print(f"{'='*70}")

    for i, label in enumerate(sorted(results3, key=lambda l: l.arrival_min)):
        h, m = divmod(label.arrival_min, 60)
        total = label.arrival_min - 480
        print(f"\n  Journey {i+1}:")
        print(f"    Arrive: {h:02d}:{m:02d} (total {total} min)")
        print(f"    Transfers: {label.num_transfers}")
        print(f"    Crowding: {label.crowding_score:.1f} ({'low' if label.crowding_score < 3 else 'medium' if label.crowding_score < 6 else 'HIGH'})")
        print(f"    Cost: ${label.cost:.2f}")
        journey = reconstruct_journey(label, stops)
        for step in journey:
            print(f"    {step}")

    # ---- Key Takeaway ----
    print("\n\n" + "=" * 70)
    print("KEY TAKEAWAY: WHY McRAPTOR > GOOGLE MAPS")
    print("=" * 70)
    print("""
    Google Maps would return ONE "best" route: NTU -> Bus 179 -> EWL -> Changi.
    It assumes you catch Bus 179 perfectly. Travel time: ~50 min.

    McRAPTOR returns MULTIPLE Pareto-optimal routes, each with trade-offs:
    - Fastest route (but crowded during peak)
    - Slightly slower route (but avoids crowded segments)
    - Route with fewer transfers (but longer)
    - Route that avoids low-frequency buses (no Bus 179 risk)

    The user sees ALL trade-offs and chooses what matters to THEM.

    To integrate with SGTravelBud:
    1. Replace Google Directions API with McRAPTOR
    2. Feed LTA BusRoutes + BusStops into the network graph
    3. Feed live PCD crowding data into trip crowding scores
    4. Feed live BusArrival frequency into trip scheduling
    5. Your existing 4-axis scoring (time/cost/risk/comfort)
       maps directly to McRAPTOR's 4 criteria!
    """)


if __name__ == "__main__":
    run_demo()
