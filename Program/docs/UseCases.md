# 6. Use Case Descriptions

## 6.1 User Input Preference

### UC-01: Initialise Preferences on App Launch

| Field | Value |
|---|---|
| Use Case ID | UC-01 |
| Use Case Name | Initialise Preferences on App Launch |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | When the user opens the application, the system initialises the search page with default preference weights (0.25 each for Time, Cost, Risk, Comfort), no active constraints, and both route categories enabled (Public Transit + Taxi/Drive). |
| Preconditions | User has opened the application |
| Postconditions | The search page is displayed with default preference values and the user can immediately begin entering a trip request |
| Priority | High |
| Frequency of Use | Every app launch |
| Flow of Events | 1. User opens the application. 2. System initialises preference weights to equal defaults (Time=0.25, Cost=0.25, Risk=0.25, Comfort=0.25). 3. System initialises route filtering constraints to no restriction (empty). 4. System enables both route categories (Public Transit and Taxi/Drive). 5. System displays the main search page with the origin and destination input fields. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-02: Adjust Preferences for Current Search

| Field | Value |
|---|---|
| Use Case ID | UC-02 |
| Use Case Name | Adjust Preferences for Current Search |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
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
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-03: Modify Default Preferences in Settings

| Field | Value |
|---|---|
| Use Case ID | UC-03 |
| Use Case Name | Modify Default Preferences in Settings |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | User |
| Description | Lets the user update saved default preference weight values through the Settings screen. Changes are persisted for future sessions via UC-04. |
| Preconditions | User navigates to the Settings screen |
| Postconditions | Updated default preference weights are ready to be persisted via UC-04 |
| Priority | Medium |
| Frequency of Use | Low |
| Flow of Events | 1. User navigates to the Settings screen. 2. System displays the current default preference weight values as four sliders (range 0.0-1.0, step 0.05). 3. User adjusts one or more weight sliders. 4. User taps Save. 5. System triggers UC-04 to persist the updated defaults. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-04 Save Settings |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | Default weights in Settings are stored separately from the search page weights and serve as a record of preferred defaults. |

---

### UC-04: Save Settings

| Field | Value |
|---|---|
| Use Case ID | UC-04 |
| Use Case Name | Save Settings |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Persists the user's updated settings (language, default preference weights) to localStorage and optionally syncs to the backend. |
| Preconditions | Settings have been modified and validated (UC-03 or UC-27) |
| Postconditions | Updated settings are saved in localStorage (key: `sgtb-settings`) and optionally in backend `settings.json` |
| Priority | High |
| Frequency of Use | Every time settings are changed |
| Flow of Events | 1. System receives the validated settings data. 2. System writes the settings to localStorage under the key `sgtb-settings`. 3. System separately stores the selected language under the key `sgtb-lang`. 4. System optionally syncs settings to the backend via `PUT /settings`, which writes to `settings.json`. 5. System confirms the save was successful to the user. |
| Alternative Flows | If backend sync fails, the localStorage save is still considered successful. |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

## 6.2 Trip Request Input

### UC-05: Initiate Trip Request

| Field | Value |
|---|---|
| Use Case ID | UC-05 |
| Use Case Name | Initiate Trip Request |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | User |
| Description | The user enters an origin and destination on the search page, optionally adjusts preferences (UC-02), and initiates route search. The system validates inputs and passes them to route generation. |
| Preconditions | User is on the search page with default preferences initialised (UC-01) |
| Postconditions | Validated trip inputs and active preferences are passed to route generation |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. User enters an origin location (UC-08). 2. User enters a destination location (UC-09). 3. User optionally adjusts preferences for this search (UC-02). 4. System validates that: (a) origin has at least 2 characters, (b) destination has at least 2 characters, (c) origin and destination are not identical (case-insensitive), and (d) at least one route category is enabled. 5. System enables the "Find Routes" button when all validations pass. 6. User taps "Find Routes". 7. System passes the validated inputs (origin, destination, weights, modes, constraints) to route generation (UC-23). |
| Alternative Flows | User may swap origin and destination using the swap button. After swapping, the system revalidates inputs automatically. |
| Exceptions | If origin and destination are identical, system displays "Origin and destination cannot be the same" and disables the Find Routes button. |
| Includes | UC-02 Adjust Preferences, UC-08 Input Origin, UC-09 Input Destination |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-08: Input Origin

| Field | Value |
|---|---|
| Use Case ID | UC-08 |
| Use Case Name | Input Origin |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | User |
| Description | Lets the user specify where their trip starts by typing an address. The system provides autocomplete suggestions from the OneMap API, which implicitly constrains results to Singapore. |
| Preconditions | User is on the search page |
| Postconditions | An origin location is entered in the origin field |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. User begins typing in the origin input field. 2. After a 300ms debounce delay and a minimum of 2 characters, the system queries the OneMap API for matching location suggestions (UC-12). 3. System displays a dropdown list of up to 5 matching suggestions. 4. User selects a suggestion to populate the origin field, or continues typing to refine suggestions. 5. The OneMap API only returns Singapore-based results, implicitly constraining the origin to Singapore. |
| Alternative Flows | NIL |
| Exceptions | If the OneMap API returns no results, no suggestions are displayed and the user may type a location manually. |
| Includes | UC-12 Generate Suggestions |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-09: Input Destination

| Field | Value |
|---|---|
| Use Case ID | UC-09 |
| Use Case Name | Input Destination |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | User |
| Description | Lets the user specify where they want to go by typing an address. The system provides autocomplete suggestions from the OneMap API and validates the destination is not identical to the origin. |
| Preconditions | User is on the search page |
| Postconditions | A destination location is entered in the destination field |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. User begins typing in the destination input field. 2. After a 300ms debounce delay and a minimum of 2 characters, the system queries the OneMap API for matching location suggestions (UC-12). 3. System displays a dropdown list of up to 5 matching suggestions. 4. User selects a suggestion to populate the destination field, or continues typing to refine suggestions. 5. System checks that the destination is not identical to the origin (case-insensitive comparison). |
| Alternative Flows | NIL |
| Exceptions | If the destination matches the origin, the system displays "Origin and destination cannot be the same" and disables the Find Routes button. |
| Includes | UC-12 Generate Suggestions |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-12: Generate Suggestions

| Field | Value |
|---|---|
| Use Case ID | UC-12 |
| Use Case Name | Generate Suggestions |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Provides autocomplete location suggestions from the OneMap API as the user types an origin or destination. Suggestions are debounced and refreshed as the input changes. |
| Preconditions | User is typing in the origin (UC-08) or destination (UC-09) input field with at least 2 characters |
| Postconditions | A list of matching location suggestions is displayed in a dropdown |
| Priority | Medium |
| Frequency of Use | High |
| Flow of Events | 1. User types at least 2 characters in a location input field. 2. System waits 300ms after the last keystroke (debounce). 3. System sends a request to the OneMap API (`/api/common/elastic/search`) with the input text. 4. OneMap returns matching Singapore locations with building name, block number, road name, postal code, and coordinates. 5. System parses results and displays up to 5 suggestions in a dropdown below the input field. 6. As the user modifies the text, the system re-queries and refreshes the suggestion list. 7. User selects a suggestion to populate the field. |
| Alternative Flows | If the input is fewer than 2 characters, the suggestion dropdown is hidden. |
| Exceptions | If the OneMap API is unreachable, suggestions fail silently and no dropdown is shown. |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

## 6.3 Route Generation and Assessment

### UC-14: Refresh Routes

| Field | Value |
|---|---|
| Use Case ID | UC-14 |
| Use Case Name | Refresh Routes |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | User |
| Description | Allows the user to manually re-fetch transport data and regenerate routes, ensuring recommendations reflect the latest conditions. |
| Preconditions | Routes have already been generated and displayed for the current trip |
| Postconditions | Route recommendations are regenerated using the most recent transport data |
| Priority | Medium |
| Frequency of Use | Low to Medium |
| Flow of Events | 1. User taps the refresh button on the results page or main view. 2. System re-initiates route generation (UC-23) using the same search parameters (origin, destination, weights, modes, constraints). 3. System fetches fresh data from all external APIs, bypassing any stale cache entries. 4. Updated routes replace the previous results on screen. |
| Alternative Flows | User may also refresh from the Settings screen, which invalidates all cached data via the `/refresh` endpoint without regenerating routes. |
| Exceptions | NIL |
| Includes | UC-23 Generate Routes |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-15: Collect Data

| Field | Value |
|---|---|
| Use Case ID | UC-15 |
| Use Case Name | Collect Data |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Gathers all real-time transport data needed for risk assessment and route generation. Uses a TTL-based in-memory cache and triggers fallback handling if any data source is stale or unavailable. |
| Preconditions | Route generation has been triggered (UC-05 or UC-14) |
| Postconditions | All required transport data is collected, timestamped, and flagged for freshness compliance |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System identifies which data sources are needed based on the enabled route categories and the route segments returned by Google Directions. 2. System calls UC-16 to retrieve real-time data from external APIs via the TTL cache. 3. The cache layer timestamps each data source upon retrieval. 4. System calls UC-17 to validate freshness of each cached source against its predefined TTL threshold. 5. If any source fails freshness checks or is unavailable, system triggers fallback handling (UC-18). 6. System packages the collected data for use in segment assessment and route generation. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-16 Retrieve Real-Time Data, UC-17 Validate Data Freshness |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-16: Retrieve Real-Time Data

| Field | Value |
|---|---|
| Use Case ID | UC-16 |
| Use Case Name | Retrieve Real-Time Data |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Fetches live transport data from external APIs. Each response is cached with a retrieval timestamp and TTL. |
| Preconditions | Data collection has been initiated (UC-15) |
| Postconditions | Raw real-time transport data is returned with retrieval timestamps |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System sends requests to the relevant external transport data APIs: (a) LTA Bus Arrival API for bus crowding (Load: SEA/SDA/LSD) and next bus arrival times; (b) LTA PCD Forecast for MRT station crowding by time interval; (c) LTA Train Service Alerts for MRT delay/disruption status; (d) LTA Traffic Speed Bands for driving congestion data; (e) LTA Carpark Availability for parking lot counts near the destination (if Taxi/Drive enabled); (f) NEA 2-Hour Weather Forecast for rain prediction along the route. 2. Each response is stored in the in-memory TTL cache with its retrieval timestamp. 3. Cached data is passed back to UC-15. |
| Alternative Flows | NIL |
| Exceptions | If an API is unreachable, the system returns an empty data structure with `is_fallback = true` and proceeds with available data. |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-17: Validate Data Freshness

| Field | Value |
|---|---|
| Use Case ID | UC-17 |
| Use Case Name | Validate Data Freshness |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Checks whether each cached data source is fresh enough to use by comparing elapsed time since retrieval against predefined TTL thresholds. |
| Preconditions | Real-time data has been retrieved and cached (UC-16) |
| Postconditions | Each data source is classified as fresh or outdated; outdated sources are sent to fallback |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System checks each cached data source against its TTL threshold: Bus Arrival (30s), PCD Forecast (600s), Train Service Alerts (60s), Traffic Speed Bands (300s), Carpark Availability (300s), Taxi Availability (60s). 2. If `time.time() - retrieved_at <= ttl_sec`, the source is marked as fresh. 3. If the TTL is exceeded, the source is flagged as outdated. 4. Outdated sources trigger UC-18 (Apply Fallback Handling). |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-18: Apply Fallback Handling

| Field | Value |
|---|---|
| Use Case ID | UC-18 |
| Use Case Name | Apply Fallback Handling |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Substitutes the most recent cached data when live data is unavailable or stale. Different segments within the same route may independently use real-time or fallback data. |
| Preconditions | One or more data sources have been flagged as unavailable or outdated (UC-17) |
| Postconditions | Fallback data is in place and affected elements are marked accordingly (UC-19) |
| Priority | High |
| Frequency of Use | Low to Medium |
| Flow of Events | 1. System identifies which data sources need fallback substitution. 2. System retrieves the most recent available cached data for each affected source. 3. If no cached data exists for a source, system uses an empty data structure. 4. System calls UC-19 to mark all affected data elements as operating in fallback mode. 5. Fallback data is fed into assessment and route generation alongside any fresh data. |
| Alternative Flows | NIL |
| Exceptions | If no cached data is available at all for a source, the system proceeds without it and flags the gap with `is_fallback = true`. |
| Includes | UC-19 Mark Fallback Handling |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | Different segments within the same route may independently use real-time or fallback data. There is no prevention of partial mixing within a route. If any segment uses fallback data, the route-level `uses_fallback` flag is set to true. |

---

### UC-19: Mark Fallback Handling

| Field | Value |
|---|---|
| Use Case ID | UC-19 |
| Use Case Name | Mark Fallback Handling |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Tags data elements and route recommendations that were computed using fallback data, so downstream processes and the user can see which results may be less accurate. |
| Preconditions | Fallback data has been applied (UC-18) |
| Postconditions | All affected data elements and route outputs carry a fallback indicator |
| Priority | Medium |
| Frequency of Use | Low to Medium |
| Flow of Events | 1. System sets `is_fallback = true` and `source = "fallback"` on each affected `RiskIndicator`. 2. At the route level, if any segment uses fallback data, the `uses_fallback` flag is set to true. 3. When route explanations are generated (UC-24), fallback-affected routes include the notation "(some data is estimated)". 4. The Settings screen displays each data source status as "Live" (green badge) or "Fallback" (amber badge). |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-20: Generate Scores

| Field | Value |
|---|---|
| Use Case ID | UC-20 |
| Use Case Name | Generate Scores |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Computes composite scores for each candidate route by combining normalised route attributes with the user's preference weights across four dimensions: Time, Cost, Risk, and Comfort. Lower score = better route. |
| Preconditions | Routes have been generated (UC-23) with assigned attributes, and risk indicators are available from UC-21 and UC-22 |
| Postconditions | Each candidate route has a composite score ready for ranking |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System computes a combined Risk score for each route: `risk_num = max(crowding_numeric, delay_numeric)`, producing a value on the 1-3 scale. 2. System computes a Comfort score for each route: `comfort = 0.6 * walk_score + 0.4 * transfer_score`, where walk_score is capped at 30 minutes (normalised to 0-10 range) and transfer_score is capped at 5 transfers (normalised to 0-10 range). 3. System applies min-max normalisation across all candidate routes for each of the four dimensions (time, cost, risk, comfort). If all routes share the same value for an attribute, the normalised value is set to 0.0 for all. 4. System retrieves the user's preference weights and normalises them so they sum to 1.0. 5. System computes the composite score: `Score = w_T * T' + w_B * B' + w_R * R' + w_F * F'`. 6. Scores are attached to each route and passed to UC-25 for ranking. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-21 Assess Crowding Risk, UC-22 Assess Delay Risk |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-21: Assess Crowding Risk

| Field | Value |
|---|---|
| Use Case ID | UC-21 |
| Use Case Name | Assess Crowding Risk |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Evaluates how crowded each public transport segment is likely to be, based on retrieved data. Each segment gets a Low, Medium, High, or Unknown crowding label. |
| Preconditions | Transport data has been collected (UC-15) and routes have been generated (UC-23) |
| Postconditions | Segment-level and route-level crowding risk indicators are assigned |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. For each bus segment, system computes a crowding indicator from the LTA Bus Arrival API `Load` field: SEA (Seats Available) = Low, SDA (Standing Available) = Medium, LSD (Limited Standing) = High. 2. For each MRT segment, system computes a crowding indicator from the LTA PCD Forecast `CrowdLevel` field matched to the closest time interval: "l"/"low" = Low, "m"/"moderate" = Medium, "h"/"high" = High. 3. If crowding data is unavailable for a segment, it is marked Unknown. 4. System aggregates segment-level values to a route-level crowding risk using a worst-case (maximum) rule: (a) if all segments are Unknown, the route is Unknown with numeric value 2; (b) if some segments are Unknown and some are known, the route-level value is the maximum of the known values; (c) otherwise, the highest segment risk is used. 5. Route-level crowding risk is passed to UC-20 for scoring. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-22: Assess Delay Risk

| Field | Value |
|---|---|
| Use Case ID | UC-22 |
| Use Case Name | Assess Delay Risk |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Evaluates the likelihood of delays on each route segment based on service status and traffic data. Each segment gets a Low, Medium, High, or Unknown delay label. |
| Preconditions | Transport data has been collected (UC-15) and routes have been generated (UC-23) |
| Postconditions | Segment-level and route-level delay risk indicators are assigned |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. For each MRT segment, system computes a delay indicator from the LTA Train Service Alerts API: Status=1 (normal) = Low; Status=2 (disruption) on the route's line = High; Status=2 on a different line = Low; Status=2 with no specific line identified = Medium (precautionary). 2. For each bus segment, system assigns a default delay indicator of Low. 3. For each driving/taxi segment, system computes a delay indicator from the LTA Traffic Speed Bands API based on average speed near the route: average speed >= 6 = Low, >= 3 = Medium, < 3 = High. 4. If delay data is unavailable for a segment, it is marked Unknown. 5. System aggregates to route-level delay risk using the same worst-case rule as crowding (UC-21 step 4). 6. Route-level delay risk is passed to UC-20 for scoring. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-23: Generate Routes

| Field | Value |
|---|---|
| Use Case ID | UC-23 |
| Use Case Name | Generate Routes |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Produces candidate route options from origin to destination using the Google Directions API for enabled transport modes. Applies user constraints, deduplicates routes, and assigns route attributes including cost estimation. |
| Preconditions | Trip request inputs are validated (UC-05) and transport data is collected (UC-15) |
| Postconditions | A set of feasible, deduplicated candidate routes is generated with assigned attributes |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System reads the active preference configuration to determine which modes are enabled. 2. If Public Transit is enabled, system calls the Google Directions API with mode "transit" to generate public transit route options (may include MRT-only or MRT+Bus combinations). 3. If Taxi/Drive is enabled, system calls the Google Directions API with mode "driving". For each driving route, system generates two candidates: (a) a Taxi candidate (no parking penalty) and (b) a Drive candidate (with parking time/comfort penalties based on nearby carpark availability). 4. System deduplicates candidate routes by fingerprint (category + mode sequence + line names + stops), retaining the faster route when duplicates exist. 5. System filters out routes that violate the maximum walking allowance, maximum transfers, or maximum budget constraints. 6. For each feasible route, system assigns: estimated travel time (from Google API), realistic travel time (adding 0.5 * bus miss_penalty_min per bus step), number of transfers (transit segments minus one), estimated cost (transit fare table / CDG 2026 taxi metered fare with surcharges / fuel at $0.12/km + ERP charges), walking time, and route-level risk indicators from UC-21 and UC-22. 7. For Drive routes, system adds parking search time penalty (+10 min if full, +5 min if limited) and inflates walking time (+5 min if full, +2 min if limited). 8. Candidate routes are passed to UC-20 for scoring and UC-25 for ranking. |
| Alternative Flows | If no feasible routes remain after constraint filtering, the system returns an empty route list with the message "No routes found or API unavailable". |
| Exceptions | NIL |
| Includes | UC-24 Generate Route Explanation, UC-25 Rank Routes |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-24: Generate Route Explanation

| Field | Value |
|---|---|
| Use Case ID | UC-24 |
| Use Case Name | Generate Route Explanation |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Creates a brief, human-readable explanation for each route, referencing the user's highest-weighted criterion, per-step crowding highlights, walking time, and any fallback data warnings. |
| Preconditions | Routes have been scored and ranked (UC-20, UC-25) |
| Postconditions | Each route has a brief explanation attached for display |
| Priority | Medium |
| Frequency of Use | High |
| Flow of Events | 1. System identifies the user's highest-weighted preference criterion. 2. For each route, system generates an explanation based on that criterion: Time = "Fastest option at {X} min"; Cost = "Cheapest at ${X}"; Risk = "Lowest risk: {category}"; Comfort = "Most comfortable: {X} min walk, {Y} transfer(s)". 3. System appends per-step crowding highlights where available (e.g., "Crowded: Bus 143" or "Not crowded: MRT NSL"). 4. System appends total walking time (e.g., "{X} min walking"). 5. If any risk indicator used fallback data, the notation "(some data is estimated)" is appended. 6. The explanation is attached to the route for display in UC-26. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | NIL |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-25: Rank Routes

| Field | Value |
|---|---|
| Use Case ID | UC-25 |
| Use Case Name | Rank Routes |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Sorts all candidate routes from best to worst based on composite scores. Uses a multi-level tie-breaker when scores are equal and ensures category diversity in the final selection. |
| Preconditions | Composite scores have been computed for all candidate routes (UC-20) |
| Postconditions | Up to 5 routes are selected for display with category diversity |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System sorts all candidate routes in ascending order of composite score (lowest = best). 2. If two or more routes tie on composite score, system applies the following tie-breaking sequence: (a) lower combined risk numeric value, (b) lower comfort numeric value, (c) shorter travel time, (d) lower cost. 3. System selects up to 5 routes for presentation, ensuring category diversity: first the best route from each category (Public Transit, Taxi, Drive), then filling remaining slots with the next-best overall routes. 4. Final selection is re-sorted by score. 5. Ranked routes are passed to UC-26 for display. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-26 Display Routes |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | NIL |

---

### UC-26: Display Routes

| Field | Value |
|---|---|
| Use Case ID | UC-26 |
| Use Case Name | Display Routes |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | System |
| Description | Presents the final ranked route options to the user with travel times, costs, risk levels, step-by-step details, weather warnings, ERP charges, parking status, and explanations. |
| Preconditions | Routes have been ranked (UC-25) and explanations generated (UC-24) |
| Postconditions | The user can see and compare the recommended route options |
| Priority | High |
| Frequency of Use | High |
| Flow of Events | 1. System displays up to 5 ranked route options (or fewer if limited feasible routes exist). 2. Each route card shows: category (Public Transit / Taxi / Drive), estimated travel time, realistic travel time, number of transfers, estimated cost with breakdown, walking time, route-level crowding risk badge, and route-level delay risk badge. 3. Each route includes its one-line explanation from UC-24. 4. Each route shows step-by-step details (Walk / Bus / Train segments with line names, stop counts, and per-step crowding indicators). 5. Routes include weather data (rain warnings), ERP charges and gantry details (for Taxi/Drive), and parking availability status with time penalties (for Drive). 6. Routes using fallback data display the notation "(some data is estimated)" in the explanation. 7. The polyline for each route is displayed on the map overlay. 8. If no routes were found, system shows a message and prompts the user to modify constraints or search again. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-24 Generate Route Explanation |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | The Scoring tab displays a 4-dimension breakdown (time, cost, risk, comfort) with normalised values and weighted contributions for each route. |

---

## 6.4 Settings

### UC-27: Change Settings

| Field | Value |
|---|---|
| Use Case ID | UC-27 |
| Use Case Name | Change Settings |
| Created By | Huynh Thao Tuong Van |
| Date Created | 11/2/2026 |
| Actor | User |
| Description | Lets the user update app-level settings including display language and default preference weights. Changes take effect once saved. |
| Preconditions | User navigates to the Settings screen |
| Postconditions | Modified settings are validated and saved (UC-04) |
| Priority | Medium |
| Frequency of Use | Low |
| Flow of Events | 1. User opens the Settings screen. 2. System displays current settings: display language (English, Chinese, Malay, Tamil), and default preference weight sliders. 3. User modifies one or more settings. 4. If the user changes the display language, system applies the selected language to all user-facing text via the i18n framework immediately on save. 5. If the user edits default preference weights, system updates the slider values. 6. User taps Save. 7. System triggers UC-04 to persist the settings. |
| Alternative Flows | NIL |
| Exceptions | NIL |
| Includes | UC-04 Save Settings |
| Special Requirements | NIL |
| Assumptions | NIL |
| Notes and Issues | The Settings screen also displays the status of each data source (Live or Fallback) and provides a cache refresh button that invalidates all cached data via the `/refresh` endpoint. |

---

## Removed Use Cases

The following use cases from the original document do not exist in the implemented application and have been removed:

| Removed UC | Reason |
|---|---|
| UC-06 (Choose Preference) | No "Use Default vs Modify for This Trip" dialog exists. Users adjust preferences directly on the search page via inline sliders. |
| UC-07 (Fetch Preference Profile) | Saved default preferences from Settings are not loaded into the search page. The search page always initialises with equal defaults (0.25 each). |
| UC-11 (Request Location / GPS) | No GPS or device location feature exists. Origin input is text-only with OneMap autocomplete. |
| UC-13 (Confirm Trip Request) | No confirmation or summary screen exists. The user clicks "Find Routes" directly after entering origin and destination. |
| UC-28 (Save Settings) | Merged into UC-04 (Save Settings), which handles all persistence (localStorage + optional backend sync). |
