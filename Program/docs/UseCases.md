# 6. Use Case Descriptions

## 6.1 User Input Preference

### UC-01: Initialise Preferences on App Launch

| Field | Value |
|---|---|
| Use Case ID | UC-01 |
| Use Case Name | Initialise Preferences on App Launch |
| Actor | System |
| Description | When the user opens the application, the system loads any saved default preference weights from localStorage and initialises the search page. If no saved defaults exist, equal weights (0.25 each) are used. |
| Preconditions | User has opened the application |
| Postconditions | The search page is displayed with preference values loaded and the user can begin entering a trip request |
| Priority | High |
| Frequency of Use | Every app launch |
| Flow of Events | 1. User opens the application. 2. System reads saved default weights from localStorage (key: `sgtb-settings`). 3. If saved defaults exist, system initialises preference weights to the saved values (default_wt_time, default_wt_cost, default_wt_risk, default_wt_comfort). 4. If no saved defaults exist, system initialises weights to equal defaults (0.25 each). 5. System initialises route filtering constraints to no restriction (empty). 6. System enables both route categories (Public Transit and Taxi/Drive). 7. System displays the main search page with origin and destination input fields. |
| Alternative Flows | NIL |
| Exceptions | If localStorage is corrupted or unreadable, system falls back to equal defaults (0.25 each). |
| Includes | NIL |

---

### UC-02: Adjust Preferences for Current Search

| Field | Value |
|---|---|
| Use Case ID | UC-02 |
| Use Case Name | Adjust Preferences for Current Search |
| Actor | User |
| Description | Allows the user to expand the priorities and constraints section on the search page and adjust preference weights, route categories, and filtering constraints for the current search. Changes apply only to the current search and do not modify saved defaults. |
| Preconditions | User is on the search page (UC-01 completed) |
| Postconditions | The active preference configuration for the current search is updated |
| Priority | High |
| Frequency of Use | Medium |
| Flow of Events | 1. User taps "Show priorities & constraints" to expand the preferences section. 2. System displays four slider controls for Time, Cost, Risk, and Comfort (range 0.0-1.0, step 0.05), and three optional constraint fields (max walking minutes, max transfers, max budget). 3. User adjusts one or more priority weight sliders. The current value is displayed next to each slider. 4. User optionally enters a maximum walking allowance (minutes), maximum number of transfers, or maximum trip budget (SGD). Leaving a field empty indicates no restriction. 5. User optionally toggles route categories (Public Transit, Taxi/Drive). The system silently prevents disabling the last remaining category by reverting the toggle. 6. System applies the active preference configuration when the user initiates route search. 7. The system normalises the preference weights (dividing each by the sum of all weights) so they total 1.0 before applying to scoring. |
| Alternative Flows | User may collapse the section; the current active preferences remain in effect. |
| Exceptions | NIL |
| Includes | NIL |

---

## 6.2 Trip Request Input

### UC-03: Input Origin

| Field | Value |
|---|---|
| Use Case ID | UC-03 |
| Use Case Name | Input Origin |
| Actor | User |
| Description | Lets the user specify where their trip starts by typing an address. The system provides autocomplete suggestions from the OneMap API, which implicitly constrains results to Singapore. |
| Preconditions | User is on the search page |
| Postconditions | An origin location is entered in the origin field |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. User begins typing in the origin input field. 2. After a 300ms debounce delay and a minimum of 2 characters, the system queries the OneMap API for matching location suggestions (UC-05). 3. System displays a dropdown list of up to 5 matching suggestions. 4. User selects a suggestion to populate the origin field, or continues typing to refine suggestions. 5. The OneMap API only returns Singapore-based results, implicitly constraining the origin to Singapore. |
| Alternative Flows | NIL |
| Exceptions | If the OneMap API returns no results, no suggestions are displayed and the user may type a location manually. |
| Includes | UC-05 Generate Suggestions |

---

### UC-04: Input Destination

| Field | Value |
|---|---|
| Use Case ID | UC-04 |
| Use Case Name | Input Destination |
| Actor | User |
| Description | Lets the user specify where they want to go by typing an address. The system provides autocomplete suggestions from the OneMap API and validates the destination is not identical to the origin. |
| Preconditions | User is on the search page |
| Postconditions | A destination location is entered in the destination field |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. User begins typing in the destination input field. 2. After a 300ms debounce delay and a minimum of 2 characters, the system queries the OneMap API for matching location suggestions (UC-05). 3. System displays a dropdown list of up to 5 matching suggestions. 4. User selects a suggestion to populate the destination field, or continues typing to refine suggestions. 5. System checks that the destination is not identical to the origin (case-insensitive comparison). |
| Alternative Flows | NIL |
| Exceptions | If the destination matches the origin, the system displays "Origin and destination cannot be the same" and disables the Find Routes button. |
| Includes | UC-05 Generate Suggestions |

---

### UC-05: Generate Suggestions

| Field | Value |
|---|---|
| Use Case ID | UC-05 |
| Use Case Name | Generate Suggestions |
| Actor | System |
| Description | Provides autocomplete location suggestions from the OneMap API as the user types an origin or destination. Suggestions are debounced and refreshed as the input changes. |
| Preconditions | User is typing in the origin (UC-03) or destination (UC-04) input field with at least 2 characters |
| Postconditions | A list of matching location suggestions is displayed in a dropdown |
| Priority | Medium |
| Frequency of Use | High |
| Flow of Events | 1. User types at least 2 characters in a location input field. 2. System waits 300ms after the last keystroke (debounce). 3. System sends a request to the OneMap API with the input text. 4. OneMap returns matching Singapore locations with building name, block number, road name, postal code, and coordinates. 5. System parses results and displays up to 5 suggestions in a dropdown below the input field. 6. As the user modifies the text, the system re-queries and refreshes the suggestion list. 7. User selects a suggestion to populate the field. |
| Alternative Flows | If the input is fewer than 2 characters, the suggestion dropdown is hidden. |
| Exceptions | If the OneMap API is unreachable, suggestions fail silently and no dropdown is shown. |
| Includes | NIL |

---

### UC-06: Initiate Trip Request

| Field | Value |
|---|---|
| Use Case ID | UC-06 |
| Use Case Name | Initiate Trip Request |
| Actor | User |
| Description | The user enters an origin and destination on the search page, optionally adjusts preferences (UC-02), and initiates route search. The system validates inputs and passes them to route generation. |
| Preconditions | User is on the search page with preferences initialised (UC-01) |
| Postconditions | Validated trip inputs and active preferences are passed to route generation |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. User enters an origin location (UC-03). 2. User enters a destination location (UC-04). 3. User optionally swaps origin and destination using the swap button. 4. User optionally adjusts preferences for this search (UC-02). 5. System validates that: (a) origin has at least 2 characters, (b) destination has at least 2 characters, (c) origin and destination are not identical (case-insensitive), and (d) at least one route category is enabled. 6. System enables the "Find Routes" button when all validations pass. 7. User taps "Find Routes". 8. System passes the validated inputs (origin, destination, weights, modes, constraints) to route generation (UC-10). |
| Alternative Flows | NIL |
| Exceptions | If origin and destination are identical, system displays "Origin and destination cannot be the same" and disables the Find Routes button. |
| Includes | UC-02 Adjust Preferences, UC-03 Input Origin, UC-04 Input Destination |

---

## 6.3 Route Generation, Assessment, and Ranking

### UC-07: Collect and Validate Transport Data

| Field | Value |
|---|---|
| Use Case ID | UC-07 |
| Use Case Name | Collect and Validate Transport Data |
| Actor | System |
| Description | Gathers all real-time transport data needed for risk assessment and route generation. Uses a TTL-based in-memory cache with automatic freshness validation and fallback handling. If any data source is stale or unavailable, the system transparently substitutes the most recent cached data and marks affected elements as fallback. |
| Preconditions | Route generation has been triggered (UC-06 or UC-17) |
| Postconditions | All required transport data is collected, timestamped, and available for assessment. Affected elements are marked if fallback data was used. |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System identifies which data sources are needed based on the enabled route categories and route segments. 2. For each required source, system checks the in-memory TTL cache. If the cached entry is fresh (within its TTL threshold), it is used directly. 3. If the cache entry is expired or missing, system fetches fresh data from the external API: (a) LTA Bus Arrival API — bus crowding and arrival times (TTL: 30s); (b) LTA PCD Forecast — MRT station crowding by time interval (TTL: 600s); (c) LTA Train Service Alerts — MRT delay/disruption status (TTL: 60s); (d) LTA Traffic Speed Bands — road traffic congestion data (TTL: 300s); (e) LTA Carpark Availability — parking lot counts near destination (TTL: 300s); (f) NEA 2-Hour Weather Forecast — rain prediction along route. 4. Each response is stored in the cache with its retrieval timestamp. 5. If an API call fails, system falls back to the most recent cached data (even if expired) and marks it with `is_fallback = true` and `source = "fallback"`. If no cached data exists at all, an empty structure with `is_fallback = true` is used. 6. Different segments within the same route may independently use real-time or fallback data. If any segment uses fallback data, the route-level `uses_fallback` flag is set to true. 7. The Settings screen displays each data source status as "Live" (green) or "Fallback" (amber). |
| Alternative Flows | NIL |
| Exceptions | If an API is completely unreachable with no cached data, the system proceeds without that data source and flags the gap. |
| Includes | NIL |

---

### UC-08: Assess Crowding Risk

| Field | Value |
|---|---|
| Use Case ID | UC-08 |
| Use Case Name | Assess Crowding Risk |
| Actor | System |
| Description | Evaluates how crowded each public transport segment is likely to be, based on retrieved data. Each segment gets a Low, Medium, High, or Unknown crowding label. Driving segments are assigned Unknown (no crowding data for cars). |
| Preconditions | Transport data has been collected (UC-07) and routes have been generated (UC-10) |
| Postconditions | Segment-level and route-level crowding risk indicators are assigned |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. For each bus segment, system computes a crowding indicator from the LTA Bus Arrival API Load field: SEA (Seats Available) = Low, SDA (Standing Available) = Medium, LSD (Limited Standing) = High. 2. For each MRT segment, system computes a crowding indicator from the LTA PCD Forecast CrowdLevel field matched to the closest time interval: l/low = Low, m/moderate = Medium, h/high = High. 3. For driving/taxi segments, crowding is set to Unknown (not applicable). 4. If crowding data is unavailable for a segment, it is marked Unknown. 5. System aggregates segment-level values to a route-level crowding risk using a worst-case (maximum) rule: (a) if all segments are Unknown, the route is Unknown with numeric value 2; (b) if some are Unknown and some known, the route-level value is the maximum of the known values; (c) otherwise, the highest segment risk is used. 6. Route-level crowding risk is passed to UC-11 for scoring. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |

---

### UC-09: Assess Delay Risk

| Field | Value |
|---|---|
| Use Case ID | UC-09 |
| Use Case Name | Assess Delay Risk |
| Actor | System |
| Description | Evaluates the likelihood of delays on each route segment. For MRT segments, uses train service alerts. For driving/taxi segments, matches LTA Traffic Speed Bands along the route polyline. Bus segments default to Low. |
| Preconditions | Transport data has been collected (UC-07) and routes have been generated (UC-10) |
| Postconditions | Segment-level and route-level delay risk indicators are assigned |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. For each MRT segment, system computes a delay indicator from the LTA Train Service Alerts API: Status=1 (normal) = Low; Status=2 (disruption) on the route's line = High; Status=2 on a different line = Low; Status=2 with no specific line identified = Medium (precautionary). 2. For each bus segment, system assigns a default delay indicator of Low. 3. For each driving/taxi segment, system decodes the Google overview polyline, samples up to 20 evenly-spaced points along the route, and matches LTA Traffic Speed Bands within 500m of each sample point using a spatial grid index. The average SpeedBand value determines delay: band >= 4 (30+ km/h) = Low, band >= 2 (10-29 km/h) = Medium, band < 2 (0-9 km/h) = High. 4. If delay data is unavailable for a segment, it is marked Unknown. 5. System aggregates to route-level delay risk using the same worst-case rule as crowding (UC-08 step 5). 6. Route-level delay risk is passed to UC-11 for scoring. |
| Alternative Flows | If no polyline is available for a driving segment, system falls back to checking speed bands near the start and end coordinates only. |
| Exceptions | NIL |
| Includes | NIL |

---

### UC-10: Generate Routes

| Field | Value |
|---|---|
| Use Case ID | UC-10 |
| Use Case Name | Generate Routes |
| Actor | System |
| Description | Produces candidate route options from origin to destination using the Google Directions API for enabled transport modes. Applies user constraints, deduplicates routes, and assigns route attributes including cost estimation, weather, ERP charges, and parking availability. |
| Preconditions | Trip request inputs are validated (UC-06) and transport data is collected (UC-07) |
| Postconditions | A set of feasible, deduplicated candidate routes is generated with assigned attributes |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System reads the active preference configuration to determine which modes are enabled. 2. If Public Transit is enabled, system calls the Google Directions API with mode "transit" to generate public transit route options (may include MRT-only or MRT+Bus combinations). 3. If Taxi/Drive is enabled, system calls the Google Directions API with mode "driving". For each driving route, system generates two candidates: (a) a Taxi candidate (no parking penalty, CDG 2026 metered fare with surcharges) and (b) a Drive candidate (fuel cost, with parking penalties on time/comfort/risk from nearby carpark availability). 4. System deduplicates candidate routes by fingerprint (category + mode sequence + line names + stops), retaining the faster route when duplicates exist. 5. System filters out routes that violate the maximum walking allowance, maximum transfers, or maximum budget constraints. 6. For each feasible route, system assigns: estimated travel time (from Google API), realistic travel time (adding 0.5 * bus miss_penalty_min per bus step and parking search penalties), number of transfers (transit segments minus one), estimated cost, walking time, weather data (rain warnings from NEA), ERP charges (from polyline-gantry proximity matching), parking availability (from LTA Carpark API), and route-level risk indicators from UC-08 and UC-09. 7. Candidate routes are passed to UC-11 for scoring and UC-12 for ranking. |
| Alternative Flows | If no feasible routes remain after constraint filtering, the system returns an empty route list with the message "No routes found or API unavailable". |
| Exceptions | NIL |
| Includes | UC-08 Assess Crowding Risk, UC-09 Assess Delay Risk, UC-11 Generate Scores, UC-12 Rank Routes |

---

### UC-11: Generate Scores

| Field | Value |
|---|---|
| Use Case ID | UC-11 |
| Use Case Name | Generate Scores |
| Actor | System |
| Description | Computes composite scores for each candidate route by combining normalised route attributes with the user's preference weights across four dimensions: Time, Cost, Risk, and Comfort. Lower score = better route. |
| Preconditions | Routes have been generated (UC-10) with assigned attributes and risk indicators from UC-08 and UC-09 |
| Postconditions | Each candidate route has a composite score ready for ranking |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System computes a combined Risk score for each route: risk_num = max(crowding_numeric, delay_numeric), producing a value on the 1-3 scale. 2. System computes a Comfort score for each route: comfort = 0.6 * walk_score + 0.4 * transfer_score, where walk_score is capped at 30 minutes (normalised to 0-10 range) and transfer_score is capped at 5 transfers (normalised to 0-10 range). 3. System applies min-max normalisation across all candidate routes for each of the four dimensions (time uses realistic_time_min, cost, risk, comfort). If all routes share the same value for an attribute, the normalised value is set to 0.0 for all. 4. System retrieves the user's preference weights and normalises them so they sum to 1.0. 5. System computes the composite score: Score = w_T * T' + w_B * B' + w_R * R' + w_F * F'. 6. Scores are attached to each route and passed to UC-12 for ranking. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |

---

### UC-12: Rank Routes

| Field | Value |
|---|---|
| Use Case ID | UC-12 |
| Use Case Name | Rank Routes |
| Actor | System |
| Description | Sorts all candidate routes from best to worst based on composite scores. Uses a multi-level tie-breaker when scores are equal and ensures category diversity in the final selection. |
| Preconditions | Composite scores have been computed for all candidate routes (UC-11) |
| Postconditions | Up to 5 routes are selected for display with category diversity |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System sorts all candidate routes in ascending order of composite score (lowest = best). 2. If two or more routes tie on composite score, system applies the following tie-breaking sequence: (a) lower combined risk numeric value, (b) lower comfort numeric value, (c) shorter travel time, (d) lower cost. 3. System selects up to 5 routes for presentation, ensuring category diversity: first the best route from each category (Public Transit, Taxi, Drive), then filling remaining slots with the next-best overall routes. 4. Final selection is re-sorted by score. 5. System generates a brief explanation for each route (UC-13). 6. Ranked routes are passed to UC-14 for display. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-13 Generate Route Explanation, UC-14 Display Routes |

---

### UC-13: Generate Route Explanation

| Field | Value |
|---|---|
| Use Case ID | UC-13 |
| Use Case Name | Generate Route Explanation |
| Actor | System |
| Description | Creates a brief, human-readable explanation for each route, referencing the user's highest-weighted criterion, per-step crowding highlights, walking time, and any fallback data warnings. |
| Preconditions | Routes have been scored and ranked (UC-11, UC-12) |
| Postconditions | Each route has a brief explanation attached for display |
| Priority | Medium |
| Frequency of Use | High |
| Flow of Events | 1. System identifies the user's highest-weighted preference criterion. 2. For each route, system generates an explanation based on that criterion: Time = "Fastest option at {X} min"; Cost = "Cheapest at ${X}"; Risk = "Lowest risk: {category}"; Comfort = "Most comfortable: {X} min walk, {Y} transfer(s)". 3. System appends per-step crowding highlights where available (e.g., "Crowded: Bus 143" or "Not crowded: MRT NSL"). 4. System appends total walking time (e.g., "{X} min walking"). 5. If any risk indicator used fallback data, the notation "(some data is estimated)" is appended. 6. The explanation is attached to the route for display in UC-14. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |

---

## 6.4 Route Display and Interaction

### UC-14: Display Routes

| Field | Value |
|---|---|
| Use Case ID | UC-14 |
| Use Case Name | Display Routes |
| Actor | System |
| Description | Presents the final ranked route options to the user with travel times, costs, risk levels, step-by-step details, weather warnings, ERP charges, parking status, bus frequency, and explanations. |
| Preconditions | Routes have been ranked (UC-12) and explanations generated (UC-13) |
| Postconditions | The user can see and compare the recommended route options |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System displays up to 5 ranked route options (or fewer if limited feasible routes exist). 2. Each route card shows: category (Public Transit / Taxi / Drive), estimated and realistic travel time, number of transfers, estimated cost with breakdown, walking time, route-level crowding risk badge, and route-level delay risk badge. 3. Each route includes its one-line explanation from UC-13. 4. Each route shows step-by-step details (Walk / Bus / Train segments with line names, stop counts, and per-step crowding indicators). 5. For Taxi/Drive routes, ERP charges and gantry details are shown in the fare breakdown. 6. For Drive routes, parking availability status and time penalties are displayed. 7. Weather data (rain warnings) are shown inline when applicable. 8. Low-frequency bus warnings are shown inline when bus headway exceeds threshold. 9. Routes using fallback data display the notation "(some data is estimated)". 10. If no routes were found, system shows a message and prompts the user to modify constraints or search again. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |

---

### UC-15: Select Route on Map

| Field | Value |
|---|---|
| Use Case ID | UC-15 |
| Use Case Name | Select Route on Map |
| Actor | User |
| Description | Allows the user to tap a route card to select it. The selected route is highlighted on the interactive map with a colour-coded polyline showing each segment (walk, bus, train, drive). |
| Preconditions | Routes have been displayed (UC-14) |
| Postconditions | The selected route is visually highlighted on the map and the route card is marked as selected |
| Priority | Medium |
| Frequency of Use | High |
| Flow of Events | 1. User taps a route card from the displayed list. 2. System marks the tapped card as selected (amber highlight). 3. System decodes the route's overview polyline and renders it on the Leaflet map overlay. 4. The polyline is colour-coded by segment mode (Walk = dashed, Bus/Train/Drive = solid, coloured by transport line). 5. Map auto-fits bounds to show the full selected route. 6. Step labels and transfer points are shown along the route on the map. |
| Alternative Flows | User taps a different route card to switch the selected route. |
| Exceptions | NIL |
| Includes | NIL |

---

### UC-16: View Scoring Breakdown

| Field | Value |
|---|---|
| Use Case ID | UC-16 |
| Use Case Name | View Scoring Breakdown |
| Actor | User |
| Description | Allows the user to view a detailed breakdown of how each route was scored across the four dimensions (Time, Cost, Risk, Comfort), including normalised values, weighted contributions, and the composite score calculation. |
| Preconditions | Routes have been generated and displayed (UC-14) |
| Postconditions | The user can see the detailed scoring analysis for all routes |
| Priority | Medium |
| Frequency of Use | Medium |
| Flow of Events | 1. User navigates to the Scoring tab via the bottom navigation bar. 2. System displays the active preference weights for the current search. 3. System displays a comparison table showing all routes with their normalised dimension values and composite scores. 4. For each route, system shows the weighted contribution of each dimension to the final score. 5. System displays an educational section explaining the 5-step scoring process (attribute assignment, risk quantification, normalisation, weighted scoring, ranking). 6. For routes containing MRT segments, system displays per-station crowding heatmaps (UC-18). |
| Alternative Flows | If no routes have been generated yet, system prompts the user to search for routes first. |
| Exceptions | NIL |
| Includes | UC-18 View Crowding Heatmap |

---

### UC-17: Refresh Routes

| Field | Value |
|---|---|
| Use Case ID | UC-17 |
| Use Case Name | Refresh Routes |
| Actor | User |
| Description | Allows the user to manually re-fetch transport data and regenerate routes, ensuring recommendations reflect the latest conditions. |
| Preconditions | Routes have already been generated and displayed for the current trip |
| Postconditions | Route recommendations are regenerated using the most recent transport data |
| Priority | Medium |
| Frequency of Use | Low to Medium |
| Flow of Events | 1. User taps the refresh button on the results page or main view. 2. System re-initiates route generation (UC-10) using the same search parameters (origin, destination, weights, modes, constraints). 3. System fetches fresh data from all external APIs, bypassing any stale cache entries. 4. Updated routes replace the previous results on screen. |
| Alternative Flows | User may also refresh from the Settings screen, which invalidates all cached data via the /refresh endpoint without regenerating routes. |
| Exceptions | NIL |
| Includes | UC-10 Generate Routes |

---

### UC-18: View Crowding Heatmap

| Field | Value |
|---|---|
| Use Case ID | UC-18 |
| Use Case Name | View Crowding Heatmap |
| Actor | User |
| Description | Displays a per-station MRT crowding heatmap (6 AM - 11 PM) showing expected crowd levels throughout the day, colour-coded by Low (green), Medium (amber), and High (red). |
| Preconditions | Routes containing MRT segments have been generated, and the user is on the Scoring tab (UC-16) |
| Postconditions | The user can see hourly crowding predictions for each MRT station on their route |
| Priority | Medium |
| Frequency of Use | Medium |
| Flow of Events | 1. System identifies all MRT stations from the route steps. 2. For each station, system calls the /crowding/heatmap endpoint with the station name. 3. Backend looks up the station code and train line, then retrieves the LTA PCD Forecast for that line. 4. Backend extracts half-hourly CrowdLevel intervals for the station and returns them. 5. Frontend renders a horizontal bar chart with hourly blocks colour-coded by crowd level. |
| Alternative Flows | NIL |
| Exceptions | If the station is not found in the lookup table or PCD data is unavailable, the heatmap is not displayed for that station. |
| Includes | NIL |

---

### UC-19: Compare Departure Times

| Field | Value |
|---|---|
| Use Case ID | UC-19 |
| Use Case Name | Compare Departure Times |
| Actor | User |
| Description | Allows the user to compare route options across different departure time windows (Morning Rush, Around Now, Evening Rush) to find the optimal time to travel. |
| Preconditions | Routes have been generated and displayed (UC-14) |
| Postconditions | The user can see route scores and attributes across 9 departure time slots |
| Priority | Medium |
| Frequency of Use | Low to Medium |
| Flow of Events | 1. User taps the "Compare Times" button on the results page. 2. System opens a modal dialog and calls the /routes/compare endpoint with the current origin, destination, and weight preferences. 3. Backend generates routes for 9 time slots across 3 groups: Morning Rush (07:30, 08:00, 08:30), Around Now (current time, +30 min, +60 min), and Evening Rush (17:30, 18:00, 18:30). 4. For each time slot, backend returns the top 3 ranked routes with their scores, times, costs, and crowding levels. 5. Frontend displays the results as a grouped comparison table. 6. User reviews the comparison and closes the modal. |
| Alternative Flows | NIL |
| Exceptions | If the backend is unreachable, the modal shows an error message. |
| Includes | NIL |

---

## 6.5 Settings

### UC-20: Change Settings

| Field | Value |
|---|---|
| Use Case ID | UC-20 |
| Use Case Name | Change Settings |
| Actor | User |
| Description | Lets the user update app-level settings including display language and default preference weights. Changes are persisted to localStorage and optionally synced to the backend. The Settings screen also shows data source status and provides a cache refresh option. |
| Preconditions | User navigates to the Settings screen |
| Postconditions | Modified settings are saved and applied |
| Priority | Medium |
| Frequency of Use | Low |
| Flow of Events | 1. User opens the Settings screen. 2. System displays current settings: display language (English, Chinese, Malay, Tamil) and default preference weight sliders (Time, Cost, Risk, Comfort, range 0.0-1.0, step 0.05). 3. User modifies one or more settings. 4. If the user changes the display language, system applies the selected language to all user-facing text via the i18n framework immediately on save. 5. If the user edits default preference weights, system updates the slider values. 6. User taps Save. 7. System writes the settings to localStorage (key: sgtb-settings) and the language separately (key: sgtb-lang). 8. System optionally syncs settings to the backend via PUT /settings. 9. System confirms the save was successful. The saved default weights will be loaded on the next app launch (UC-01). |
| Alternative Flows | If backend sync fails, the localStorage save is still considered successful. |
| Exceptions | NIL |
| Includes | NIL |
| Notes and Issues | The Settings screen also displays the status of each data source (Live or Fallback) and provides a cache refresh button that invalidates all cached data via the /refresh endpoint. When the backend is not running, the data sources section shows "Backend is not running". |
