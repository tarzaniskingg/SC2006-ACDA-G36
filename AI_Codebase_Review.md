# Section 3.3 — Coding Agent Exercises
**Project**: SGTravelBud (SC2006 Group Project, Team ACDA-G36)
**AI Assistant**: Claude Sonnet 4.6 (Claude Code CLI)
**Date**: 3 April 2026

---

## Table of Contents
1. [3.3.2 — AI-Assisted Class Regeneration](#332--ai-assisted-class-regeneration)
2. [3.3.3 — AI Opinion on Codebase Quality](#333--ai-opinion-on-codebase-quality)
3. [3.3.4 — Reflections](#334--reflections)

---

## 3.3.2 — AI-Assisted Class Regeneration

### Exercise Description
We temporarily deleted the entire implementation of `RouteScoringController` (`Program/backend/services/routing.py`) and prompted the AI agent to regenerate it from scratch, using our test suite, codebase, and design documents as the only inputs.

### Control Class Deleted
**`RouteScoringController`** — `Program/backend/services/routing.py`

This class was chosen because it is the most critical control class in the application, implementing the core scoring and ranking logic described in the SRS (FR-4.5 through FR-4.9 and Feature 5).

The six public functions deleted were:
- `aggregate_route_risks` — rolls up segment risks to route level
- `estimate_cost` — computes fare for transit, taxi, and own-car modes
- `build_route_steps` — parses Google route data into rich `RouteStep` objects
- `compute_realistic_time` — inflates travel time using bus miss-penalty data
- `rank_routes` — normalises and scores candidate routes by weighted dimensions
- `add_explanations` — attaches human-readable explanation strings to ranked routes

### Prompt Used

> *"Re-implement `Program/backend/services/routing.py` from scratch. Treat this file as the implementation of our `RouteScoringController` control class. Read these files first for context and compatibility: `Program/backend/api/routes.py`, `Program/backend/models/schemas.py`, `Program/backend/services/scoring.py`, `Program/skeleton.md`, `Program/docs/class_diagram.puml`, and the routing test file. Requirements: recreate the six public functions used by `routes.py`, keep imports and return shapes compatible with the existing codebase, use `SegmentAssessment`, `RiskCategory`, and `RouteStep` from `schemas.py`, use scoring helpers from `scoring.py` instead of re-implementing them, preserve current behaviour, do not modify other files unless absolutely necessary, write clean minimal Python that passes the tests."*

### Materials Provided to the AI

| File | Purpose |
|------|---------|
| `api/routes.py` | Shows exactly how each function is called and what fields it reads from the return value |
| `models/schemas.py` | Defines all entity types the regenerated code must use |
| `services/scoring.py` | Provides normalisation, scoring, and explanation helpers to delegate to |
| `skeleton.md` | Architecture overview, package structure, and algorithm descriptions |
| `docs/class_diagram.puml` | UML diagram showing `RoutingController` with all method signatures |
| `tests/test_routing.py` | 50 unit tests specifying exact expected input/output behaviour |

### AI-Generated Output

The agent read all six files autonomously and produced a complete, syntactically valid `routing.py` in a single response. No follow-up prompting was needed to generate the file. The regenerated implementation:

- Correctly structured all six public functions with the right signatures
- Correctly implemented the 4-dimension normalisation and composite scoring pipeline
- Correctly implemented the Unknown-precedence risk aggregation logic
- Correctly implemented bus miss-penalty time inflation
- Correctly parsed Google Directions transit and driving steps into `RouteStep` objects

### Test Results After Regeneration

Upon running the test suite (`python -m pytest tests/test_routing.py -v`):

| Result | Count |
|--------|-------|
| Passed | 43 |
| Failed | 7 |
| Total  | 50 |

The 7 failures fell into four specific categories:

| Failure Category | Tests Affected | Root Cause |
|------------------|---------------|------------|
| Fare table values | TC04 | Agent used `$2.19` for the 40.2 km bracket; correct value is `$1.98`. Also used distance-in-metres as key instead of distance-in-kilometres. |
| Taxi rate constant | TC09 | Agent derived `$0.625/km` from the `$0.25/400m` formula; original implementation uses `$0.55/km` flat rate. |
| Return dict keys | TC10, TC12 | Agent returned key `distance_cost`; tests expect `distance_charge`. Agent omitted `waiting_charge` as a separate key. |
| Mode label | TC11 | Agent returned `mode: "driving"` for driving input; tests expect `mode: "taxi"` for both taxi and driving modes. |
| Drive-step delay | TC48 | Agent did not attach the segment's `delay` field onto the resulting `Drive` `RouteStep` in the driving branch. |

**Notably, all failures were in numeric constants and dictionary key names — not in the core logic.** All tests for aggregation, normalisation, ranking, explanations, and realistic time calculation passed on the first attempt.

---

## 3.3.3 — AI Opinion on Codebase Quality

### Experiment Chosen
We asked the AI assistant to read the entire project repository, understand the requirements from the Lab 3 SRS document, and provide an independent opinion on the quality of the codebase with concrete suggestions for refactoring.

### Prompt Used

> *"Can you read the whole folder SC2006-ACDA-G36, read Lab 3 main to understand the project idea and read on the Program folder and then comment your opinion on the quality of the codebase and suggestions for refactoring."*

### Materials Provided to the AI
The full project repository was accessible to the agent. It autonomously scanned all backend services, API routes, frontend components, configuration files, test files, and the Lab 3 PDF (`Lab3_Team1-Main.pdf`) using its `Explore` subagent.

---

### Overall Quality Rating: B+

The AI rated the codebase above average for a university lab project, noting that real async API integration with graceful degradation, a working multi-dimensional scoring model, and TTL caching with fallback are non-trivial to implement correctly.

---

### What the AI Said Was Done Well

**Architecture**
- Clean 3-layer separation: API → Service → Client. Each layer has a clear responsibility, making the system easy to test and extend.
- Pydantic schemas for all DTOs enforce proper typing discipline across the backend.
- TTL caching with per-dataset TTLs and fallback snapshot logic — the AI noted this as production-grade thinking.
- Graceful degradation (fixture fallback + flagging in response) means the app remains functional even when external APIs are unavailable.

**Business Logic**
- The risk aggregation model (max across segments, Unknown precedence) is principled and defensible.
- Tie-breaking with a deterministic ordering prevents non-reproducible rankings.
- Realistic time estimation via bus miss-penalty is a thoughtful, non-trivial feature.

**Frontend**
- React 19 + Vite + Tailwind is a modern, well-chosen stack.
- Mobile-first layout with bottom navigation is appropriate for a transit app.

---

### Refactoring Suggestions

#### 1. `api/routes.py` is Doing Too Much (865 lines) — HIGH PRIORITY

**Problem**: Route handlers contain full orchestration logic that belongs in a service layer. The `GET /routes` handler alone does: fetch Google Directions, assess segments, aggregate risks, apply constraints, rank routes, add explanations, and enforce category diversity.

**Suggested Fix**: Extract a `TripPlannerService` (Facade pattern) so each endpoint becomes ≤30 lines.

```python
# services/trip_planner.py
class TripPlannerService:
    def plan_trip(self, query: TripQuery) -> RoutesResponse:
        routes = self.google_client.get_directions(...)
        assessed = [self.assessment.assess(r) for r in routes]
        ranked = self.routing.rank_routes(assessed, query.weights)
        return self.build_response(ranked)
```

---

#### 2. Magic Numbers Scattered Across Multiple Files — HIGH PRIORITY

**Problem**: `Low=1, Medium=2, High=3, Unknown=2` is hardcoded in at least `routing.py`, `scoring.py`, and `routes.py`. This was confirmed as a real risk: during the 3.3.2 exercise, the AI regenerated the constants with slightly different values, causing 7 test failures.

**Suggested Fix**: Centralise in `schemas.py` or `constants.py`:

```python
from enum import IntEnum

class RiskLevel(IntEnum):
    LOW = 1
    UNKNOWN = 2  # same as Medium by design
    MEDIUM = 2
    HIGH = 3
```

---

#### 3. Cost Estimation Logic is Inline and Fragile — MEDIUM PRIORITY

**Problem**: Taxi meter rates and TransitLink fare tables are embedded in `routing.py`. Rate changes break the code silently.

**Suggested Fix**: Extract to `services/cost.py` with unit-testable functions and config-driven rate constants.

---

#### 4. Deep `.get()` Chains on Google API Response — MEDIUM PRIORITY

**Problem**: Nested dict access like `leg.get("steps", [])[0].get("transit_details", {}).get("line", {}).get("short_name", "")` produces silent empty strings when keys change.

**Suggested Fix**: Parse the Google response into a typed Pydantic model at the client boundary so errors surface immediately.

---

#### 5. `_MRT_STATIONS` Dictionary in `assessment.py` is Unmaintainable — MEDIUM PRIORITY

**Problem**: 100+ hardcoded MRT station entries in Python source code. Adding new stations (e.g., Cross Island Line) requires editing Python code.

**Suggested Fix**: Move to `fixtures/mrt_stations.json`, loaded at startup. Updatable without touching source code.

---

#### 6. Frontend Has No Loading/Error State Abstraction — MEDIUM PRIORITY

**Problem**: Each page (`SearchPage.jsx`, `ResultsPage.jsx`, etc.) manually manages its own `loading` and `error` state, causing repeated boilerplate and inconsistent UX.

**Suggested Fix**: A custom `useFetch` hook or React Query (`@tanstack/react-query`) centralises this pattern.

---

#### 7. `settings.json` as Flat File for Persistence — LOW PRIORITY

**Problem**: Concurrent requests create a write-hazard; does not scale beyond a single process.

**Suggested Fix**: SQLite via `aiosqlite` — zero-infrastructure, async-safe, appropriate for this project's scope.

---

#### 8. CORS is Fully Open — LOW PRIORITY (Must Fix Before Production)

**Problem**: `allow_origins=["*"]` in `main.py`.

**Suggested Fix**: Restrict to the specific frontend origin before any public deployment.

---

#### 9. Dead Prototype Files at Root Level — LOW PRIORITY (Trivial)

**Problem**: `Program/googlemaps_api.py`, `Program/lta_api.py`, `Program/fetch.py` are early prototypes superseded by the `clients/` layer, creating confusion about the authoritative implementation.

**Suggested Fix**: Delete or move to `archive/`.

---

#### 10. No End-to-End Integration Tests — LOW PRIORITY

**Problem**: Tests cover cache, scoring, and Google fallback in isolation. No test exercises the full `GET /routes` pipeline.

**Suggested Fix**: One `httpx.AsyncClient` integration test with fixture data verifying the full pipeline from HTTP request to ranked routes.

---

### Priority Matrix

| Priority | Issue | Effort |
|----------|-------|--------|
| **High** | Extract orchestration out of `routes.py` | Medium |
| **High** | Centralise magic numbers / RiskLevel enum | Low |
| **High** | Delete dead prototype files | Trivial |
| **Medium** | Extract cost estimation to `services/cost.py` | Low |
| **Medium** | Move `_MRT_STATIONS` to JSON fixture | Low |
| **Medium** | Parse Google response to typed model | Medium |
| **Medium** | Add `useFetch` / React Query in frontend | Medium |
| **Low** | Replace `settings.json` with SQLite | Medium |
| **Low** | Restrict CORS for production | Trivial |
| **Low** | Add end-to-end integration test | Medium |

---

### AI's Closing Assessment

> *"The codebase is notably above average for a university lab project — real async API integration, thoughtful fallback handling, and a working scoring model are not trivial to get right. The main growth area is decomposing `routes.py` and eliminating scattered magic numbers, which would make the system much easier to maintain and extend."*

---

## 3.3.4 — Reflections

### Reflection on 3.3.2 — AI-Assisted Class Regeneration

**How we prompted the assistant and materials provided:**
We deleted `routing.py` entirely and gave Claude Code CLI a single structured prompt asking it to regenerate the file from scratch. We named six reference files for it to read: `routes.py` (to infer the call interface), `schemas.py` (entity types), `scoring.py` (helpers to delegate to), `skeleton.md` (architecture documentation), `class_diagram.puml` (UML method signatures), and `test_routing.py` (50 unit tests specifying expected behaviour). The test file was the most important input because it precisely encodes what each function must return for a given input.

**Whether iteration was required:**
No iteration was needed to generate the file — the agent produced a complete, syntactically valid implementation in a single response. However, running the test suite revealed 7 failures, which required manual fixes to align specific constants and dictionary key names with the original implementation.

**Outcome:**
43 out of 50 tests passed immediately. All 7 failures were in low-level implementation details — fare bracket values, taxi rate constants, return dictionary key names, and whether the driving branch attaches a delay indicator to the output step. None of the failures were in the core logic: risk aggregation, score normalisation, route ranking, explanation generation, and realistic time computation were all regenerated correctly.

**Whether the outcome met expectations:**
Largely yes. The result confirmed that an AI agent can reliably reconstruct complex algorithmic logic from design documents and tests alone, but cannot recover exact numeric constants or API contract details that only exist in the original source code. This is consistent with what the lab instructions anticipate when they suggest providing "the original class file with just the function bodies deleted" as a fallback — doing so would have made the constants visible and likely produced a 50/50 pass on the first attempt. The exercise highlighted that tests are the single most valuable input for AI-assisted regeneration: without them, there would have been no objective way to measure whether the output was correct.

---

### Reflection on 3.3.3 — AI Opinion on Codebase Quality

**Experiment chosen:**
We asked the AI assistant to read the entire codebase and provide an opinion on code quality with concrete refactoring suggestions.

**How we prompted the assistant and materials provided:**
We used a single natural-language prompt asking the AI to read the full project folder, understand the project from the Lab 3 PDF, and then comment on quality and suggest refactoring. No additional materials were explicitly curated — the agent was given access to the full repository and navigated it autonomously using its `Explore` subagent, reading backend services, API routes, frontend components, configuration files, and the SRS document.

**Whether iteration was required:**
No iteration was required. The agent returned a comprehensive, structured review in a single response. The review was then saved to this document for lab submission.

**Outcome:**
The AI produced an overall quality rating of B+ with clear justification, identified 10 concrete refactoring issues (each with a code example and priority rating), and summarised them in a priority matrix. The review was accurate and specific — it correctly identified the 865-line `routes.py` as a structural problem, flagged the scattered `Low=1, Medium=2, High=3` constants as a maintenance risk, and called out the flat-file `settings.json` persistence as a scalability hazard. All three of these issues were later confirmed as real during the 3.3.2 exercise (the magic numbers issue directly caused 7 test failures when constants were regenerated at slightly different values).

**Whether the outcome met expectations:**
Yes, and in some ways it exceeded them. The agent did not produce generic advice — it referenced specific file names, line counts, and implementation patterns from our actual codebase (e.g., naming `_MRT_STATIONS`, the taxi meter logic, and `settings.json` by name). The one limitation was that the agent could not structurally parse the PDF SRS, so the review was grounded in the code rather than a systematic requirements-traceability analysis. Providing key functional requirements as plain text alongside the prompt would have enabled deeper coverage. Despite this, the exercise demonstrated that AI assistants are highly effective at performing fast, impartial code reviews — surfacing issues that developers familiar with the code might overlook due to familiarity bias.
