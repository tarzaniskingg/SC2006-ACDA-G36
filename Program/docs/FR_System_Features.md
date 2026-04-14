# 4. System Features

## 4.1 User Input Preference

### 4.1.1 Description and Priority

This feature allows the User to view and adjust travel preferences and route filtering constraints within the route search page. These preferences influence route generation, scoring, and ranking. They include priority weights for Time, Cost, Risk, and Comfort, route category selection, and optional constraints such as maximum walking allowance, maximum number of transfers, and maximum budget. The active preference configuration is applied to the current route search, and default values may be updated through the Settings screen.

Priority: High

### 4.1.2 Stimulus/Response Sequences

1. User accesses the route search page.
2. System displays the current active preference values and constraints for the search page, initialised to equal defaults (0.25 each) with no constraints.
3. User optionally expands the priorities and constraints section.
4. User adjusts one or more priority weights, route categories, or route filtering constraints.
5. System updates the active preference configuration for the current search.
6. When the User initiates route search, the system applies the active preference configuration during route generation, scoring, and ranking.
7. If the User updates default values through the Settings screen, the system saves them for future sessions.

### 4.1.3 Functional Requirements

**FR-1.1. Preference Availability on Search Page**

- 1.1.1. The system shall display the current active preference values on the route search page.
- 1.1.2. The system shall display the current route filtering constraints on the route search page.
- 1.1.3. The system shall initialise the preference weights to equal default values (0.25 each) and constraints to no restriction on each page load.

**FR-1.2. Preference Weight Adjustment**

- 1.2.1. The system shall allow the User to adjust the relative importance of the following criteria within the route search page:
  - Time
  - Cost
  - Risk (combining crowding and delay)
  - Comfort (combining walking requirement and transfer burden)
- 1.2.2. The system shall provide adjustable slider controls for the above criteria, with a range of 0.0 to 1.0 in steps of 0.05.
- 1.2.3. The system shall display the current value of each criterion weight.
- 1.2.4. The system shall apply the active criterion weights to the current route search.

**FR-1.3. Preference Weight Normalisation**

- 1.3.1. The system shall normalise the active preference weights before applying them to route scoring by dividing each weight by the sum of all weights.
- 1.3.2. The sum of all normalised preference weights shall equal 1.0.
- 1.3.3. The system shall use the normalised preference weights in composite route scoring.

**FR-1.4. Comfort Definition**

- 1.4.1. The system shall interpret Comfort as a route convenience measure derived from walking requirement and transfer burden, using the formula: `comfort = 0.6 * walk_score + 0.4 * transfer_score`, where walk_score is capped at 30 minutes and normalised to a 0-10 range, and transfer_score is capped at 5 transfers and normalised to a 0-10 range.
- 1.4.2. The system shall not treat crowding level as the definition of Comfort. Crowding is part of the Risk dimension.
- 1.4.3. The system shall apply the Comfort measure consistently in route scoring.

**FR-1.5. Route Filtering Constraints**

- 1.5.1. The system shall allow the User to specify a maximum walking allowance (in minutes).
- 1.5.2. The system shall allow the User to specify a maximum number of transfers.
- 1.5.3. The system shall allow the User to specify a maximum trip budget (in SGD).
- 1.5.4. The system shall allow the User to leave any of the above constraints unspecified (empty) to indicate no restriction.
- 1.5.5. The system shall apply active constraints to the current route search by filtering out candidate routes that exceed any specified constraint.

**FR-1.6. Route Category Selection**

- 1.6.1. The system shall allow the User to enable or disable the following route categories on the route search page:
  - Public Transit (Bus + MRT)
  - Taxi / Drive (Private car)
- 1.6.2. The system shall require at least one route category to remain enabled.
- 1.6.3. The system shall prevent the User from disabling the last remaining enabled route category by silently reverting the toggle action (returning to the previous state).

**FR-1.7. Expand and Collapse Preferences Section**

- 1.7.1. The system shall allow the User to expand or collapse the priorities and constraints section on the route search page via a "Show/Hide priorities & constraints" toggle button.
- 1.7.2. When expanded, the section shall display the active priority weights and route filtering constraints.
- 1.7.3. When collapsed, the current active preference configuration shall remain in effect for the current search.

**FR-1.8. Saving Default Preferences**

- 1.8.1. The system shall allow the User to view and update default preference weight values through the Settings screen.
- 1.8.2. Upon saving updated default preference values, the system shall persist them in localStorage and optionally to the backend for future sessions.

---

## 4.2 Trip Request Input

### 4.2.1 Description and Priority

This feature allows the User to initiate and configure a route search by specifying the origin and destination on the route search page. The system validates the search inputs and applies the current active preference configuration before route generation begins. This feature ensures that only valid and complete search inputs are passed to the route generation and assessment functions.

Priority: High

### 4.2.2 Stimulus/Response Sequences

1. User accesses the route search page.
2. User enters an origin location.
3. System displays location suggestions from the OneMap API as the User types.
4. User selects a suggested origin or continues typing.
5. User enters a destination location.
6. System displays location suggestions from the OneMap API as the User types.
7. User selects a suggested destination or continues typing.
8. User may swap the origin and destination values.
9. System checks whether the search inputs are valid and whether at least one route category is enabled.
10. When the required inputs are valid, the system enables the Find Routes action.
11. User initiates route search.
12. System passes the validated route search inputs and active preference configuration to the route generation and assessment functions.

### 4.2.3 Functional Requirements

**FR-2.1. Route Search Initiation**

- 2.1.1. The system shall allow the User to initiate a route search from the route search page.
- 2.1.2. The system shall use the current active preference configuration when route search is initiated.
- 2.1.3. The system shall not initiate route search unless the required search inputs are valid.

**FR-2.2. Origin Input**

- 2.2.1. The system shall allow the User to enter an origin location manually via a text input field.
- 2.2.2. The system shall display location suggestions from the OneMap API while the User is entering the origin, triggered after a 300ms debounce delay and a minimum of 2 characters.
- 2.2.3. The system shall update the suggestion list when the User modifies the origin input.
- 2.2.4. The system shall allow the User to select a suggested location to populate the origin field.
- 2.2.5. The system shall implicitly constrain origin locations to Singapore by using the OneMap API, which only returns Singapore-based results.

**FR-2.3. Destination Input**

- 2.3.1. The system shall allow the User to enter a destination location manually via a text input field.
- 2.3.2. The system shall display location suggestions from the OneMap API while the User is entering the destination, triggered after a 300ms debounce delay and a minimum of 2 characters.
- 2.3.3. The system shall update the suggestion list when the User modifies the destination input.
- 2.3.4. The system shall allow the User to select a suggested location to populate the destination field.
- 2.3.5. The system shall implicitly constrain destination locations to Singapore by using the OneMap API, which only returns Singapore-based results.

**FR-2.4. Search Input Validation**

- 2.4.1. The system shall validate that the origin and destination are not identical (case-insensitive string comparison).
- 2.4.2. If the origin and destination are identical, the system shall display the error message "Origin and destination cannot be the same" and prevent route search.
- 2.4.3. The system shall require at least one enabled route category before route search can proceed.
- 2.4.4. The system shall require both origin and destination to contain at least 2 characters.

**FR-2.5. Swap Origin and Destination**

- 2.5.1. The system shall allow the User to swap the origin and destination values on the route search page via a swap button.
- 2.5.2. After swapping, the system shall revalidate the updated search inputs automatically through reactive state binding.

**FR-2.6. Find Routes Availability**

- 2.6.1. The system shall enable the Find Routes action only when: (a) the origin has at least 2 characters, (b) the destination has at least 2 characters, (c) the origin and destination are not identical, and (d) no search is currently in progress.
- 2.6.2. The system shall disable the Find Routes action when any of the above conditions are not met.

---

## 4.3 Assess Transport Conditions and Generate Risk Scores

### 4.3.1 Description and Priority

This feature retrieves real-time transport data relevant to the current route search and evaluates transport conditions associated with candidate routes. It assesses data freshness, applies fallback mechanisms where necessary, and computes risk-related indicators for route generation, scoring, ranking, and display. For public transit routes, the system assesses crowding and delay conditions where such data is available. For Taxi/Drive routes, the system retrieves relevant category-specific data where available.

Priority: High

### 4.3.2 Stimulus/Response Sequences

1. User initiates route search from the route search page.
2. System determines which transport data sources are relevant based on the validated search inputs, enabled route categories, and active preference configuration.
3. System retrieves relevant real-time transport data from external sources.
4. System associates timestamps with the retrieved data.
5. System evaluates whether each retrieved data source satisfies freshness requirements using TTL-based thresholds.
6. If any required data is unavailable or outdated, the system applies fallback handling using the most recent cached data.
7. System computes risk-related indicators for relevant route segments and routes.
8. System packages the route assessment output.
9. System passes the route assessment output to the route generation, scoring, ranking, and display functions.

### 4.3.3 Functional Requirements

**FR-3.1. Initiate Transport Condition Assessment**

- 3.1.1. The system shall initiate transport condition assessment when the User initiates route search.
- 3.1.2. The system shall use the validated search inputs as the assessment context.
- 3.1.3. The system shall apply the current active preference configuration during transport condition assessment.

**FR-3.2. Retrieve Relevant Real-Time Transport Data**

- 3.2.1. The system shall retrieve real-time transport data relevant to the current route search from the following sources:
  - LTA Bus Arrival API (bus crowding and frequency data)
  - LTA PCD Real Time API (real-time MRT station crowding levels)
  - LTA PCD Forecast API (forecasted MRT station crowding by 30-min interval)
  - LTA Train Service Alerts (MRT delay/disruption data)
  - LTA Carpark Availability (parking data for Drive routes)
  - NEA 2-Hour Weather Forecast (weather conditions along route)
  - Google Directions API (route options with traffic-aware driving duration and transit fare data)
- 3.2.2. If Public Transit is enabled, the system shall retrieve public-transit-related data including MRT crowdedness data (PCD Real Time, with PCD Forecast and time-based heuristic as fallbacks), MRT service alert information, and bus arrival data.
- 3.2.3. If Taxi/Drive is enabled, the system shall retrieve driving-related data including traffic-aware duration from Google (duration_in_traffic), ERP gantry data, and carpark availability at the destination.
- 3.2.4. The system shall retrieve only the data sources required for the current route search.
- 3.2.5. The system shall enforce a global rate limit on LTA API calls (max ~6 requests/second) to stay within quota limits, using a per-call lock with minimum interval.

**FR-3.3. Data Freshness Compliance**

- 3.3.1. The system shall associate a retrieval timestamp with each retrieved real-time transport data source via the cache layer.
- 3.3.2. The system shall evaluate whether each data source meets predefined TTL-based freshness thresholds:
  - Bus Arrival: 30 seconds
  - PCD Real Time (MRT crowding): 60 seconds
  - PCD Forecast (MRT crowding): 21,600 seconds (6 hours; updated daily by LTA)
  - Train Service Alerts: 60 seconds
  - Carpark Availability: 300 seconds (5 minutes)
  - NEA Weather Forecast: 600 seconds (10 minutes)
- 3.3.3. If a data source does not meet the freshness criteria (TTL expired), the system shall treat it as outdated and apply fallback handling in accordance with Section 4.5.

**FR-3.4. Fallback Data Compliance**

- 3.4.1. If real-time transport data is unavailable or outdated, the system shall apply fallback handling using the most recent cached data.
- 3.4.2. The system shall mark any data elements operating in fallback mode by setting `is_fallback = true` and `source = "fallback"` on the corresponding `RiskIndicator`.
- 3.4.3. The system shall allow route generation and ranking to proceed when fallback data is used, unless no relevant data is available at all.
- 3.4.4. Different segments within the same route may independently use real-time or fallback data. If any segment uses fallback data, the route-level `uses_fallback` flag shall be set to true.

**FR-3.5. Assess Crowding Conditions**

- 3.5.1. For bus segments, the system shall compute a crowding indicator from the LTA Bus Arrival API `Load` field using the following mapping:
  - SEA (Seats Available) -> Low
  - SDA (Standing Available) -> Medium
  - LSD (Limited Standing) -> High
- 3.5.2. For MRT segments, the system shall attempt three crowding sources in order:
  - (a) LTA PCD Real Time API — returns the current crowding level per station (l=Low, m=Medium, h=High). Used as the primary source.
  - (b) LTA PCD Forecast API — returns forecasted crowding by 30-min interval matched to the query time. Used when real-time data is unavailable.
  - (c) Time-based heuristic — uses well-known Singapore MRT peak patterns (weekday 7-9:30am and 5:30-8pm = High, shoulder periods = Medium, off-peak and weekends = Low). Used when both PCD APIs return no data.
- 3.5.3. The system shall use the first source in the above chain that returns valid data.
- 3.5.4. The system shall categorise each crowding indicator as Low, Medium, High, or Unknown.
- 3.5.5. If crowding data is unavailable from all sources for a relevant segment, the system shall mark the indicator as Unknown.
- 3.5.6. The system shall pass crowding indicators to downstream route assessment and display functions.

**FR-3.6. Assess Delay Conditions**

- 3.6.1. For MRT segments, the system shall compute a delay indicator from the LTA Train Service Alerts API:
  - Status = 1 (normal service): Low
  - Status = 2 (disruption) on the route's line: High
  - Status = 2 (disruption) on a different line: Low
  - Status = 2 (disruption) with no specific line identified: Medium (precautionary)
- 3.6.2. For bus segments, the system shall assign a default delay indicator of Low.
- 3.6.3. For driving/taxi segments, the system shall derive a delay indicator from Google's traffic data by comparing the baseline duration to the traffic-aware duration (duration_in_traffic):
  - Ratio >= 1.5 (50%+ slower than normal): High
  - Ratio >= 1.2 (20-50% slower): Medium
  - Ratio < 1.2 (within 20% of normal): Low
- 3.6.4. The system shall categorise each delay indicator as Low, Medium, High, or Unknown.
- 3.6.5. If delay data is unavailable for a relevant segment, the system shall mark the indicator as Unknown.
- 3.6.6. The system shall pass delay indicators to downstream route assessment and display functions.

**FR-3.7. Prepare Route Assessment Output**

- 3.7.1. The system shall package the computed transport-condition indicators as a structured route assessment output using the `SegmentAssessment` schema.
- 3.7.2. For each computed indicator, the output shall include the indicator category, numeric value, source type ("realtime" or "fallback"), fallback flag, and retrieval timestamp.
- 3.7.3. The system shall pass the route assessment output as input to route generation, route scoring, route ranking, and route display functions.

---

## 4.4 Route Generation and Ranking

### 4.4.1 Description and Priority

This feature generates feasible route options based on validated route search inputs and the current active preference configuration. It applies user-defined route categories and filtering constraints, assigns route attributes, derives route-level risk and comfort measures, computes composite scores, ranks routes deterministically, and prepares ranked route options for display with brief explanations.

Priority: High

### 4.4.2 Stimulus/Response Sequences

1. Route assessment output is received after the User initiates route search.
2. System generates candidate routes using the Google Directions API for the enabled route categories.
3. For driving routes, the system generates both a Taxi candidate and a Drive (own car) candidate from the same route.
4. System deduplicates candidate routes by fingerprint (category + mode sequence + line names + stops), keeping the faster route when duplicates exist.
5. System applies active walking, transfer, and budget constraints by filtering.
6. System assigns route attributes such as travel time, travel cost, walking requirement, transfer count, and risk indicators.
7. System derives a comfort measure and a combined risk measure for each candidate route.
8. System normalises route attributes using min-max normalisation.
9. System computes composite scores using normalised preference weights and normalised route attributes.
10. System ranks routes in ascending order of composite score.
11. System applies tie-breaking rules where required.
12. System selects up to 5 distinct ranked route options, ensuring category diversity.
13. System generates a brief explanation for each selected route.
14. System passes the ranked route options to the route display function.

### 4.4.3 Functional Requirements

**FR-4.1. Route Generation Initiation**

- 4.1.1. The system shall initiate route generation after transport condition assessment has been completed.
- 4.1.2. The system shall use the validated route search inputs for route generation.
- 4.1.3. The system shall use the route assessment output from Section 4.3 as input to route generation, scoring, and ranking.
- 4.1.4. The system shall apply the current active preference configuration during route generation, scoring, and ranking.

**FR-4.2. Route Generation by Route Category**

- 4.2.1. The system shall generate route options only using route categories enabled in the active preference configuration.
- 4.2.2. If Public Transit is enabled, the system shall generate public transit route options via the Google Directions API with mode "transit".
- 4.2.3. Public transit route options may include MRT-only or MRT-and-Bus combinations as determined by the Google Directions API.
- 4.2.4. If Taxi/Drive is enabled, the system shall generate driving route options via the Google Directions API with mode "driving", producing both a Taxi candidate and a Drive (own car) candidate from each driving route.
- 4.2.5. The Taxi candidate shall not include parking penalties (taxi drops off the passenger).
- 4.2.6. The Drive candidate shall include parking-related penalties on time, risk, and comfort based on nearby carpark availability.
- 4.2.7. If Public Transit is the only enabled route category, the system shall exclude Taxi/Drive route options.
- 4.2.8. If Taxi/Drive is the only enabled route category, the system shall exclude Public Transit route options.

**FR-4.3. Route Deduplication and Constraint Handling**

- 4.3.1. The system shall generate only routes that are feasible, i.e., routes that allow travel from the specified origin to the destination.
- 4.3.2. The system shall deduplicate candidate routes using a fingerprint comprising the route category, mode sequence, line names, and stop names. When duplicates are detected, the system shall retain the faster route.
- 4.3.3. The system shall apply walking tolerance constraints during route filtering:
  - 4.3.3.1. If a maximum walking allowance is specified, the system shall exclude routes where total walking time exceeds the limit.
- 4.3.4. The system shall apply transfer tolerance constraints during route filtering:
  - 4.3.4.1. If a maximum number of transfers is specified, the system shall exclude routes where the transfer count exceeds the limit.
- 4.3.5. The system shall apply budget constraints during route filtering:
  - 4.3.5.1. If a maximum budget is specified, the system shall exclude routes where the estimated cost exceeds the budget.
- 4.3.6. If no feasible routes remain after constraint filtering, the system shall return an empty route list with the message "No routes found or API unavailable".

**FR-4.4. Route Attribute Assignment**

- 4.4.1. For each generated route, the system shall assign an estimated travel time derived from the Google Directions API. For driving routes, the system shall use `duration_in_traffic` (real-time traffic-aware ETA) when available, falling back to `duration` (historical average). For transit routes, the system shall use `duration`.
- 4.4.2. For each generated route, the system shall compute a realistic travel time by adding a bus wait buffer of `0.5 * miss_penalty_min` per bus step (modelling a 50% chance of missing the bus).
- 4.4.3. For Drive routes, the system shall add a parking search time penalty to the realistic travel time: +10 minutes if nearby parking is full, +5 minutes if limited.
- 4.4.4. For each generated route, the system shall compute a route-level crowding risk level by aggregating segment-level crowding risk values using a worst-case (maximum) rule:
  - (a) If all segment-level crowding risk indicators are Unknown, the route-level crowding risk level shall be Unknown with numeric value 2.
  - (b) If some segment-level crowding risk indicators are Unknown and some are known, the route-level crowding risk level shall be the maximum of the known segment-level crowding risk values.
  - (c) Otherwise, the route-level crowding risk level shall be the maximum segment-level crowding risk level.
- 4.4.5. For each generated route, the system shall compute a route-level delay risk level by aggregating segment-level delay risk values using the same worst-case rule as crowding (FR-4.4.4).
- 4.4.6. For each generated route, the system shall determine the number of transfers as the count of transit segments minus one (minimum 0).
- 4.4.7. For each generated route, the system shall determine the estimated travel cost:
  - Public Transit: The system shall prefer Google's `fare` field when available (real TransitLink pricing including early-bird and off-peak discounts, multi-modal fare caps). When Google fare data is unavailable, the system shall fall back to a distance-based fare table (TransitLink rates, $0.99-$2.20) with time-of-day adjustments: $0.50 early-bird discount (before 7:45am weekdays), $0.50 off-peak discount (9:30am-4pm weekdays and all day weekends).
  - Taxi: ComfortDelGro 2026 metered fare with $4.60 flag-down (first 1 km), $0.27 per 400m up to 10 km, $0.27 per 350m after 10 km, $0.27 per 45 seconds waiting (assuming 20% idle time), plus applicable surcharges (25% peak, 50% late-night, $2.30-$3.30 booking fee, $6-$8 Changi Airport surcharge), plus ERP charges.
  - Own Car (Drive): Fuel cost at $0.12/km, plus ERP charges.
- 4.4.8. For Drive routes, the system shall inflate the walking time when parking is scarce: +5 minutes if parking is full, +2 minutes if limited.

**FR-4.5. Risk Quantification for Scoring (Numeric Conversion)**

- 4.5.1. The system shall convert route-level crowding and delay risk categories into numerical values for use in the composite scoring formula.
- 4.5.2. The system shall use the following numeric mapping for risk categories, where a lower numeric value represents lower risk (better outcome):

| Risk Category | Numeric Value | Rationale |
|---|---|---|
| Low | 1 | Minimal risk - most desirable |
| Medium | 2 | Moderate risk - acceptable |
| High | 3 | Elevated risk - least desirable |
| Unknown | 2 (default fallback) | Conservative mid-point - treated as potentially moderate risk |

Note: When route-level risk is Unknown, the system shall display it as Unknown. For scoring purposes only, Unknown is treated as a neutral value (2).

- 4.5.3. The system shall combine route-level crowding and delay risk into a single Risk score using the formula: `Risk = max(crowding_numeric, delay_numeric)`, producing a value on the 1-3 scale.

**FR-4.6. Normalisation of Route Attributes**

- 4.6.1. The system shall normalise route attributes to a common scale before computing composite scores, enabling fair comparison across routes with different units.
- 4.6.2. The system shall apply min-max normalisation to the following four dimensions within each trip request:
  - Travel time (T)
  - Estimated travel cost (B)
  - Combined risk score (R) - derived from `max(crowding_numeric, delay_numeric)`
  - Comfort score (F) - derived from `0.6 * walk_score + 0.4 * transfer_score`
- 4.6.3. Min-max normalisation shall be applied as follows:
  - 4.6.3.1. `X_norm = (X - X_min) / (X_max - X_min)`, where X_min and X_max are the minimum and maximum values of that attribute across all candidate routes in the current trip request.
  - 4.6.3.2. A normalised value of 0.0 represents the best-performing route on that attribute; a normalised value of 1.0 represents the worst-performing route.
  - 4.6.3.3. If all candidate routes have identical values for an attribute, the system shall assign a normalised value of 0.0 to all routes for that attribute.
- 4.6.4. Normalisation shall be computed consistently across all candidate routes within a single trip.

**FR-4.7. Composite Route Scoring**

- 4.7.1. The system shall compute a composite score for each candidate route using the User's normalised preference weights and normalised route attributes.
- 4.7.2. The composite score shall be computed using the following weighted scoring formula:

```
Route Score = w_T * T' + w_B * B' + w_R * R' + w_F * F'
```

| Term | Definition | Remarks |
|---|---|---|
| Route Score | Composite score | Lower score = better route |
| w_T, w_B, w_R, w_F | Normalised preference weights (Section 1.3) | Sum to 1.0 |
| T' | Normalised travel time | 0.0 = fastest |
| B' | Normalised travel cost | 0.0 = cheapest |
| R' | Normalised combined risk score | 0.0 = lowest risk |
| F' | Normalised comfort score | 0.0 = most comfortable |

- 4.7.3. The system shall rank routes in ascending order of composite score, such that the route with the lowest composite score is ranked first.
- 4.7.4. A composite score of 0.0 represents a route that is best on all criteria relative to the candidate set; a score of 1.0 represents a route that is worst on all criteria.

**FR-4.8. Route Ranking and Tie-Breaker**

- 4.8.1. The system shall rank all feasible candidate routes in ascending order of composite score.
- 4.8.2. If two or more routes have equal composite scores, the system shall apply the following tie-breaking sequence in order:
  1. Lower combined risk numeric value (max of crowding and delay)
  2. Lower comfort numeric value (lower = more comfortable)
  3. Shorter estimated travel time
  4. Lower estimated travel cost
- 4.8.3. Tie-breaking shall use numeric values to ensure deterministic ordering.

**FR-4.9. Route Selection Output**

- 4.9.1. The system shall generate up to 5 ranked route options per trip request.
- 4.9.2. The system shall ensure category diversity by first selecting the best route from each category (Public Transit, Taxi, Drive), then filling remaining slots (up to 5) with the next-best overall routes.
- 4.9.3. Each presented route option shall represent a distinct travel alternative, as determined by the deduplication fingerprint (different mode sequences, paths, or transfer points).
- 4.9.4. If no feasible routes can be generated, the system shall notify the User with the message "No routes found or API unavailable" and display a prompt to modify constraints or search again.

**FR-4.10. Route Explanation**

- 4.10.1. For each generated route option, the system shall provide a brief explanation composed of multiple descriptive pieces joined by periods.
- 4.10.2. The explanation shall reference the User's highest-weighted criterion and summarise how the route performs on that criterion:
  - Time: "Fastest option at {X} min"
  - Cost: "Cheapest at ${X}"
  - Risk: "Lowest risk: {category}"
  - Comfort: "Most comfortable: {X} min walk, {Y} transfer(s)"
- 4.10.3. The explanation shall include per-step crowding highlights where available (e.g., "Crowded: Bus 143" or "Not crowded: MRT NSL").
- 4.10.4. The explanation shall include the total walking time (e.g., "{X} min walking").
- 4.10.5. If fallback data was used in computing any risk indicator for the route, the explanation shall include the notation "(some data is estimated)".

---

## 4.5 Data Freshness, Fallback & Settings

### 4.5.1 Description and Priority

This feature manages real-time data freshness evaluation, fallback data handling, user-initiated data refresh, and system settings such as localisation and preference updates. It ensures that route recommendations remain consistent, transparent, and adaptable to User preferences and data availability conditions.

Priority: Medium

### 4.5.2 Stimulus/Response Sequences

1. Real-time transport data is retrieved.
2. System evaluates freshness against predefined TTL thresholds.
3. If data is outdated (TTL expired), system uses most recent cached data as fallback.
4. System marks affected route recommendations accordingly via `uses_fallback` flag.
5. User selects "Refresh".
6. System invalidates all cached data and re-initiates transport condition assessment.
7. System regenerates and re-ranks routes.
8. User accesses Settings screen.
9. User modifies language or default preference weights.
10. System saves updated settings to localStorage and optionally to the backend.

### 4.5.3 Functional Requirements

**FR-5.1. Data Freshness Management**

- 5.1.1. The system shall maintain an in-memory TTL cache for all retrieved real-time transport data.
- 5.1.2. Each cached item shall record the retrieval timestamp and TTL in seconds.
- 5.1.3. The system shall evaluate whether each data source meets its predefined freshness threshold by comparing elapsed time since retrieval against the TTL.
- 5.1.4. If a data source does not meet the freshness criteria, the system shall treat it as outdated.

**FR-5.2. Fallback Data Handling**

- 5.2.1. If real-time transport data is unavailable or outdated, the system shall use the most recent cached data for processing, marked with `source = "fallback"` and `is_fallback = true`.
- 5.2.2. If no cached data exists and the API call fails, the system shall return an empty data structure with `is_fallback = true`.
- 5.2.3. The system shall identify which transport sources are operating in fallback mode through the `RiskIndicator.is_fallback` field at the segment level and the `uses_fallback` flag at the route level.
- 5.2.4. Different segments within the same route may independently use real-time or fallback data. The route-level `uses_fallback` flag is set to true if any segment uses fallback data.

**FR-5.3. Impact Awareness on Route Recommendations**

- 5.3.1. If fallback data is used during risk assessment or route generation, the system shall set the route-level `uses_fallback` flag to true.
- 5.3.2. The route explanation shall include the notation "(some data is estimated)" when the route uses fallback data.
- 5.3.3. The Settings screen shall display the status of each data source as either "Live" (real-time) or "Fallback" (stale/unavailable), with colour-coded badges (green for Live, amber for Fallback).
- 5.3.4. The system shall allow route generation and ranking to proceed when fallback data is used, unless no relevant data is available.

**FR-5.4. User-Initiated Data Refresh**

- 5.4.1. The system shall provide a Refresh button on the results page, the main view, and the Settings screen.
- 5.4.2. Upon refresh from the results page or main view, the system shall re-fetch routes using the same search parameters with fresh data.
- 5.4.3. Upon refresh from the Settings screen, the system shall invalidate all cached data via the `/refresh` endpoint, clearing the entire in-memory cache.
- 5.4.4. The system shall regenerate and re-rank route options after a successful data refresh.

**FR-5.5. User Settings & Localisation**

- 5.5.1. The system shall allow the User to access the Settings screen.
- 5.5.2. The system shall allow the User to select a display language from the following options:
  - English (en)
  - Chinese Simplified (zh)
  - Malay (ms)
  - Tamil (ta)
- 5.5.3. The system shall apply the selected language to all user-facing text using the i18n framework, with English as the fallback language.
- 5.5.4. The system shall save the selected language to localStorage for future sessions.
- 5.5.5. The system shall allow the User to view and update default preference weights through the Settings screen via slider controls (range 0.0-1.0, step 0.05).
- 5.5.6. Upon saving changes, the system shall persist the updated settings to localStorage and optionally sync to the backend via the `/settings` endpoint.
