# Appendix C: Test Cases
## SGTravelBud — ACDA-G36 | 14 April 2026

---

## Table of Contents
1. [Test Case Overview](#1-test-case-overview)
2. [Demo Workflows](#2-demo-workflows)
3. [Black Box Testing](#3-black-box-testing)
   - [3.1 Route Search and Input Validation](#31-route-search-and-input-validation)
   - [3.2 Preferences, Constraints and Ranking](#32-preferences-constraints-and-ranking)
   - [3.3 Results, Comparison and Map Display](#33-results-comparison-and-map-display)
   - [3.4 Driving / Taxi Features](#34-driving--taxi-features)
   - [3.5 Settings, Data Freshness and Fallback](#35-settings-data-freshness-and-fallback)
4. [White Box Testing](#4-white-box-testing)
   - [4.1 Overview and Class Under Test](#41-overview-and-class-under-test)
   - [4.2 Equivalence Class + Boundary Value Analysis](#42-equivalence-class--boundary-value-analysis)
   - [4.3 Basis Path Testing](#43-basis-path-testing)
   - [4.4 Test Case Minimisation](#44-test-case-minimisation)
   - [4.5 White Box Execution Results](#45-white-box-execution-results)
5. [Full Execution Summary](#5-full-execution-summary)

---

## 1. Test Case Overview

### Numbering Convention

| Prefix | Meaning | Count |
|--------|---------|-------|
| BB-TC | Black Box Test Case (UI/system level) | 21 |
| WB-TC | White Box Test Case (code/unit level) | 91 (50 original + 41 gap coverage) |

### FR Traceability Matrix

| FR | Description | BB-TC | WB-TC |
|----|-------------|-------|-------|
| FR-1.1 | Preference availability on search page | BB-TC09 | — |
| FR-1.2 | Preference weight adjustment | BB-TC07 | WB-TC32–WB-TC37 |
| FR-1.3 | Preference weight normalisation | BB-TC-G1 *(manual)* | WB-TC-G3c, WB-TC-G10d |
| FR-1.4 | Comfort = 0.6×walk + 0.4×transfer | BB-TC-G2 *(manual)* | WB-TC-G1a–G1f |
| FR-1.5 | Route filtering constraints | BB-TC06, BB-TC08 | — |
| FR-1.6 | Route category selection (min 1 active) | BB-TC05 | — |
| FR-1.7 | Expand/collapse preferences section | BB-TC-G3 *(manual)* | — |
| FR-1.8 | Save default preferences | BB-TC19, BB-TC20 | WB-TC-G10a–G10d |
| FR-2.1 | Route search initiation + validation | BB-TC01, BB-TC02 | — |
| FR-2.2 | Origin/destination input + autocomplete | BB-TC03, BB-TC04 | — |
| FR-4.3 | Assess transport risk (crowding + delay) | — | WB-TC15–WB-TC25 |
| FR-4.4 | Route generation, cost, ranking | BB-TC01 | WB-TC01–WB-TC14, WB-TC26–WB-TC48 |
| FR-4.5 | Aggregate segment-level risk | — | WB-TC15–WB-TC25 |
| FR-4.7 | Normalise dimensions to [0,1] | — | WB-TC33, WB-TC35 |
| FR-4.8 | Weighted composite score | BB-TC07 | WB-TC32–WB-TC37 |
| FR-4.9 | Rank routes with tie-breaking | — | WB-TC36 |
| FR-4.10 | ERP toll detection | BB-TC15 | — (UI-level only) |
| FR-4.11 | Carpark availability | BB-TC16 | — (UI-level only) |
| FR-4.12 | Weather integration | BB-TC17 | — (UI-level only) |
| FR-5 | Data freshness, fallback, cache | BB-TC21 | test_cache.py |
| FR-5.3 | Compare departure times | BB-TC11 | WB-TC-G11a–G11d |
| FR-5.4 | Crowding heatmap | BB-TC-G4 *(manual)* | WB-TC-G9a–G9c |

---

## 2. Demo Workflows

Workflows demonstrate integrated end-to-end scenarios. Each step references the BB-TC or WB-TC it exercises.

---

### Workflow 1: Public Transit Search — Full Journey

**Estimated Time:** ~3 min

**Goal:** Demonstrate the core user journey: search for a public transit route, explore results, inspect scoring, compare departure times, and view the route on the map.

**Test Cases Covered:** BB-TC01, BB-TC02, BB-TC03, BB-TC04, BB-TC05, BB-TC06, BB-TC07, BB-TC08, BB-TC09, BB-TC10, BB-TC11, BB-TC12, BB-TC13, WB-TC35, WB-TC38, WB-TC40

| Step | Action (What to Do) | Narration (What to Say) | Expected Result / Verify |
|------|---------------------|-------------------------|--------------------------|
| 1 | Open the app. Show the Home screen with the empty search form. | This is SGTravelBud — a smart transport routing app for Singapore. | Map is visible. Search fields are empty. Search button is disabled. |
| 2 | Type "Clem" in the Origin field. Wait for autocomplete dropdown to appear. Select "Clementi MRT Station". | We use Nominatim geocoding for place autocomplete — suggestions appear after 2 characters. | Autocomplete dropdown shows Singapore locations. Selection populates the field with coordinates. **(BB-TC03)** |
| 3 | Try to type the same location "Clementi MRT" in Destination. Note the Search button stays disabled. | The app validates that origin and destination are different. | Search button remains disabled. **(BB-TC02)** |
| 4 | Clear Destination. Enter "Raffles Place MRT" as the destination. Ensure Public Transit mode is selected. | Now we have a valid transit query — Clementi to Raffles Place. | Both fields filled. Search button becomes enabled. **(BB-TC01)** |
| 5 | Tap the Swap button between origin and destination. | Quick swap — useful if you entered them the wrong way around. | Origin and Destination values are reversed. **(BB-TC04)** |
| 6 | Swap back. Expand the "Show priorities & constraints" section. Show the 4 weight sliders (Time, Cost, Risk, Comfort) and the 3 constraint fields (Max Walk, Max Transfers, Max Budget). | Users can personalise how routes are ranked. Weights control the scoring formula; constraints hard-filter routes. | Sliders default to 0.25 each. Constraint fields are empty (no constraint). **(BB-TC09)** |
| 7 | Set Max Transfers to 0. Tap Search. | Let's first try a strict constraint — zero transfers. | If no direct routes exist: "No routes found" message. Otherwise, only direct routes shown. **(BB-TC06)** |
| 8 | Remove the Max Transfers constraint. Tap Search again with default weights. | Now searching with no constraints — we get the full ranked list. | Bottom sheet expands. 1–5 route cards appear with duration, cost, transfers, and crowding risk badges (Low/Medium/High). Map shows route polyline. **(BB-TC01)** |
| 9 | Navigate to the Results tab. Point out the route cards, risk legend, and the Compare Departure Times button. | Each card shows a composite score. Risk badges use real-time LTA crowding and delay data. | Route cards listed in score order. Risk legend shows Low (green), Medium (amber), High (red). |
| 10 | Tap Compare Departure Times. | This compares routes across 9 time slots — Morning Rush, Around Now, and Evening Rush. | Modal opens with 3 groups × 3 time slots. Cells show score, time, realistic time, cost, crowding. Best = green, worst = red. **(BB-TC11)** |
| 11 | Close the comparison modal. Select a route card. Tap View on Map. | Let's inspect this route on the map. | MapPage shows selected route with polyline, start/end markers. Bottom panel: time, distance, cost, risk badges. **(BB-TC12)** |
| 12 | Tap the Refresh button on the results page. | Users can refresh to get the latest real-time data. | Routes re-fetched. Data timestamps updated. **(BB-TC13)** |
| 13 | Navigate to the Scoring tab. Scroll through the scoring breakdown. | The Scoring page shows how each route was ranked. We normalise metrics to 0–1, multiply by weights, and sum. Realistic time accounts for bus frequency delays. | Active weights displayed. Comparison table (best green, worst red). Per-route breakdown cards with normalised bars, weighted contributions, and formula. Crowding heatmaps per MRT station (6AM–11PM). **(BB-TC10, WB-TC35)** |
| 14 | Go back to Home. Expand Advanced Priorities. Set Time = 1.0, Cost = 0.0, Risk = 0.0, Comfort = 0.0. Search again. | Watch how the ranking changes when we only care about speed. | The fastest route is now ranked #1. Order differs from the default-weight search. **(BB-TC07, WB-TC37)** |
| 15 | Add constraints: Max Walk = 5 min, Max Transfers = 1, Max Budget = $2.00. Search. | Constraints hard-filter: any route exceeding these limits is removed entirely. | Results include only routes satisfying ALL three constraints. Fewer routes returned. **(BB-TC08)** |
| 16 | Try to deselect Public Transit mode while Taxi/Drive is also disabled. | The app requires at least one mode to remain active. | Last enabled mode cannot be deselected; toggle reverts. **(BB-TC05)** |

---

### Workflow 2: Driving / Taxi Search — ERP, Parking, Weather

**Estimated Time:** ~3 min

**Goal:** Demonstrate driving and taxi mode with differentiation features: ERP toll calculation, carpark availability, and weather integration.

**Test Cases Covered:** BB-TC14, BB-TC15, BB-TC16, BB-TC17

| Step | Action (What to Do) | Narration (What to Say) | Expected Result / Verify |
|------|---------------------|-------------------------|--------------------------|
| 1 | On the Home screen, enter Origin = "NUS" and Destination = "Changi Airport". | A cross-island trip — good for showing driving features. | Fields populated. Search button enabled. |
| 2 | Toggle mode to Taxi/Drive only (deselect Public Transit). | Now we're searching exclusively for driving and taxi routes. | Only the Taxi/Drive toggle is active. |
| 3 | Tap Search. | The backend calls Google Maps for driving directions, then enriches them with ERP gantry detection, carpark availability, and weather data. | Results show route cards categorised as "Taxi" or "Drive". Cost reflects taxi fare estimate or fuel cost. No transfer count shown. **(BB-TC14)** |
| 4 | Select a driving route. Check the route explanation text for ERP mentions. | The app detects ERP gantries along the route polyline and adds toll charges to the cost. | If the route passes ERP gantries during peak hours, the cost includes toll charges and the explanation mentions ERP. **(BB-TC15)** |
| 5 | Check the route details for carpark availability near the destination. | For driving routes, we query LTA for nearby HDB/URA carparks and show available lot counts. | Carpark availability data appears in the route response with lot counts. **(BB-TC16)** |
| 6 | Check the route explanation or assessment for weather information. | We pull the NEA 2-hour weather forecast and factor adverse weather into the risk assessment. | If rain or thunderstorms are forecast, the route explanation or risk reflects this. **(BB-TC17)** |
| 7 | Enable BOTH modes (Public Transit + Taxi/Drive). Search again. | With both modes on, you get a mixed comparison — transit vs driving vs taxi side by side. | Results include a mix of transit, taxi, and drive routes, up to 5 total. Categories labelled correctly. |

---

### Workflow 3: Settings, Data Freshness, and Fallback

**Estimated Time:** ~2 min

**Goal:** Demonstrate user settings management, live data source monitoring, cache refresh, and fallback resilience.

**Test Cases Covered:** BB-TC18, BB-TC19, BB-TC20, BB-TC21

| Step | Action (What to Do) | Narration (What to Say) | Expected Result / Verify |
|------|---------------------|-------------------------|--------------------------|
| 1 | Navigate to the Settings tab. Show the current settings: language, units, and default weights. | User preferences are persisted on the backend as a JSON file. | Settings page loads with current values. Default weights shown as sliders. **(BB-TC18)** |
| 2 | Change Language to "zh" (Chinese). Change Units to "imperial". Adjust the default Time weight to 0.8. Tap Save. | Settings are saved via PUT /settings and persist across sessions. | Green success toast appears. **(BB-TC19)** |
| 3 | Navigate away to Home, then back to Settings. | Let's verify persistence. | Settings still show zh, imperial, Time = 0.8. Values persisted. **(BB-TC20)** |
| 4 | Reset settings back to defaults (en, metric, all weights 0.25). Save. | Restoring defaults for the rest of the demo. | Success toast. Settings reset. |
| 5 | Scroll down to the Data Sources section. Show the table of data sources with their Live/Fallback status. | This shows the real-time health of every external data source the app depends on. Each has a TTL-based cache. | Table lists all data sources. Each shows "Live" (green) or "Fallback" (amber) badge with last-retrieved timestamp. **(BB-TC21)** |
| 6 | Tap the Refresh button in the Data Sources section. | This invalidates all caches and re-fetches fresh data from every external API. If an API is down, the app falls back to the last known good data. | Sources reload. Live sources refresh timestamps. Any unavailable API shows "Fallback" badge. |

---

## 3. Black Box Testing

Black box tests verify system behaviour from the user's perspective, without knowledge of internal implementation. Tests are organised by Functional Requirement group.

---

### 3.1 Route Search and Input Validation

Covers: FR-2.1 (Route Search Initiation), FR-2.2 (Origin/Destination Input)

| TC-ID | FR Ref | Test Input / Action | Expected Output | Actual Output | Result |
|-------|--------|---------------------|-----------------|---------------|--------|
| BB-TC01 | FR-2.1 | Origin = NTU North Spine, Destination = Marina Bay Sands, mode = Public Transit, tap Search | System generates and displays ranked route options with time, cost, transfers, and risk badges | Ranked route options displayed correctly | Pass |
| BB-TC02 | FR-2.1.3 | Origin = NTU North Spine, Destination = NTU North Spine | Search button remains disabled because origin and destination are identical | Search button remained disabled | Pass |
| BB-TC03 | FR-2.2.2 | Type "Marina" into Destination field | Autocomplete suggestions appear for Singapore locations | Suggestions appeared, including Marina Barrage and Marina Bay Sands | Pass |
| BB-TC04 | FR-2.2 | Valid origin and destination entered, then tap Swap button | Origin and destination values are exchanged and inputs revalidated | Values swapped successfully and remained valid | Pass |
| BB-TC05 | FR-1.6.2, FR-1.6.3 | Valid inputs, attempt to deselect the last enabled mode (Public Transit when Taxi/Drive is off) | Toggle action reverts; last enabled mode cannot be disabled | Last enabled mode (Public Transit) remained selected | Pass |

---

### 3.2 Preferences, Constraints and Ranking

Covers: FR-1.1 (Preference Display), FR-1.2 (Weight Adjustment), FR-1.5 (Constraints)

| TC-ID | FR Ref | Test Input / Action | Expected Output | Actual Output | Result |
|-------|--------|---------------------|-----------------|---------------|--------|
| BB-TC06 | FR-1.5.2 | Set Max Transfers = 0, then Search | Only direct routes shown, or "No routes found" displayed if none exists | No direct routes found; message displayed correctly | Pass |
| BB-TC07 | FR-1.2, FR-1.3 | Set Time weight = 1.0, Cost = 0.0, Risk = 0.0, Comfort = 0.0, then Search | Fastest route becomes top-ranked; weights normalised automatically | Fastest route ranked first | Pass |
| BB-TC08 | FR-1.5 | Set Max Walk = 5 min, Max Transfers = 1, Max Budget = $5, then Search | Only routes satisfying all constraints are shown; Taxi option excluded by budget | Returned routes satisfying all conditions | Pass |
| BB-TC09 | FR-1.1 | Open Search page without prior customisation | Priorities section shows four sliders each defaulting to 0.25; constraint fields are empty | Default weights displayed correctly | Pass |
| BB-TC10 | FR-4.8 | Remove strict constraints and Search again using default weights, then open Scoring tab | More route options are displayed; Scoring tab shows comparison table and per-route breakdown | Full ranked list displayed; scoring breakdown shown | Pass |

---

### 3.3 Results, Comparison and Map Display

Covers: FR-4.8 (Composite Score Display), FR-5.3 (Departure Time Comparison)

| TC-ID | FR Ref | Test Input / Action | Expected Output | Actual Output | Result |
|-------|--------|---------------------|-----------------|---------------|--------|
| BB-TC11 | FR-5.3 | Tap "Compare Departure Times" after a successful search | Comparison modal opens with 3 groups × 3 time slots showing score, time, realistic time, cost, crowding | Comparison modal displayed correctly | Pass |
| BB-TC12 | FR-4.8 | Select a route card, tap "View on Map" | Selected route shown on map with polyline, start/end markers, and route details panel | Map displayed selected route and route details correctly | Pass |
| BB-TC13 | FR-4.4 | Tap Refresh button on results page | System re-fetches data and regenerates ranked routes | Routes refreshed successfully | Pass |

---

### 3.4 Driving / Taxi Features

Covers: FR-4.10 (ERP), FR-4.11 (Carpark), FR-4.12 (Weather)

| TC-ID | FR Ref | Test Input / Action | Expected Output | Actual Output | Result |
|-------|--------|---------------------|-----------------|---------------|--------|
| BB-TC14 | FR-4.4 | Origin = NTU Hall 4, Destination = Jewel Changi Airport, mode = Taxi/Drive only | Results include Taxi and Drive routes only, labelled correctly | Taxi and Drive routes displayed only | Pass |
| BB-TC15 | FR-4.10 | Select a driving route that passes an ERP gantry during peak hours | Route cost includes ERP tolls; explanation mentions ERP where applicable | ERP reflected in cost and explanation | Pass |
| BB-TC16 | FR-4.11 | Select a driving route and inspect route details | Carpark availability near destination is shown with lot counts | Carpark lot data displayed | Pass |
| BB-TC17 | FR-4.12 | Search when adverse weather (rain/thunderstorm) is forecast | Weather condition is reflected in route explanation or risk assessment | "Rain expected along route" displayed | Pass |

---

### 3.5 Settings, Data Freshness and Fallback

Covers: FR-1.8 (Settings Persistence), FR-5 (Data Freshness)

| TC-ID | FR Ref | Test Input / Action | Expected Output | Actual Output | Result |
|-------|--------|---------------------|-----------------|---------------|--------|
| BB-TC18 | FR-1.8.1 | Open Settings page | Current language, units, and default weights are displayed | Settings loaded correctly | Pass |
| BB-TC19 | FR-1.8, FR-1.2 | Change language to Chinese and adjust Time weight to 0.8, then tap Save Settings | Updated settings are saved and applied | Changes saved and reflected correctly | Pass |
| BB-TC20 | FR-1.8.2 | Leave Settings page and return | Saved settings remain persisted | Settings remain updated | Pass |
| BB-TC21 | FR-5 | Open Data Sources section in Settings | All data sources listed with Live/Fallback status badge and last-retrieved timestamp | Data source table displayed correctly | Pass |

---

## 4. White Box Testing

White box tests verify internal code logic using knowledge of implementation. The control class under test is `RouteScoringController`, implemented across `Program/backend/services/routing.py` and `Program/backend/services/scoring.py`.

---

### 4.1 Overview and Class Under Test

**Control Class:** `RouteScoringController`
**Implementation files:**
- `Program/backend/services/routing.py`
- `Program/backend/services/scoring.py`

**FR Coverage:**
| FR | Method Tested |
|----|--------------|
| FR-4.5 | `aggregate_route_risks()` |
| FR-4.4 | `estimate_cost()`, `build_route_steps()` |
| FR-4.7 | `normalize()` via `rank_routes()` |
| FR-4.8 | `composite_score()` via `rank_routes()` |
| FR-4.9 | `rank_routes()`, `tie_break_key()` |
| FR-1.4 | `compute_comfort()` |
| FR-5 | `compute_realistic_time()` |

**Test framework:** Python 3.11 + `unittest` + `pytest`
**Test file:** `Program/tests/test_routing.py`
**Run command:** `cd Program && python -m pytest tests/test_routing.py -v`

---

### 4.2 Equivalence Class + Boundary Value Analysis

#### Method 1: `estimate_cost(distance_m, duration_s, mode)` — FR-4.4

**Purpose:** Estimates monetary cost of a route using Singapore-specific fare models.

**Equivalence Classes — `mode` parameter**

| Class ID | Partition | Representative | Valid? |
|----------|-----------|----------------|--------|
| EC-M1 | Transit mode | `"transit"` | Valid |
| EC-M2 | Taxi mode | `"taxi"` | Valid |
| EC-M3 | Driving (mapped to taxi branch) | `"driving"` | Valid |
| EC-M4 | Own-car mode | `"owncar"` | Valid |
| EC-M5 | Unrecognised string | `"bicycle"` | Invalid (falls to transit) |

**Equivalence Classes — `distance_m` (transit mode)**

| Class ID | Partition | Representative | Expected Fare |
|----------|-----------|----------------|---------------|
| EC-D1 | Zero distance | 0 m | $0.99 |
| EC-D2 | Short trip (0–3200 m) | 1600 m | $0.99 |
| EC-D3 | Mid-range (3201–20200 m) | 10000 m | $1.40 |
| EC-D4 | Long trip (20201–40200 m) | 30000 m | $1.78 |
| EC-D5 | Beyond table (>40200 m) | 50000 m | $2.20 |
| EC-D6 | Negative (invalid) | −500 m | $0.99 (clamped) |

**Boundary Values — `distance_m` (transit mode)**

| BV-ID | Boundary | Value | Expected Fare |
|-------|----------|-------|---------------|
| BV-D1 | Exact floor of first bracket | 3200 m | $0.99 |
| BV-D2 | One metre past first bracket | 3201 m | $1.09 |
| BV-D3 | Exact last table entry | 40200 m | $1.98 |
| BV-D4 | One metre past last entry (max fare) | 40201 m | $2.20 |
| BV-D5 | Zero (absolute floor) | 0 m | $0.99 |

**Equivalence Classes — taxi distance**

| Class ID | Partition | Representative | Rate Applied |
|----------|-----------|----------------|--------------|
| EC-T1 | Short taxi (≤10 km) | 5 km | $0.55/km |
| EC-T2 | Long taxi (>10 km) | 15 km | $0.55/km up to 10, $0.629/km beyond |

**Boundary Value — taxi duration**

| BV-ID | Boundary | Value | Expected Waiting Charge |
|-------|----------|-------|------------------------|
| BV-S1 | Zero idle time | 0 s | $0.00 |
| BV-S2 | One increment | 45 s idle | $0.22 |

---

#### Method 2: `aggregate_route_risks(segments)` — FR-4.5

**Purpose:** Aggregates segment-level crowding and delay into a single route-level risk category.

**Equivalence Classes — segments list**

| Class ID | Partition | Description |
|----------|-----------|-------------|
| EC-S1 | Empty list | No segments → both dims Unknown |
| EC-S2 | All Low (known) | All Low crowd and delay |
| EC-S3 | All Unknown (one dim) | All segments have Unknown crowding |
| EC-S4 | Mixed Unknown + known | Some Unknown, some known → max-of-known wins |
| EC-S5 | Contains High | Worst segment is High → route = High |
| EC-S6 | Fallback segment | At least one is_fallback=True → uses_fallback=True |

**Boundary Values — numeric risk**

| BV-ID | Value | Category |
|-------|-------|----------|
| BV-R1 | 1 | Low |
| BV-R2 | 2 | Medium / Unknown |
| BV-R3 | 3 | High |

---

### 4.3 Basis Path Testing

#### `estimate_cost()` — Cyclomatic Complexity V(G) = 5

**Control Flow:**
```
Node 1: mode == "taxi" or "driving"?
  YES → Node 2: distance_km <= 10?
          YES → Path P1 (short taxi)
          NO  → Path P2 (long taxi, higher per-km rate)
  NO  → Node 3: mode == "owncar"?
          YES → Path P3 (fuel cost only)
          NO  → transit loop
                Node 4: distance_km <= threshold?
                  YES (early exit) → Path P4
                  Loop exhausted  → Path P5 (max fare)
```

| Path | Description | Test Case |
|------|-------------|-----------|
| P1 | Taxi, short distance (≤10 km) | WB-TC09 |
| P2 | Taxi, long distance (>10 km) | WB-TC10 |
| P3 | Own car fuel cost | WB-TC13 |
| P4 | Transit, fare found in table | WB-TC06 |
| P5 | Transit, distance beyond table → max fare | WB-TC05 |

---

#### `aggregate_route_risks()` — Cyclomatic Complexity V(G) = 7

**Control Flow:**
```
Node 1: segments empty?
  YES → Path P1 (Unknown both dims)
  NO  →
    Node 2: any crowd Unknown?
      YES → Node 3: any known crowd nums?
              YES → Path P4 (max-of-known crowd)
              NO  → Path P3 (all crowd Unknown)
      NO  → Path P2 (max of all crowd)
    [Mirror for delay: Nodes 4,5,6]
    Node 7: any is_fallback?
      YES → Path P6 (uses_fallback=True)
```

| Path | Description | Test Case |
|------|-------------|-----------|
| P1 | Empty segments | WB-TC15 |
| P2 | All crowd known, no Unknown | WB-TC16 |
| P3 | All crowd Unknown, none known | WB-TC18 |
| P4 | Mixed crowd Unknown + known → max-of-known | WB-TC19 |
| P5 | Mirror P3 for delay dimension | WB-TC20 |
| P6 | Fallback flag detected | WB-TC21 |

---

### 4.4 Test Case Minimisation

Minimisation reduces redundant tests while preserving full equivalence class and basis path coverage.

| Principle | Application | Example |
|-----------|-------------|---------|
| BVAs subsume interior EC representatives | BV-D1 (3200 m) covers EC-D2 (short trip) | WB-TC02 covers both |
| One representative per EC | Each EC has exactly one test | EC-M1 → WB-TC01 |
| Invalid inputs collapsed | One test per invalid class | EC-D6 → WB-TC07; EC-M5 → WB-TC08 |
| Basis paths are already minimal | No duplication across paths | 5 paths = 5 tests |
| Combined coverage where possible | WB-TC05 covers BV-D4, EC-D5, Path P5 | Single test serves all three |

**Result:** 57 designed tests reduced to 50 after minimisation (12% reduction).

---

### 4.5 White Box Execution Results

**Run:** `cd Program && python -m pytest tests/test_routing.py -v`
**Result:** 50 passed in 0.27 seconds

#### `estimate_cost()` — WB-TC01 to WB-TC14

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC01 | EC + BVA | transit, dist=0 | $0.99 (floor) | FR-4.4 |
| WB-TC02 | BVA | transit, dist=3200 | $0.99 (upper of first bracket) | FR-4.4 |
| WB-TC03 | BVA | transit, dist=3201 | $1.09 (crosses into next bracket) | FR-4.4 |
| WB-TC04 | BVA | transit, dist=40200 | $1.98 (penultimate bracket) | FR-4.4 |
| WB-TC05 | BVA + Basis P5 | transit, dist=40201 | $2.20 (max fare) | FR-4.4 |
| WB-TC06 | EC + Basis P4 | transit, dist=6000 | $1.29 | FR-4.4 |
| WB-TC07 | EC (invalid) | transit, dist=−500 | $0.99 (clamped to 0) | FR-4.4 |
| WB-TC08 | EC (invalid mode) | mode="bicycle", dist=1000 | mode="transit", $0.99 | FR-4.4 |
| WB-TC09 | EC + Basis P1 | taxi, dist=5000, dur=600 | total≈$7.34, mode="taxi" | FR-4.4 |
| WB-TC10 | Basis P2 | taxi, dist=15000, dur=600 | total > WB-TC09; distance_charge=$8.645 | FR-4.4 |
| WB-TC11 | EC | driving, dist=5000, dur=600 | mode="taxi", same total as WB-TC09 | FR-4.4 |
| WB-TC12 | BVA + Basis | taxi, dist=5000, dur=0 | waiting_charge=0.00 | FR-4.4 |
| WB-TC13 | Basis P3 | owncar, dist=10000 | $1.20, mode="owncar" | FR-4.4 |
| WB-TC14 | EC | owncar, dist=0 | $0.00 | FR-4.4 |
| WB-TC14b | Contract | all modes, dist=5000, dur=300 | all return "total" key (float) | FR-4.4 |

#### `aggregate_route_risks()` — WB-TC15 to WB-TC25

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC15 | EC + Basis P1 | [] (empty) | Unknown,2, Unknown,2, False | FR-4.5 |
| WB-TC16 | Basis P2 | [Low crowd, Low delay] | Low,1, Low,1, False | FR-4.5 |
| WB-TC17 | EC | [High crowd, Low delay] | High,3 crowd, Low,1 delay | FR-4.5 |
| WB-TC18 | Basis P3 | [Unknown crowd, Low delay] | Unknown,2 crowd, Low,1 delay | FR-4.5 |
| WB-TC19 | Basis P4 | [Unknown crowd, High crowd] + Low delay | High,3 crowd (max-of-known wins) | FR-4.5 |
| WB-TC20 | EC | [Low crowd, Unknown delay] | Low,1 crowd, Unknown,2 delay | FR-4.5 |
| WB-TC21 | EC + Basis P6 | [Low crowd, Low delay, is_fallback=True] | uses_fallback=True | FR-4.5 |
| WB-TC21b | EC | [Low crowd, Low delay, delay_fallback=True] | uses_fallback=True | FR-4.5 |
| WB-TC22 | EC | [Medium crowd, High crowd] | High,3 crowd | FR-4.5 |
| WB-TC23 | EC | [Low delay, High delay] across two segments | High,3 delay | FR-4.5 |
| WB-TC24 | BVA | all Medium (numeric=2) | Medium,2 both dims | FR-4.5 |
| WB-TC25 | Contract | [Low,Low] | 5-tuple: (RiskCategory, int, RiskCategory, int, bool) | FR-4.5 |

#### `compute_realistic_time()` — WB-TC26 to WB-TC31

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC26 | EC | base=30.0, steps=[] | 30.0 (unchanged) | FR-5 |
| WB-TC27 | EC | base=30.0, steps=[Walk, Train] | 30.0 (no penalty) | FR-5 |
| WB-TC28 | EC | base=30.0, one bus miss_penalty=10 | 35.0 (+5.0) | FR-5 |
| WB-TC29 | EC | base=20.0, two buses penalties=10,8 | 29.0 (+5.0+4.0) | FR-5 |
| WB-TC30 | EC | bus step with no miss_penalty_min key | 30.0 (no penalty added) | FR-5 |
| WB-TC31 | BVA | base=0.0, one bus miss_penalty=6 | 3.0 (only penalty) | FR-5 |

#### `rank_routes()` — WB-TC32 to WB-TC37

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC32 | EC | candidates=[] | [] (empty) | FR-4.9 |
| WB-TC33 | EC | single route | score=0.0 (all normalised values = 0) | FR-4.7, FR-4.8 |
| WB-TC34 | EC | Route A (fast/cheap/low risk) vs Route B (slow/costly/high risk) | A ranked first | FR-4.8, FR-1.4 |
| WB-TC35 | Contract | two routes | all routes have normalized_time, normalized_cost, normalized_risk, normalized_comfort, score keys | FR-4.7 |
| WB-TC36 | Contract | 3 unsorted routes | output list in ascending score order | FR-4.9 |
| WB-TC37 | EC | time weight=0.9, cost/risk/comfort=0.033; fast+risky vs slow+safe | fast route ranked first | FR-4.8 |

#### `add_explanations()` — WB-TC38 to WB-TC43

| WB-TC | Technique | Top Weight | Expected Explanation Prefix | FR |
|-------|-----------|-----------|------------------------------|----|
| WB-TC38 | EC | time=0.7 | "Fastest option at N min" | FR-4.8 |
| WB-TC39 | EC | cost=0.7 | "Cheapest at $X.XX" | FR-4.8 |
| WB-TC40 | EC | risk=0.7 | "Lowest risk: Cat" | FR-4.8 |
| WB-TC41 | EC | comfort=0.7 | "Most comfortable: N min walk, N transfer(s)" | FR-1.4, FR-4.8 |
| WB-TC42 | EC | routes=[] | No exception raised | FR-4.8 |
| WB-TC43 | Contract | two routes, any weights | Every route has "explanation" key (string) | FR-4.8 |

#### `build_route_steps()` — WB-TC44 to WB-TC48

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC44 | EC | driving route, no segments | 1 Drive step, transfers=0 | FR-4.4 |
| WB-TC45 | EC | transit route with empty legs | [], transfers=0 (no crash) | FR-4.4 |
| WB-TC46 | EC | transit route, 1 bus step, 1 matching segment | 1 Bus step, line_name correct, transfers=0 | FR-4.4 |
| WB-TC47 | EC | transit route, Bus then Train | transfers=1 | FR-4.4 |
| WB-TC48 | EC | driving route with High-delay segment | delay propagated to Drive step | FR-4.4 |

#### `compute_comfort()` — WB-TC-G1a to WB-TC-G1f

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC-G1a | EC | walk=0.0, transfers=0 | 0.0 (best comfort) | FR-1.4 |
| WB-TC-G1b | EC | walk=30.0, transfers=5 | 10.0 (worst comfort) | FR-1.4 |
| WB-TC-G1c | BVA (cap) | walk=60.0, transfers=0 | same as walk=30.0 | FR-1.4 |
| WB-TC-G1d | BVA (cap) | walk=0.0, transfers=6 | same as transfers=5 | FR-1.4 |
| WB-TC-G1e | EC | walk=8.0, transfers=1 | 0.6×(8/3) + 0.4×2 = 2.4 | FR-1.4 |
| WB-TC-G1f | EC | walk=15.0, transfers=0 | 0.6×5.0 = 3.0 | FR-1.4 |

#### `normalize()` and `composite_score()` — WB-TC-G2 / WB-TC-G3

| WB-TC | Function | Technique | Input | Expected | FR |
|-------|----------|-----------|-------|----------|----|
| WB-TC-G2a | `normalize()` | EC | [10, 20, 30] | [0.0, 0.5, 1.0] | FR-4.7 |
| WB-TC-G2b | `normalize()` | EC (identical) | [5, 5, 5] | [0.0, 0.0, 0.0] | FR-4.7 |
| WB-TC-G2c | `normalize(invert=True)` | EC | [10, 20, 30] | [1.0, 0.5, 0.0] | FR-4.7 |
| WB-TC-G2d | `normalize()` | EC (empty) | [] | [] | FR-4.7 |
| WB-TC-G2e | `normalize()` | BVA (single) | [42.0] | [0.0] | FR-4.7 |
| WB-TC-G2f | `tie_break_key()` | EC | equal risk, lower comfort_num | lower comfort_num wins | FR-4.9 |
| WB-TC-G3a | `composite_score()` | EC | equal weights, mixed norms | 0.375 | FR-4.8 |
| WB-TC-G3b | `composite_score()` | EC | time=0.8, norm time=1.0 rest=0 | 0.8 | FR-4.8 |
| WB-TC-G3c | `composite_score()` | EC | all weights=2.0, all norms=1.0 | 1.0 (normalised) | FR-4.8 |
| WB-TC-G3d | `composite_score()` | EC | all norms=0.0 | 0.0 | FR-4.8 |

#### `estimate_cost()` — Mid-range Brackets — WB-TC-G4a to WB-TC-G4d

| WB-TC | Technique | Distance | Expected Fare | Bracket | FR |
|-------|-----------|----------|--------------|---------|-----|
| WB-TC-G4a | EC | 10000 m | $1.40 | ≤10.2 km | FR-4.4 |
| WB-TC-G4b | EC | 15000 m | $1.50 | ≤15.2 km | FR-4.4 |
| WB-TC-G4c | EC | 20000 m | $1.60 | ≤20.2 km | FR-4.4 |
| WB-TC-G4d | EC | 25000 m | $1.70 | ≤26.2 km | FR-4.4 |

#### `rank_routes()` Weight Sensitivity — WB-TC-G5a to WB-TC-G5c

| WB-TC | Technique | Dominant Weight | Expected | FR |
|-------|-----------|----------------|----------|----|
| WB-TC-G5a | EC | cost=0.9 | cheapest ranked first | FR-4.8 |
| WB-TC-G5b | EC | risk=0.9 | lowest risk ranked first | FR-4.8 |
| WB-TC-G5c | EC | comfort=0.9 | 0 walk + 0 transfers ranked first | FR-4.8 |

#### `aggregate_route_risks()` Asymmetric — WB-TC-G6a to WB-TC-G6b

| WB-TC | Technique | Input | Expected crowd | Expected delay | FR |
|-------|-----------|-------|----------------|----------------|----|
| WB-TC-G6a | EC | crowd=Unknown+High, delay=all Low | High | Low | FR-4.5 |
| WB-TC-G6b | EC | crowd=all Low, delay=Unknown+Medium | Low | Medium | FR-4.5 |

#### `compute_realistic_time()` 3+ Buses — WB-TC-G7a

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC-G7a | EC | base=20.0, 3 buses (penalties 10,8,6) | 32.0 | FR-5 |

#### `build_route_steps()` Lookup Miss — WB-TC-G8a

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC-G8a | EC | transit step, dep/arr not in segment lookup | crowding=None, delay=None, no crash | FR-4.4 |

#### `GET /crowding/heatmap` — WB-TC-G9a to WB-TC-G9c

| WB-TC | Technique | Input | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC-G9a | EC (invalid) | station="XYZNOTASTATION" | 200, intervals=[] | FR-5.4 |
| WB-TC-G9b | EC (mock) | known station + mocked PCD | intervals populated, valid schema | FR-5.4 |
| WB-TC-G9c | EC | raw CrowdLevel l/h/m/unknown | normalised to Low/High/Medium/Unknown | FR-5.4 |

#### `GET /settings` and `PUT /settings` — WB-TC-G10a to WB-TC-G10d

| WB-TC | Technique | Action | Expected | FR |
|-------|-----------|--------|----------|----|
| WB-TC-G10a | EC | GET /settings | 200, all 6 fields present | FR-1.8 |
| WB-TC-G10b | EC | PUT /settings with new values | response reflects new values | FR-1.8 |
| WB-TC-G10c | EC | GET after PUT | persisted values returned | FR-1.8 |
| WB-TC-G10d | Contract | GET /settings defaults | sum of 4 weights = 1.0 | FR-1.3 |

#### `_build_compare_slots()` — WB-TC-G11a to WB-TC-G11d

| WB-TC | Technique | Check | Expected | FR |
|-------|-----------|-------|----------|----|
| WB-TC-G11a | EC | Count of groups and slots | 3 groups × 3 slots = 9 total | FR-5.3 |
| WB-TC-G11b | EC | Group labels | Morning Rush, Around Now, Evening Rush | FR-5.3 |
| WB-TC-G11c | EC | All slot datetimes | Every datetime strictly in the future | FR-5.3 |
| WB-TC-G11d | EC | Around Now slot labels | Now, +30 min, +1 hr | FR-5.3 |

---

## 5. Full Execution Summary

```
Platform: darwin — Python 3.11 — pytest 7.4.4

Test Files:
  tests/test_routing.py          (83 tests)
  tests/test_scoring.py          (11 tests)
  tests/test_api.py              (11 tests)
  tests/test_cache.py             (1 test)
  tests/test_clients_google_fallback.py (1 test)

Result: 91 passed in 0.88 seconds
```

| Test File | Tests | Passed | Failed | Coverage |
|-----------|-------|--------|--------|----------|
| test_routing.py | 83 | 83 | 0 | estimate_cost, aggregate_route_risks, compute_realistic_time, rank_routes, add_explanations, build_route_steps, compute_comfort |
| test_scoring.py | 11 | 11 | 0 | normalize, composite_score, tie_break_key |
| test_api.py | 11 | 11 | 0 | GET/PUT /settings, /crowding/heatmap, _build_compare_slots |
| test_cache.py | 1 | 1 | 0 | TTLCache |
| test_clients_google_fallback.py | 1 | 1 | 0 | Google client fallback |
| **Total** | **91** | **91** | **0** | |

