# SGTravelBud — Test Cases

## TC1: Route Search — Basic Transit Search

| Field | Details |
|-------|---------|
| **Objective** | Verify that a basic public transit route search returns valid results |
| **Preconditions** | Backend server running; Google Maps API key configured |
| **Steps** | 1. Open the app (MainView) 2. Enter "Clementi MRT" as origin 3. Enter "Raffles Place MRT" as destination 4. Ensure "Public Transit" mode is selected 5. Tap **Search** |
| **Expected Result** | Bottom sheet expands showing 1–5 route cards. Each card displays duration, cost, transfer count, and a crowding risk badge (Low/Medium/High). Map updates with route polyline. |

---

## TC2: Route Search — Driving / Taxi Mode

| Field | Details |
|-------|---------|
| **Objective** | Verify driving and taxi routes are returned when the Taxi/Drive toggle is active |
| **Preconditions** | Backend running |
| **Steps** | 1. Enter origin "NUS" and destination "Changi Airport" 2. Toggle mode to **Taxi/Drive** (deselect Public Transit) 3. Tap **Search** |
| **Expected Result** | Results contain route cards categorised as "Taxi" or "Drive". Cost reflects estimated taxi fare or fuel cost. No transit-specific fields (transfers) shown. |

---

## TC3: Route Search — Both Modes Selected

| Field | Details |
|-------|---------|
| **Objective** | Verify mixed-mode results when both Public Transit and Taxi/Drive are enabled |
| **Steps** | 1. Enter origin and destination 2. Enable both mode toggles 3. Tap **Search** |
| **Expected Result** | Results include a mix of transit and driving/taxi routes, deduplicated, up to 5 total. Categories are labelled correctly. |

---

## TC4: Route Search — Swap Origin and Destination

| Field | Details |
|-------|---------|
| **Objective** | Verify the swap button correctly reverses origin and destination |
| **Steps** | 1. Enter "Jurong East" as origin and "Marina Bay" as destination 2. Tap the **Swap** button |
| **Expected Result** | Origin becomes "Marina Bay" and destination becomes "Jurong East". |

---

## TC5: Route Search — Validation (Empty Fields)

| Field | Details |
|-------|---------|
| **Objective** | Verify search is blocked when required fields are incomplete |
| **Steps** | 1. Leave origin empty, enter destination 2. Attempt to tap **Search** |
| **Expected Result** | Search button is disabled. No API call is made. |

---

## TC6: Route Search — Validation (Same Origin and Destination)

| Field | Details |
|-------|---------|
| **Objective** | Verify search rejects identical origin and destination |
| **Steps** | 1. Enter "Orchard MRT" as both origin and destination 2. Tap **Search** |
| **Expected Result** | Search button is disabled or an error message is shown. No results returned. |

---

## TC7: Route Search — No Routes Found

| Field | Details |
|-------|---------|
| **Objective** | Verify graceful handling when no routes exist for the query |
| **Steps** | 1. Enter a very remote or invalid location pair 2. Tap **Search** |
| **Expected Result** | "No routes found" message displayed. App does not crash. |

---

## TC8: Advanced Priorities — Weight Sliders

| Field | Details |
|-------|---------|
| **Objective** | Verify that adjusting weight sliders changes route ranking |
| **Steps** | 1. Enter origin/destination and search with default weights (all 0.25) 2. Note the top-ranked route 3. Expand Advanced Priorities 4. Set Time weight to 1.0 and all others to 0.0 5. Search again |
| **Expected Result** | The fastest route is now ranked first. Route ordering changes compared to step 2. |

---

## TC9: Constraints — Max Walk Time

| Field | Details |
|-------|---------|
| **Objective** | Verify max walk constraint filters routes appropriately |
| **Steps** | 1. Expand Advanced Priorities 2. Set Max Walk to 5 minutes 3. Search for a route that normally involves long walks |
| **Expected Result** | Routes with walking segments exceeding 5 minutes are excluded from results. |

---

## TC10: Constraints — Max Transfers

| Field | Details |
|-------|---------|
| **Objective** | Verify max transfers constraint filters routes |
| **Steps** | 1. Set Max Transfers to 0 2. Search for a multi-transfer route |
| **Expected Result** | Only direct (no-transfer) routes are returned. If none exist, "No routes found" is shown. |

---

## TC11: Constraints — Max Budget

| Field | Details |
|-------|---------|
| **Objective** | Verify max budget constraint filters routes by cost |
| **Steps** | 1. Set Max Budget to $1.00 2. Search for a route |
| **Expected Result** | Only routes costing $1.00 or less are returned. Expensive routes are excluded. |

---

## TC12: Results Page — Route Selection and Map Navigation

| Field | Details |
|-------|---------|
| **Objective** | Verify selecting a route and navigating to map view |
| **Steps** | 1. Perform a successful search 2. On ResultsPage, tap a RouteCard 3. Tap "View on Map" |
| **Expected Result** | MapPage opens showing the selected route on an interactive map with start/end markers and a polyline. Bottom panel shows time, distance, cost, risk badges. |

---

## TC13: Map Page — Navigate Between Routes

| Field | Details |
|-------|---------|
| **Objective** | Verify Prev/Next buttons cycle through routes on the map |
| **Steps** | 1. Navigate to MapPage with multiple routes available 2. Tap **Next** to go to route 2 3. Tap **Prev** to return to route 1 |
| **Expected Result** | Map updates to show the corresponding route. "Route X of Y" label updates. Prev is disabled on route 1; Next is disabled on the last route. |

---

## TC14: Scoring Page — Breakdown Display

| Field | Details |
|-------|---------|
| **Objective** | Verify scoring breakdown is displayed correctly |
| **Steps** | 1. Perform a search that returns 2+ routes 2. Navigate to the Scoring tab |
| **Expected Result** | Page shows: active weights, comparison table (best values green, worst red), normalised bar charts per route, weighted contribution grid, and formula breakdown. |

---

## TC15: Scoring Page — Single Route

| Field | Details |
|-------|---------|
| **Objective** | Verify scoring page handles a single route gracefully |
| **Steps** | 1. Perform a search that returns exactly 1 route 2. Navigate to the Scoring tab |
| **Expected Result** | Comparison table is hidden (not applicable). Single route breakdown card is shown with rank "Best". |

---

## TC16: Departure Time Comparison

| Field | Details |
|-------|---------|
| **Objective** | Verify the time comparison modal shows routes across 9 time slots |
| **Steps** | 1. Perform a search 2. On ResultsPage, tap **Compare Departure Times** |
| **Expected Result** | Modal opens with 3 groups (Morning Rush, Around Now, Evening Rush). Each group has 3 time slots. Cells show score, time, realistic time, cost, and crowding. Best values highlighted green, worst red. |

---

## TC17: Departure Time Comparison — Close Modal

| Field | Details |
|-------|---------|
| **Objective** | Verify the modal can be dismissed |
| **Steps** | 1. Open the time comparison modal 2. Tap the close button (or click backdrop) |
| **Expected Result** | Modal closes. Results page is visible again. |

---

## TC18: Crowding Heatmap — Display

| Field | Details |
|-------|---------|
| **Objective** | Verify crowding heatmap renders for train stations |
| **Steps** | 1. Perform a transit search involving MRT stations 2. Navigate to Scoring page |
| **Expected Result** | Heatmap bars appear for each train station on the route. Color blocks show Low (green), Medium (amber), High (red) for each hour from 6 AM to 11 PM. A "Now" marker indicates the current time. |

---

## TC19: Settings Page — Load and Display

| Field | Details |
|-------|---------|
| **Objective** | Verify settings page loads saved preferences |
| **Steps** | 1. Navigate to the Settings tab |
| **Expected Result** | Page shows current language, units, and default weight sliders loaded from backend. Data sources table shows status (Live/Fallback) for each dataset. |

---

## TC20: Settings Page — Save Preferences

| Field | Details |
|-------|---------|
| **Objective** | Verify settings can be saved and persist |
| **Steps** | 1. Navigate to Settings 2. Change language to "zh" and units to "imperial" 3. Adjust default Time weight to 0.8 4. Tap **Save** 5. Navigate away, then return to Settings |
| **Expected Result** | Green success toast appears on save. On return, settings reflect the saved values (zh, imperial, Time=0.8). |

---

## TC21: Settings Page — Refresh Data Sources

| Field | Details |
|-------|---------|
| **Objective** | Verify cache refresh invalidates and re-fetches data |
| **Steps** | 1. Navigate to Settings 2. Note the current data source statuses 3. Tap the **Refresh** button |
| **Expected Result** | All caches are invalidated. Data sources table reloads. Sources that successfully re-fetch show "Live"; those that fail show "Fallback". |

---

## TC22: Risk Badges — Correct Categorisation

| Field | Details |
|-------|---------|
| **Objective** | Verify risk badges display the correct category and colour |
| **Steps** | 1. Perform a transit search 2. Observe crowding and delay badges on route cards and MapPage |
| **Expected Result** | Badges show "Low" (green), "Medium" (amber), or "High" (red) matching the backend assessment data. |

---

## TC23: API — Route Search Endpoint

| Field | Details |
|-------|---------|
| **Objective** | Verify `GET /routes` returns correct response structure |
| **Steps** | Send: `GET /routes?origin=Clementi&destination=Raffles+Place&include_transit=true&wt_time=0.5&wt_cost=0.2&wt_risk=0.2&wt_comfort=0.1` |
| **Expected Result** | 200 OK. Response contains `trip` (origin, destination, weights), `routes` (list of up to 5 RouteOption objects with time, cost, score, steps, crowding, delay fields). |

---

## TC24: API — Route Search with Constraints

| Field | Details |
|-------|---------|
| **Objective** | Verify constraint parameters filter results server-side |
| **Steps** | Send: `GET /routes?origin=NUS&destination=Changi+Airport&max_transfers=1&max_budget=3.0` |
| **Expected Result** | 200 OK. All returned routes have transfers <= 1 and cost <= $3.00. |

---

## TC25: API — Assessment Endpoint

| Field | Details |
|-------|---------|
| **Objective** | Verify `GET /assessment` returns segment-level risk data |
| **Steps** | Send: `GET /assessment?origin=Jurong+East&destination=Dhoby+Ghaut` |
| **Expected Result** | 200 OK. Response contains segment assessments with crowding levels, delay estimates, and bus frequency data per segment. |

---

## TC26: API — Crowding Heatmap Endpoint

| Field | Details |
|-------|---------|
| **Objective** | Verify `GET /crowding/heatmap` returns hourly crowding data |
| **Steps** | Send: `GET /crowding/heatmap?station_name=Orchard` |
| **Expected Result** | 200 OK. Response contains station name, line code, and intervals array with entries from 6 AM to 11 PM, each having a crowding level (l/m/h). |

---

## TC27: API — Settings Round-Trip

| Field | Details |
|-------|---------|
| **Objective** | Verify settings can be saved and loaded via API |
| **Steps** | 1. Send `PUT /settings` with body `{"language":"ta","units":"imperial","default_weights":{"time":0.4,"cost":0.3,"risk":0.2,"comfort":0.1}}` 2. Send `GET /settings` |
| **Expected Result** | PUT returns 200 with updated settings. GET returns the same values that were saved. |

---

## TC28: API — Cache Status and Refresh

| Field | Details |
|-------|---------|
| **Objective** | Verify dataset status reporting and cache invalidation |
| **Steps** | 1. Send `GET /datasets` — note statuses 2. Send `POST /refresh` 3. Send `GET /datasets` again |
| **Expected Result** | Initial GET shows cached data with timestamps. POST invalidates all caches. Second GET shows refreshed timestamps. Fallback flags update based on API availability. |

---

## TC29: API — Health Check

| Field | Details |
|-------|---------|
| **Objective** | Verify the health endpoint responds |
| **Steps** | Send: `GET /health` |
| **Expected Result** | 200 OK with a health status response. |

---

## TC30: Scoring Logic — Weighted Composite Score

| Field | Details |
|-------|---------|
| **Objective** | Verify scoring formula produces correct ranking |
| **Steps** | 1. Search with weights: Time=1.0, Cost=0.0, Risk=0.0, Comfort=0.0 2. Verify the fastest route has the lowest score 3. Repeat with Cost=1.0 (others 0.0) 4. Verify the cheapest route has the lowest score |
| **Expected Result** | Route with the best value in the weighted dimension always ranks first. Score = sum of (normalised_metric * weight). |

---

## TC31: Fallback Behaviour — API Failure

| Field | Details |
|-------|---------|
| **Objective** | Verify app uses cached fallback data when an external API is unavailable |
| **Preconditions** | Perform a search once (to populate cache), then simulate LTA API unavailability |
| **Steps** | 1. Perform a route search (cache populated) 2. Block LTA API access 3. Perform the same search again |
| **Expected Result** | Results still return using cached data. Backend message may include "Using fallback data". Settings page shows "Fallback" badge for affected data source. |

---

## TC32: ERP Cost Calculation (Driving Routes)

| Field | Details |
|-------|---------|
| **Objective** | Verify ERP gantry charges are included in driving route costs |
| **Steps** | 1. Search a driving route that passes through known ERP gantries (e.g., CTE during peak hours) 2. Check the cost breakdown |
| **Expected Result** | Route cost includes ERP toll charges. Explanation text mentions ERP if applicable. |

---

## TC33: Weather Integration

| Field | Details |
|-------|---------|
| **Objective** | Verify weather data is factored into route assessment |
| **Steps** | 1. Perform a route search 2. Check if weather information appears in route explanation or risk assessment |
| **Expected Result** | If adverse weather is forecast for the route area, it is reflected in the risk assessment or route explanation. |

---

## TC34: Parking Availability (Drive Mode)

| Field | Details |
|-------|---------|
| **Objective** | Verify nearby carpark availability is shown for driving routes |
| **Steps** | 1. Search a driving route to a destination with nearby HDB/URA carparks 2. Check route details |
| **Expected Result** | Carpark availability data is included in the route response. Available lots count shown. |

---

## TC35: Realistic Time Calculation

| Field | Details |
|-------|---------|
| **Objective** | Verify realistic time accounts for bus frequency and delays |
| **Steps** | 1. Search a transit route involving buses 2. Compare Google time vs Realistic time on the Scoring page |
| **Expected Result** | Realistic time >= Google time. The difference reflects added delay from bus frequency risk. Realistic time is highlighted amber on the Scoring page when it exceeds Google time. |

---

## TC36: Place Autocomplete (Geocoding)

| Field | Details |
|-------|---------|
| **Objective** | Verify location autocomplete suggestions appear while typing |
| **Steps** | 1. Click the origin field 2. Type "Clem" (at least 2 characters) |
| **Expected Result** | Dropdown suggestions appear from Nominatim API (e.g., "Clementi MRT Station", "Clementi Avenue 2"). Selecting a suggestion populates the field. |

---

## TC37: Bottom Navigation — Tab Switching

| Field | Details |
|-------|---------|
| **Objective** | Verify bottom navigation tabs switch between pages |
| **Steps** | 1. Tap **Home** tab 2. Tap **Results** tab 3. Tap **Scoring** tab 4. Tap **Settings** tab |
| **Expected Result** | Each tab navigates to the corresponding page. Active tab is visually highlighted. State is preserved when switching back. |

---

## TC38: Refresh Route Results

| Field | Details |
|-------|---------|
| **Objective** | Verify refreshing re-fetches routes with the same parameters |
| **Steps** | 1. Perform a search 2. On ResultsPage, tap the **Refresh** button |
| **Expected Result** | Spinner appears. Routes are re-fetched from the backend. Results update (scores/crowding may change if real-time data changed). |

---

## TC39: Google Maps Passthrough Endpoint

| Field | Details |
|-------|---------|
| **Objective** | Verify `GET /gmaps/directions` returns raw directions data |
| **Steps** | Send: `GET /gmaps/directions?origin=1.3,103.8&destination=1.35,103.85&mode=transit` |
| **Expected Result** | 200 OK. Response contains Google Maps directions data (routes, legs, steps). |

---

## TC40: Concurrent Constraint Combination

| Field | Details |
|-------|---------|
| **Objective** | Verify multiple constraints applied simultaneously work correctly |
| **Steps** | 1. Set Max Walk = 10 min, Max Transfers = 1, Max Budget = $2.00 2. Search for a route |
| **Expected Result** | Only routes satisfying ALL three constraints are returned. If no routes match all constraints, "No routes found" message is shown. |
