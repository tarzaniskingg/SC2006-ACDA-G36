# SGTravelBud Backend Implementation Plan

## Objectives
- Implement Lab2 FRs for transport condition assessment, route generation, ranking, freshness, fallbacks, and settings.
- Provide a FastAPI backend with clear layers, typed models, and testable services.
- Support 2–3 ranked route options with explanations, honoring constraints and preferences.

## Scope Mapping (FR coverage)
- FR-3.x Assessment: segment-level crowding and delay indicators, timestamps, freshness, fallback flags, packaged output.
- FR-4.x Routing/Ranking: mode-constrained route generation, risk aggregation (max + Unknown rules), normalization, weighted scoring, tie-breakers, selection, explanations.
- FR-5.x Freshness/Fallback/Settings: per-source timestamps + TTLs, coherent fallback snapshot per request, dataset status, manual refresh, basic settings persistence.

## Architecture
- API (FastAPI): route, assessment, datasets, refresh, settings endpoints.
- Clients: Google Directions, LTA DataMall (BusArrival, PCDForecast, EstTravelTimes, Taxi-Availability, TrafficSpeedBands, CarParkAvailabilityv2).
- Services:
  - AssessmentService: per-segment crowding + delay indicators, timestamps, fallback.
  - RoutingService: route generation (by enabled modes), constraints, aggregation, tie-breakers, explanations.
  - ScoringService: normalization (min–max), composite scoring, weight handling.
  - CacheService: per-dataset TTL cache + snapshot for coherent processing.
- Models: Pydantic schemas and enums for inputs, indicators, routes, settings, dataset status.
- Core: config (env), logging, scheduler (optional background refresh).

## Endpoints
- GET `/routes`
  - Query: `origin`, `destination`, `departure_time` (ISO), mode flags (mrt_only, public_only, taxi, drive, hybrid_taxi), constraints (max_walk_min, max_transfers, max_budget), weights (wt_time, wt_reliability, wt_crowding, wt_budget).
  - Returns: 2–3 ranked route options with normalized attributes, score, risks (cat + numeric), explanation, fallback markers.
- GET `/assessment`
  - Same trip inputs; returns packaged segment-level indicators.
- GET `/datasets`
  - Returns dataset freshness state: last_retrieved, ttl_sec, is_fallback, source.
- POST `/refresh`
  - Forces invalidation/refetch for a trip context; re-runs assessment and returns updated datasets/routes.
- GET/PUT `/settings`
  - Gets/updates default preference profile, language, units (simple JSON file persistence).

## Data & Caching
- TTLs (initial defaults): BusArrival 30s; PCDForecast 10m; EstTravelTimes 5m; TrafficSpeedBands 5m; Taxi-Availability 60s; CarPark 5m.
- Cache item: `{ value, retrieved_at, ttl_sec, source: 'realtime'|'fallback' }`.
- Snapshot: For each request, resolve each dataset to either realtime or fallback instance consistently (no mixing within a mode per FR-5.2).

## Risk Assessment
- Crowding (FR-3.5):
  - Bus: `BusArrival.Services[].NextBus.Load` → SEA/SDA/LSD mapped to Low/Medium/High; missing → Unknown.
  - MRT: PCDForecast crowding levels mapped to Low/Medium/High; missing → Unknown.
- Delay (FR-3.6):
  - Prefer EstTravelTimes by corridor/road segment; alternatively derive from TrafficSpeedBands deviation from free-flow; missing → Unknown.
- Segment output fields: `{ mode, from, to, crowding: {cat,num,source,is_fallback}, delay: {cat,num,source,is_fallback}, timestamp }`.

## Route Generation & Ranking
- Mode handling (FR-4.2): honor mode flags and constraints; hybrid taxi placeholder.
- Aggregation (FR-4.5.2/3): route-level crowding/delay = max over segments; Unknown precedence: if any Unknown → route-level Unknown.
- Attributes: time, transfers, cost (refined later; initial estimator by distance and duration), route risks.
- Numeric mapping (FR-4.6.3): Low=1, Medium=2, High=3, Unknown=2.
- Normalization (FR-4.7): min–max per request; identical values → 0.0 for all.
- Scoring (FR-4.8): weighted sum of normalized T', R', C', B'; weights normalized to sum 1.0.
- Tie-breakers (FR-4.9): delay num → crowding num → transfers → time → cost.
- Selection (FR-4.10): return 2–3 distinct options; notify when 1 or none (message field).
- Explanation (FR-4.11): reference top weight criterion and show risk cats; note reduced accuracy if any fallback used.

## Security & Config
- Env vars: `GOOGLE_MAPS_KEY`, `LTA_ACCOUNT_KEY`, TTLs, defaults; `.env.example` provided.
- Timeouts/retries: HTTP clients with backoff; safe defaults.

## Implementation Phases
1) Scaffold backend
   - Create FastAPI app, routers, core config, models; wire health check.
   - Requirements and `.env.example`.
2) Scoring & normalization
   - Numeric mapping, normalization (0.0/1.0), composite score, tie-breakers, explanation generator stub.
3) Cache & freshness
   - TTL cache, dataset status model, snapshot resolution, `/datasets` endpoint.
4) Assessment service (MVP)
   - Parse Google route legs into segments; compute crowding (bus via BusArrival; MRT via PCD); delay placeholder (Unknown); package output.
5) Routing service (MVP)
   - Use assessment outputs; aggregate risks; compute attributes; scoring; return 2–3 options; explanations; tie-breakers.
6) API routes
   - `/routes`, `/assessment`, `/datasets`, `/refresh`, `/settings` (JSON file persistence for settings).
7) Enrich delay signal & hybrid taxi (optional next)
   - EstTravelTimes/TrafficSpeedBands integration; hybrid taxi generator; improved cost model.

## Testing & Fixtures
- Unit tests for normalization, score, tie-breakers, risk aggregation, fallback snapshot logic.
- JSON fixtures for Google Directions and LTA to run offline.

## Acceptance Criteria (selected)
- FR-3.3/5.1: Each dataset in assessment output has timestamp; `/datasets` shows freshness and fallback.
- FR-3.5/3.6: Segment crowding/delay computed and categorized; Unknown when unavailable.
- FR-4.5: Route-level risks aggregated with Unknown precedence; transfers/time/cost present.
- FR-4.7/4.8: Attributes normalized; composite scores computed with normalized weights.
- FR-4.9: Deterministic ranking with tie-breakers.
- FR-4.10/4.11: 2–3 options with explanations; fallback noted when used.
- FR-5.2/5.3: Fallback used consistently and marked; no mixing per mode within a request.

## Open Questions
- Confirm PCDForecast categorical mapping; expected station identifiers format.
- Baseline/typical estimates for delay (if EstTravelTimes not granular enough) for MVP.
- Hybrid taxi constraints (max duration/budget thresholds) default values.

## Next Steps
- Implement Phases 1–3 immediately; then wire MVP assessment and routing services.

