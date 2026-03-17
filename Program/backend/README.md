Backend (FastAPI) for SGTravelBud (MVP).

Run (after installing requirements):
- Create `.env` in repo root (or copy `.env.example`) and set:
  - `GOOGLE_MAPS_KEY`
  - `LTA_ACCOUNT_KEY`
- Install deps: `pip install -r requirements.txt`
- Start server: `uvicorn backend.main:app --reload`

Key endpoints:
- `GET /health` — basic health check
- `GET /gmaps/directions` — direct Google Directions passthrough (no fallbacks). Params: `origin`, `destination`, optional `mode` (`transit|driving|walking|bicycling`), `alternatives` (bool), `departure_time` (`now` or ISO), `raw` (bool for raw response), `detail` (bool for expanded step-by-step with substeps and stop names).
- `GET /routes` — ranked 2–3 route options; query params include `origin`, `destination`, optional `departure_time`, flags (`mrt_only`, `public_only`, `taxi`, `drive`), constraints (`max_walk_min`, `max_transfers`, `max_budget`), and weights (`wt_time`, `wt_reliability`, `wt_crowding`, `wt_budget`).
- `GET /assessment` — segment-level indicators for the trip.
- `GET /datasets` — caching layer freshness and fallback state.
- `POST /refresh` — invalidates cached datasets.
- `GET/PUT /settings` — persisted simple settings in `backend/settings.json`.

Notes:
- When Google/LTA APIs are unavailable or keys missing, `/routes` and `/assessment` use a small sample route fixture to keep the API testable; risks may be marked Unknown.
- Use `/gmaps/directions` for live calls only; it requires a valid `GOOGLE_MAPS_KEY` and will not use fixtures.
- CORS is enabled for all origins to ease local frontend development.
