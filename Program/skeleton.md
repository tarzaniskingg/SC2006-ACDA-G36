# SGTravelBud — Implementation Skeleton

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Package Structure](#2-package-structure)
3. [Enumerations](#3-enumerations)
4. [Entity Classes](#4-entity-classes)
5. [Control Classes](#5-control-classes)
6. [Boundary (UI) Classes](#6-boundary-ui-classes)
7. [Service & Provider Classes](#7-service--provider-classes)
8. [Backend API Routes](#8-backend-api-routes)
9. [Frontend Component Tree](#9-frontend-component-tree)
10. [Import Structure](#10-import-structure)
11. [Class Diagram ↔ Implementation Mapping](#11-class-diagram--implementation-mapping)
12. [Key Algorithms Skeleton](#12-key-algorithms-skeleton)
13. [Data Flow Walkthrough](#13-data-flow-walkthrough)



## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                 │
│  Boundary Layer                                             │
│  TripOriginUI  RouteResultUI  PreferenceProfileUI  SettingsUI│
└──────────────────────────┬──────────────────────────────────┘
                           │  REST (JSON over HTTP)
┌──────────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI / Python)                 │
│  Control Layer                                              │
│  TripController  RouteScoringController  DataFetchController │
│  LocationController  PreferenceProfileController            │
│                                                             │
│  Entity Layer                                               │
│  TripRequest  RouteOption  RouteSegment  UserPreferenceProfile│
│  TransportDataSource  TransportDataProvider                 │
│                                                             │
│  External Clients                                           │
│  Google Directions API   LTA DataMall   NEA Weather         │
└─────────────────────────────────────────────────────────────┘
```


## 2. Package Structure

```
Program/
├── backend/
│   ├── main.py                     # FastAPI app, CORS, startup
│   ├── api/
│   │   └── routes.py               # All HTTP endpoints
│   ├── core/
│   │   └── config.py               # Config / env vars (AppConfig)
│   ├── models/
│   │   └── schemas.py              # Pydantic schemas (Entity classes)
│   ├── services/                   # Control layer
│   │   ├── routing.py              # RouteScoringController logic
│   │   ├── scoring.py              # Scoring / normalisation helpers
│   │   ├── assessment.py           # DataFetchController risk logic
│   │   ├── caching.py              # TTLCache (TransportDataSource)
│   │   ├── weather.py              # NEA weather service
│   │   └── erp.py                  # ERP gantry calculation
│   ├── clients/                    # TransportDataProvider adapters
│   │   ├── google.py               # Google Directions wrapper
│   │   ├── lta.py                  # LTA DataMall wrapper
│   │   └── nea.py                  # NEA forecast wrapper
│   └── fixtures/
│       ├── google_routes_sample.json
│       └── erp_gantries.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Root router + global state
│   │   ├── main.jsx                # ReactDOM entry point
│   │   ├── pages/                  # Boundary (UI) classes
│   │   │   ├── MainView.jsx        # TripOriginUI + RouteResultUI combined
│   │   │   ├── SearchPage.jsx      # TripOriginUI search form
│   │   │   ├── ResultsPage.jsx     # RouteResultUI route list
│   │   │   ├── ScoringPage.jsx     # Score breakdown visualisation
│   │   │   └── SettingsPage.jsx    # PreferenceProfileUI + SettingsUI
│   │   ├── components/             # Reusable UI elements
│   │   │   ├── RouteCard.jsx       # Single RouteOption display
│   │   │   ├── RouteMap.jsx        # Leaflet map
│   │   │   ├── PlaceInput.jsx      # Autocomplete (LocationController)
│   │   │   ├── TimeCompare.jsx     # Departure time comparison table
│   │   │   ├── RiskBadge.jsx       # RiskCategory badge
│   │   │   ├── CrowdingHeatmap.jsx # Crowding timeline
│   │   │   ├── BottomNav.jsx       # Navigation bar
│   │   │   └── mapTiles.js         # CartoDB tile config
│   │   └── utils/
│   │       ├── api.js              # API client functions
│   │       └── helpers.js          # Formatting, colour mapping
│   └── index.html
│
├── googlemaps_api.py               # Legacy Google wrapper
├── lta_api.py                      # Legacy LTA wrapper
├── fetch.py                        # Legacy assessment stub
├── requirements.txt
└── SKELETON.md                     # This file
```


## 3. Enumerations

### 3.1 `TransportMode` — `backend/models/schemas.py`

```python
class TransportMode(str, Enum):
    MRT_ONLY  = "MRT_ONLY"
    MRT_BUS   = "MRT_BUS"
    TAXI      = "TAXI"
    DRIVE     = "DRIVE"
```

### 3.2 `RiskCategory` — `backend/models/schemas.py`

```python
class RiskCategory(str, Enum):
    LOW     = "LOW"
    MEDIUM  = "MEDIUM"
    HIGH    = "HIGH"
    UNKNOWN = "UNKNOWN"
```

### 3.3 `OptimisationCriterion` — `backend/models/schemas.py`

```python
class OptimisationCriterion(str, Enum):
    TRAVEL_TIME   = "TRAVEL_TIME"
    DELAY_RISK    = "DELAY_RISK"
    CROWDING_RISK = "CROWDING_RISK"
    COST          = "COST"
```

### 3.4 `PreferenceLevel` — `backend/models/schemas.py`

```python
class PreferenceLevel(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"
```

### 3.5 `DataSourceType` — `backend/models/schemas.py`

```python
class DataSourceType(str, Enum):
    MRT_CROWD          = "MRT_CROWD"
    MRT_DELAY          = "MRT_DELAY"
    TAXI_AVAILABILITY  = "TAXI_AVAILABILITY"
    CARPARK_AVAILABILITY = "CARPARK_AVAILABILITY"
```


## 4. Entity Classes

### 4.1 `TripRequest` — `backend/models/schemas.py`

Maps to: `TripRequest` in class diagram

```python
class TripRequest(BaseModel):
    # Attributes from class diagram
    origin: Location                          
    destination: Location                     
    departureTime: Optional[datetime]  
    activeProfile: Optional[UserPreferenceProfile]

    # Extended attributes (implementation)
    mode_preference: Optional[TransportMode]
    max_walk_min: Optional[int]               
    max_transfers: Optional[int]
    max_budget: Optional[float]
    weight_time: float = 0.4
    weight_cost: float = 0.2
    weight_risk: float = 0.3
    weight_comfort: float = 0.1

    # Methods
    def setOrigin(self, location: Location) -> None: ...
    def setDestination(self, location: Location) -> None: ...
    def setDepartureTime(self, time: datetime) -> None: ...
```

### 4.2 `UserPreferenceProfile` — `backend/models/schemas.py`

Maps to: `UserPreferenceProfile` in class diagram

```python
class UserPreferenceProfile(BaseModel):
    # Attributes from class diagram
    walkingTolerance: int        # minutes
    maxTransfers: int
    maxBudget: float
    concessionBudget: float
    hybridTaxiEnabled: bool
    hybridTaxiMaxDuration: int   # minutes
    hybridTaxiMaxBudget: float

    # Methods
    def detectFirstTimeUser(self) -> bool: ...
```

### 4.3 `DefaultPreferenceProfile` — `backend/models/schemas.py`

Subclass / factory of `UserPreferenceProfile`:

```python
class DefaultPreferenceProfile(UserPreferenceProfile):
    walkingTolerance: int = 10
    maxTransfers: int = 3
    maxBudget: float = 5.0
    concessionBudget: float = 2.0
    hybridTaxiEnabled: bool = False
    hybridTaxiMaxDuration: int = 30
    hybridTaxiMaxBudget: float = 15.0
```

### 4.4 `TripLevelOverride` — `backend/models/schemas.py`

Per-trip overrides that take precedence over the stored profile:

```python
class TripLevelOverride(BaseModel):
    weight_time: Optional[float]
    weight_cost: Optional[float]
    weight_risk: Optional[float]
    weight_comfort: Optional[float]
    mode_exclude: Optional[List[TransportMode]]
```

### 4.5 `RouteOption` — `backend/models/schemas.py`

Maps to: `RouteOption` in class diagram

```python
class RouteOption(BaseModel):
    # Attributes from class diagram
    totalTravelTime: int               # minutes
    totalCost: float                   # SGD
    delayRiskCategory: RiskCategory
    crowdingRiskCategory: RiskCategory
    delayRiskScore: int                # 0-100
    crowdingRiskScore: int             # 0-100
    compositeScore: float              # 0-1, lower = better
    explanation: str
    isFallback: bool
    rank: int                          # 1 = best

    # Extended attributes (implementation)
    steps: List[RouteStep]
    polyline: Optional[str]
    weather_rain_on_route: bool
    erp_total: float
    frequency_risk: Optional[RiskCategory]
    realistic_wait_min: int

    # Methods
    def getExplanation(self) -> str: ...
    def getRank(self) -> int: ...
    def isFallback(self) -> bool: ...
    def getCompositeScore(self) -> float: ...
```

### 4.6 `RouteSegment` — `backend/models/schemas.py`

Maps to: `RouteSegment` in class diagram

```python
class RouteSegment(BaseModel):
    # Attributes from class diagram
    mode: TransportMode
    segmentTravelTime: int       # minutes
    segmentCost: float           # SGD
    delayRiskCategory: RiskCategory
    crowdingRiskCategory: RiskCategory
    isFallback: bool
    attribute: float             # raw numeric risk score

    # Extended attributes (implementation)
    start_stop: Optional[str]
    end_stop: Optional[str]
    line: Optional[str]          # MRT line name
    service_no: Optional[str]    # Bus service number
    num_stops: int = 0
    frequency_headway_min: Optional[int]

    # Methods
    def getCrowdingRiskCategory(self) -> RiskCategory: ...
    def getDelayRiskCategory(self) -> RiskCategory: ...
    def isFallback(self) -> bool: ...
    def getDuration(self) -> int: ...
```

### 4.7 `TransportDataSource` — `backend/services/caching.py`

Maps to: `TransportDataSource` in class diagram

```python
class TransportDataSource:
    # Attributes from class diagram
    sourceType: DataSourceType
    retrievalTimeStamp: datetime
    freshnessThreshold: int      # seconds
    isFallback: bool
    rawData: Any                 # JSON payload from API

    # Methods
    def isFresh(self) -> bool:
        """Return True if age < freshnessThreshold."""
        ...

    def getAge(self) -> int:
        """Seconds since retrievalTimeStamp."""
        ...

    def markFallback(self) -> None:
        """Set isFallback = True, log warning."""
        ...

    def getData(self) -> Any:
        """Return rawData."""
        ...
```


## 5. Control Classes

### 5.1 `TripController` — `backend/api/routes.py`

Maps to: `TripController` in class diagram
**Entry point** for the main `/routes` endpoint.

```python
class TripController:
    """
    Orchestrates the full trip request lifecycle.
    Called by GET /routes.
    """

    def initiateTrip(self) -> None:
        """
        Parse query params → build TripRequest →
        call DataFetchController → call RouteScoringController.
        """
        ...

    def applyPreferenceProfile(self) -> None:
        """Merge UserPreferenceProfile + TripLevelOverride into weights."""
        ...

    def validateInputs(self) -> None:
        """
        Check origin/destination not empty, lat/lng within Singapore,
        departure time not in the past. Raise HTTP 422 on failure.
        """
        ...

    def confirmRequest(self, r: TripRequest) -> None:
        """Attach validated TripRequest to current context."""
        ...

    def setDepartureTime(self, t: datetime) -> None:
        """Default to now() if not provided."""
        ...

    def refreshRoutes(self, r: TripRequest) -> None:
        """Invalidate cache entries relevant to this trip, re-fetch."""
        ...
```

**Implementation location:** `backend/api/routes.py` → `GET /routes` handler
**Delegates to:** `RouteScoringController.generateRoutes()`, `DataFetchController.fetchAllTransportData()`

### 5.2 `RouteScoringController` — `backend/services/routing.py` + `backend/services/scoring.py`

Maps to: `RouteScoringController` in class diagram

```python
class RouteScoringController:
    """
    Transforms raw Google route options into ranked RouteOption objects.
    """

    def aggregateSegmentRisks(self) -> None:
        """
        Walk RouteSegment list; apply UNKNOWN-wins precedence rule:
          UNKNOWN > HIGH > MEDIUM > LOW
        """
        ...

    def convertRiskToNumeric(self) -> None:
        """Map RiskCategory enum → numeric 0-100 score."""
        ...

    def normaliseAttributes(self) -> None:
        """
        Min-max normalise [time, cost, risk, comfort] across all candidate routes.
        Edge case: all equal → assign 0.5.
        """
        ...

    def computeCompositeScore(self) -> None:
        """
        composite = w_time*t_norm + w_cost*c_norm + w_risk*r_norm + w_comfort*cf_norm
        Lower score = better route.
        """
        ...

    def rankRoutes(self) -> None:
        """Sort ascending by compositeScore; apply tie-breaking."""
        ...

    def applyTieBreaking(self) -> None:
        """Deterministic secondary sort: time → cost → mode order."""
        ...

    def generateRoutes(self, r: TripRequest) -> List[RouteOption]:
        """
        Main pipeline:
          1. Call Google Directions API (transit + driving)
          2. For each raw route: build RouteSegment list via build_route_steps()
          3. Assess each segment (DataFetchController.assessDelayRisks / assessCrowdingRisks)
          4. aggregateSegmentRisks → normalise → score → rank
          5. Return top-3 RouteOption objects
        """
        ...

    def generateExplanation(self, r: RouteOption) -> str:
        """
        Produce human-readable string, e.g.:
          'Best time: 22 min transit via MRT (East West Line). Low delay risk.'
        """
        ...

    def handleNoRoutes(self) -> None:
        """Return fallback fixture routes; mark isFallback=True."""
        ...
```

### 5.3 `DataFetchController` — `backend/services/assessment.py`

Maps to: `DataFetchController` in class diagram

```python
class DataFetchController:
    """
    Fetches, caches, and assesses all live transport data.
    Wraps LTA DataMall, NEA, and Google clients behind a TTL cache.
    """

    def fetchAllTransportData(self) -> None:
        """
        Populate TTLCache with:
          - LTA bus arrivals (TTL 30s)
          - LTA PCD MRT crowding (TTL 60s)
          - LTA train service alerts (TTL 120s)
          - LTA traffic speed bands (TTL 60s)
          - NEA 2-hour weather forecast (TTL 600s)
        """
        ...

    def fetchMRTData(self) -> TransportDataSource:
        """Fetch PCDForecast + TrainServiceAlerts via lta_client."""
        ...

    def fetchTaxiData(self) -> TransportDataSource:
        """Fetch TaxiAvailability via lta_client."""
        ...

    def fetchCarparkData(self) -> TransportDataSource:
        """Fetch CarparkAvailability via lta_client."""
        ...

    def checkFreshness(self) -> None:
        """
        Iterate TTLCache; for any expired entry call applyFallback().
        Called at the start of each /routes request.
        """
        ...

    def applyFallback(self) -> None:
        """
        Replace expired/missing data with fixture JSON.
        Mark affected TransportDataSource.isFallback = True.
        """
        ...

    def refreshData(self) -> None:
        """
        Invalidate entire TTLCache (called by POST /refresh).
        Next request triggers fresh fetchAllTransportData().
        """
        ...

    def getLatestData(self, t: DataSourceType) -> TransportDataSource:
        """Return cached TransportDataSource for given type, fetching if stale."""
        ...

    def assessDelayRisks(self, s: RouteSegment) -> RiskCategory:
        """
        For MRT segment: parse service alerts → LOW/MEDIUM/HIGH/UNKNOWN.
        For bus segment: compare headway vs threshold.
        For drive segment: check traffic speed band.
        """
        ...

    def assessCrowdingRisks(self, s: RouteSegment) -> RiskCategory:
        """
        For MRT: query PCDForecast for station + time window.
        For bus: parse BusArrival Load field (SEA/SDA/LSD → LOW/MEDIUM/HIGH).
        """
        ...

    def markFallbackRoutes(self, routes: List[RouteOption]) -> List[RouteOption]:
        """Set RouteOption.isFallback if any segment used fallback data."""
        ...
```

### 5.4 `LocationController` — `backend/api/routes.py` (partial) + `frontend/src/components/PlaceInput.jsx`

Maps to: `LocationController` in class diagram

```python
class LocationController:
    """
    Handles origin/destination resolution.
    Backend side: geocoding validation.
    Frontend side: PlaceInput autocomplete via Nominatim.
    """

    def getOrigin(self) -> Location: ...
    def getDestination(self) -> Location: ...
    def validateLocation(self) -> bool:
        """Confirm coords fall within Singapore bounding box."""
        ...

    def fetchSuggestions(self, query: str) -> List[Location]:
        """
        Debounced call to Nominatim /search.
        Returns list of {display_name, lat, lon, type} objects.
        """
        ...

    def selectFromMap(self, coor: Coordinates) -> Location:
        """Resolve lat/lng tap on map to a Location."""
        ...

    def requestGPSLocation(self) -> Location:
        """
        Browser Geolocation API → reverse-geocode via Nominatim.
        """
        ...

    def requestPermission(self) -> bool:
        """Check/request browser geolocation permission."""
        ...

    def isWithinSingapore(self, location: Location) -> bool:
        """
        Bounding box check:
          lat in [1.15, 1.48], lng in [103.6, 104.1]
        """
        ...
```


### 5.5 `PreferenceProfileController` — `backend/api/routes.py` (settings endpoints)

Maps to: `PreferenceProfileController` in class diagram

```python
class PreferenceProfileController:
    """
    Manages persistence and validation of UserPreferenceProfile.
    """

    def mapImportanceToWeight(self) -> None:
        """
        Convert PreferenceLevel enum to numeric weight:
          LOW=0.1, MEDIUM=0.3, HIGH=0.5
        Then normalise so weights sum to 1.0.
        """
        ...

    def normaliseWeights(self) -> None:
        """Divide each weight by sum(weights)."""
        ...

    def validateModeConstraints(self) -> None:
        """
        Ensure at least one TransportMode is enabled.
        Raise validation error if all disabled.
        """
        ...

    def saveDefaultProfile(self) -> None:
        """Persist DefaultPreferenceProfile to settings store on first launch."""
        ...

    def loadProfile(self) -> UserPreferenceProfile:
        """Read profile from GET /settings response."""
        ...

    def updateProfile(self, profile: UserPreferenceProfile) -> None:
        """Write profile via PUT /settings."""
        ...

    def detectFirstTimeUser(self) -> bool:
        """Return True if no profile found in settings store."""
        ...

    def saveSettings(self, setting: UserPreferenceProfile) -> None:
        """Persist settings JSON to file / in-memory store."""
        ...
```

## 6. Boundary (UI) Classes

### 6.1 `TripOriginUI` — `frontend/src/pages/SearchPage.jsx` + `frontend/src/pages/MainView.jsx`

Maps to: `TripOriginUI` in class diagram

```jsx
// SearchPage.jsx / MainView.jsx

function TripOriginUI() {
    // State
    const [origin, setOrigin] = useState(null);
    const [destination, setDestination] = useState(null);
    const [departureTime, setDepartureTime] = useState(null);

    // Methods from class diagram
    function showOriginMap() { /* Render Leaflet map for point selection */ }
    function showOriginField() { /* Render PlaceInput for origin */ }
    function showDestinationField() { /* Render PlaceInput for destination */ }
    function showSuggestions(l) { /* Pass suggestions to PlaceInput dropdown */ }
    function showDeparturePicker() { /* Render datetime-local input */ }
    function showPreferenceSummary(p) { /* Inline weight chips display */ }
    function showValidationError(msg) { /* Red toast / inline error */ }
    function onConfirmClicked() {
        /* Validate → navigate to ResultsPage with query params */
    }

    return ( /* JSX */ );
}
```

### 6.2 `RouteResultUI` — `frontend/src/pages/ResultsPage.jsx` + `frontend/src/components/RouteCard.jsx`

Maps to: `RouteResultUI` in class diagram

```jsx
function RouteResultUI({ routes }) {
    // Methods from class diagram
    function displayRoutes(routes) {
        /* Map over RouteOption array → render RouteCard components */
    }
    function showFallbackWarning(msg) {
        /* Yellow banner: "Live data unavailable — showing estimated results" */
    }
    function showNoRouteMessage() {
        /* Empty state with retry button */
    }
    function showExplanation(e) {
        /* Expandable explanation text from RouteOption.explanation */
    }

    return ( /* JSX */ );
}
```

### 6.3 `PreferenceProfileUI` — `frontend/src/pages/SettingsPage.jsx`

Maps to: `PreferenceProfileUI` in class diagram

```jsx
function PreferenceProfileUI() {
    // Methods from class diagram
    function displayWeightSliders() {
        /* Four sliders: Time / Cost / Risk / Comfort (0-100), auto-normalise */
    }
    function displayModeToggles() {
        /* Toggle switches: MRT Only / MRT+Bus / Taxi / Drive */
    }
    function displayConstraintForm() {
        /* Max walk, max transfers, max budget inputs */
    }
    function showValidationError(msg) {
        /* Inline red text below invalid field */
    }
    function onSaveClicked() {
        /* PUT /settings → show notifySaved() */
    }
    function notifySaved() {
        /* Green toast "Settings saved" */
    }

    return ( /* JSX */ );
}
```

### 6.4 `SettingsUI` — `frontend/src/pages/SettingsPage.jsx`

Maps to: `SettingsUI` in class diagram

```jsx
function SettingsUI() {
    // Methods from class diagram
    function showProfileEditor() { /* Render PreferenceProfileUI sub-section */ }
    function showLanguageSelector() { /* Dropdown: English / 中文 */ }
    function onSaveClicked() { /* PUT /settings */ }
    function onResetClicked() { /* Restore DefaultPreferenceProfile */ }

    return ( /* JSX */ );
}
```

## 7. Service & Provider Classes

### 7.1 `LocationService` — `backend/clients/google.py` + frontend Nominatim calls

Maps to: `LocationService` in class diagram

```python
class LocationService:
    """Resolves device GPS position to a Location object."""

    def getCurrentLocation(self) -> Location:
        """
        Backend: not needed (GPS is browser-side).
        Frontend: navigator.geolocation.getCurrentPosition()
                  → reverse-geocode via Nominatim.
        Returns: { lat, lng, display_name }
        """
        ...
```


### 7.2 `TransportDataProvider` — `backend/clients/lta.py`, `backend/clients/nea.py`, `backend/clients/google.py`

Maps to: `TransportDataProvider` in class diagram

```python
class TransportDataProvider:
    """
    Abstract adapter over all external transport APIs.
    Each concrete client (LTA, NEA, Google) implements fetchData().
    """

    def fetchData(self, trip: TripRequest) -> TransportDataSource:
        """
        Perform HTTP request to external API.
        Wrap response in TransportDataSource with correct DataSourceType.
        On network error: return fixture-backed TransportDataSource with isFallback=True.
        """
        ...

# Concrete implementations:

class LTADataProvider(TransportDataProvider):
    BASE_URL = "http://datamall2.mytransport.sg/ltaodataservice"
    # Endpoints: BusArrivalv2, PCDForecast, TrainServiceAlerts,
    #            EstTravelTimes, TaxiAvailability, TrafficSpeedBands,
    #            BusStops, CarParkAvailabilityv2

class NEAWeatherProvider(TransportDataProvider):
    BASE_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    # Returns rain/no-rain per 24 forecast areas

class GoogleDirectionsProvider(TransportDataProvider):
    # Calls googlemaps.Client.directions() with transit + driving modes
    # Returns up to 3 route alternatives per mode
```

## 8. Backend API Routes

All routes are in `backend/api/routes.py`.

| Method | Path | Controller | Description |
|--------|------|-----------|-------------|
| `GET` | `/routes` | `TripController.initiateTrip()` | Ranked route options (2-3 results) |
| `GET` | `/assessment` | `DataFetchController.assessDelayRisks/assessCrowdingRisks()` | Segment-level risk breakdown |
| `GET` | `/datasets` | `DataFetchController.checkFreshness()` | Cache freshness + fallback status |
| `POST` | `/refresh` | `DataFetchController.refreshData()` | Invalidate all cached datasets |
| `GET` | `/settings` | `PreferenceProfileController.loadProfile()` | Load user preference profile |
| `PUT` | `/settings` | `PreferenceProfileController.saveSettings()` | Persist user preference profile |
| `GET` | `/routes/compare` | `TripController` | Departure time comparison (Morning/Now/Evening) |
| `GET` | `/crowding/heatmap` | `DataFetchController.assessCrowdingRisks()` | 24h crowding timeline |
| `GET` | `/gmaps/directions` | `GoogleDirectionsProvider.fetchData()` | Raw Google Directions passthrough |
| `GET` | `/health` | — | Liveness probe |

### Route Handler Skeleton

```python
# backend/api/routes.py

router = APIRouter()

@router.get("/routes", response_model=RoutesResponse)
async def get_routes(
    origin: str,
    destination: str,
    mode: Optional[str] = None,
    departure_time: Optional[str] = None,
    weight_time: float = 0.4,
    weight_cost: float = 0.2,
    weight_risk: float = 0.3,
    weight_comfort: float = 0.1,
    max_walk_min: Optional[int] = None,
    max_transfers: Optional[int] = None,
    max_budget: Optional[float] = None,
):
    # 1. Build TripRequest
    trip = TripRequest(origin=origin, destination=destination, ...)

    # 2. DataFetchController.checkFreshness() — refresh stale data
    data_controller = DataFetchController()
    data_controller.checkFreshness()

    # 3. RouteScoringController.generateRoutes(trip)
    scoring_controller = RouteScoringController()
    routes: List[RouteOption] = scoring_controller.generateRoutes(trip)

    # 4. Return ranked results
    return RoutesResponse(routes=routes)
```


## 9. Frontend Component Tree

```
App.jsx
├── Router
│   ├── "/" → MainView.jsx
│   │   ├── SearchPage.jsx          ← TripOriginUI
│   │   │   ├── PlaceInput.jsx      ← LocationController (frontend)
│   │   │   ├── PlaceInput.jsx
│   │   │   └── [weight sliders, constraint form]
│   │   ├── RouteMap.jsx            ← Leaflet map
│   │   ├── ResultsPage.jsx         ← RouteResultUI
│   │   │   ├── RouteCard.jsx × N   ← RouteOption display
│   │   │   │   ├── RiskBadge.jsx   ← RiskCategory
│   │   │   │   └── CrowdingHeatmap.jsx
│   │   │   └── TimeCompare.jsx     ← Departure comparison
│   │   └── BottomNav.jsx
│   │
│   ├── "/scoring" → ScoringPage.jsx
│   │   └── [4-dimension score breakdown charts]
│   │
│   └── "/settings" → SettingsPage.jsx
│       ├── PreferenceProfileUI     ← weight sliders, mode toggles
│       └── SettingsUI              ← language, reset, dataset status
```


## 10. Import Structure

### Backend

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import AppConfig

# backend/api/routes.py
from fastapi import APIRouter, Query, HTTPException
from backend.models.schemas import (
    TripRequest, RouteOption, RoutesResponse,
    AssessmentResponse, DatasetsStatusResponse,
    Settings, CompareResponse, CrowdingHeatmapResponse,
    RiskCategory, TransportMode
)
from backend.services.routing import rank_routes, build_route_steps
from backend.services.scoring import composite_score, normalize, explain
from backend.services.assessment import assess_segments_from_google_route
from backend.services.caching import ttl_cache
from backend.services.weather import get_weather_risk
from backend.services.erp import calculate_erp
from backend.clients.google import get_google_routes
from backend.clients.lta import LTAClient
from backend.clients.nea import NEAClient

# backend/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

# backend/services/scoring.py
from typing import List
from backend.models.schemas import RouteOption, RiskCategory

# backend/services/routing.py
from backend.services.scoring import composite_score, normalize
from backend.services.assessment import assess_segments_from_google_route
from backend.clients.google import get_google_routes
from backend.models.schemas import RouteOption, RouteSegment, TripRequest
```

### Frontend

```js
// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainView from './pages/MainView'
import ScoringPage from './pages/ScoringPage'
import SettingsPage from './pages/SettingsPage'

// src/utils/api.js
// All fetch() calls to /api/* (proxied by Vite dev server)
export async function fetchRoutes(params) { ... }
export async function fetchDatasets() { ... }
export async function refreshCache() { ... }
export async function fetchSettings() { ... }
export async function fetchCompare(params) { ... }
export async function fetchCrowdingHeatmap(station) { ... }
export async function geocode(query) { ... }

// src/components/RouteCard.jsx
import RiskBadge from './RiskBadge'
import CrowdingHeatmap from './CrowdingHeatmap'
import { formatDuration, formatCost, modeColor } from '../utils/helpers'

// src/components/RouteMap.jsx
import { MapContainer, TileLayer, Polyline, Marker } from 'react-leaflet'
import { cartoDB } from './mapTiles'
```


## 11. Class Diagram ↔ Implementation Mapping

| Class Diagram Class | Stereotype | Implementation File(s) |
|--------------------|-----------|----------------------|
| `TripRequest` | Entity | `backend/models/schemas.py` → `TripRequest` Pydantic model |
| `UserPreferenceProfile` | Entity | `backend/models/schemas.py` → `Settings` Pydantic model |
| `DefaultPreferenceProfile` | Entity | Default values in `Settings` + `GET /settings` defaults |
| `TripLevelOverride` | Entity | Query params on `GET /routes` (weight_*, max_*) |
| `RouteOption` | Entity | `backend/models/schemas.py` → `RouteOption` Pydantic model |
| `RouteSegment` | Entity | `backend/models/schemas.py` → `RouteStep` Pydantic model |
| `TransportDataSource` | Entity | `backend/services/caching.py` → `CacheItem` / `TTLCache` |
| `TransportDataProvider` | Service | `backend/clients/lta.py`, `google.py`, `nea.py` |
| `LocationService` | Service | `frontend/src/components/PlaceInput.jsx` (Nominatim) |
| `TripController` | Control | `backend/api/routes.py` → `get_routes()` handler |
| `RouteScoringController` | Control | `backend/services/routing.py` + `scoring.py` |
| `DataFetchController` | Control | `backend/services/assessment.py` + `caching.py` |
| `LocationController` | Control | `backend/api/routes.py` (validate) + `PlaceInput.jsx` |
| `PreferenceProfileController` | Control | `backend/api/routes.py` → `/settings` handlers |
| `TripOriginUI` | Boundary | `frontend/src/pages/SearchPage.jsx` + `MainView.jsx` |
| `RouteResultUI` | Boundary | `frontend/src/pages/ResultsPage.jsx` + `RouteCard.jsx` |
| `PreferenceProfileUI` | Boundary | `frontend/src/pages/SettingsPage.jsx` (top section) |
| `SettingsUI` | Boundary | `frontend/src/pages/SettingsPage.jsx` (full page) |
| `TransportMode` | Enumeration | `backend/models/schemas.py` → `TransportMode` Enum |
| `RiskCategory` | Enumeration | `backend/models/schemas.py` → `RiskCategory` Enum |
| `OptimisationCriterion` | Enumeration | Implicit in weight params (`weight_time` etc.) |
| `PreferenceLevel` | Enumeration | `Settings.default_weight_*` fields |
| `DataSourceType` | Enumeration | Cache key strings in `TTLCache` |


## 12. Key Algorithms Skeleton

### 12.1 Composite Scoring (`backend/services/scoring.py`)

```python
def normalize(values: List[float]) -> List[float]:
    """
    Min-max normalisation.
    Edge: all equal → return [0.5, 0.5, ...]
    """
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def compute_risk(delay: RiskCategory, crowding: RiskCategory) -> float:
    """
    UNKNOWN wins, then HIGH, MEDIUM, LOW.
    Returns numeric 0-100.
    """
    ORDER = {RiskCategory.UNKNOWN: 100, RiskCategory.HIGH: 75,
             RiskCategory.MEDIUM: 40, RiskCategory.LOW: 10}
    return max(ORDER[delay], ORDER[crowding])


def composite_score(
    time_norm: float, cost_norm: float,
    risk_norm: float, comfort_norm: float,
    w_time: float, w_cost: float, w_risk: float, w_comfort: float
) -> float:
    """Weighted sum; lower = better."""
    return (w_time * time_norm + w_cost * cost_norm
            + w_risk * risk_norm + w_comfort * comfort_norm)


def tie_break_key(route: RouteOption) -> tuple:
    """Secondary sort when compositeScore equal."""
    mode_order = {TransportMode.MRT_ONLY: 0, TransportMode.MRT_BUS: 1,
                  TransportMode.DRIVE: 2, TransportMode.TAXI: 3}
    return (route.totalTravelTime, route.totalCost,
            mode_order.get(route.primary_mode, 99))
```


### 12.2 Risk Aggregation (`backend/services/routing.py`)

```python
def aggregate_route_risks(
    segments: List[RouteSegment]
) -> tuple[RiskCategory, RiskCategory]:
    """
    UNKNOWN-wins precedence for delay and crowding independently.
    Return (delay_category, crowding_category) for the whole route.
    """
    PRECEDENCE = [RiskCategory.UNKNOWN, RiskCategory.HIGH,
                  RiskCategory.MEDIUM, RiskCategory.LOW]

    def worst(risks: List[RiskCategory]) -> RiskCategory:
        for level in PRECEDENCE:
            if level in risks:
                return level
        return RiskCategory.UNKNOWN

    delay_risks    = [s.delayRiskCategory    for s in segments]
    crowding_risks = [s.crowdingRiskCategory for s in segments]
    return worst(delay_risks), worst(crowding_risks)
```


### 12.3 Realistic Time Estimation (`backend/services/routing.py`)

```python
def compute_realistic_time(
    google_duration_min: int,
    segments: List[RouteSegment]
) -> int:
    """
    Add bus waiting buffer based on headway data (Feature 5).
    If any bus segment has headway > 15 min, add half-headway as buffer.
    """
    extra = 0
    for seg in segments:
        if seg.mode == TransportMode.MRT_BUS and seg.frequency_headway_min:
            if seg.frequency_headway_min > 15:
                extra += seg.frequency_headway_min // 2
    return google_duration_min + extra
```


### 12.4 ERP Calculation (`backend/services/erp.py`)

```python
def decode_polyline(encoded: str) -> List[tuple[float, float]]:
    """Decode Google encoded polyline to list of (lat, lng) pairs."""
    ...

def calculate_erp(
    polyline: str,
    departure_time: datetime,
    gantries: List[dict]  # from erp_gantries.json
) -> float:
    """
    1. Decode polyline to coordinate list.
    2. For each gantry, check if any polyline point is within 80m.
    3. Look up charge rate for (gantry_id, vehicle_type, time_band).
    4. Return total SGD cost.
    """
    ...
```


### 12.5 TTL Cache (`backend/services/caching.py`)

```python
class CacheItem:
    data: Any
    fetched_at: float      # time.time()
    ttl: int               # seconds
    is_fallback: bool

    def is_expired(self) -> bool:
        return time.time() - self.fetched_at > self.ttl


class TTLCache:
    _store: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item and not item.is_expired():
            return item.data
        return None

    def set(self, key: str, data: Any, ttl: int, fallback: bool = False) -> None:
        self._store[key] = CacheItem(data, time.time(), ttl, fallback)

    def invalidate_all(self) -> None:
        self._store.clear()

    def status(self) -> Dict[str, dict]:
        """Return freshness + fallback status for GET /datasets."""
        ...
```


## 13. Data Flow Walkthrough

### Use Case: User requests a route

```
1. User fills SearchPage (TripOriginUI)
   └── onConfirmClicked()
       └── navigate to MainView with {origin, destination, weights, constraints}

2. MainView calls fetchRoutes(params)            [src/utils/api.js]
   └── GET /api/routes?origin=...

3. FastAPI routes.py: get_routes()               [TripController]
   ├── Build TripRequest from query params
   ├── validateInputs() — check Singapore bounds, non-empty
   ├── DataFetchController.checkFreshness()
   │   └── For each DataSourceType: TTLCache.get() → fetch if expired
   └── RouteScoringController.generateRoutes(trip)
       ├── GoogleDirectionsProvider.fetchData(trip)
       │   └── googlemaps.directions(origin, destination, mode=['transit','driving'])
       ├── For each raw route:
       │   ├── build_route_steps() → List[RouteSegment]
       │   ├── DataFetchController.assessDelayRisks(segment)    × N
       │   ├── DataFetchController.assessCrowdingRisks(segment) × N
       │   ├── weather.get_weather_risk(route_coords)
       │   ├── erp.calculate_erp(polyline, departure_time)
       │   └── compute_realistic_time(duration, segments)
       ├── aggregate_route_risks(segments)
       ├── estimate_cost(route)
       ├── normalize([times, costs, risks, comforts])
       ├── composite_score(w_time, w_cost, w_risk, w_comfort)
       ├── rank_routes() — sort ascending by compositeScore
       ├── apply tie_break_key() for equal scores
       └── generateExplanation(route) for top-3

4. Response: RoutesResponse { routes: [RouteOption × 3] }

5. ResultsPage renders RouteCard × 3              [RouteResultUI]
   ├── showFallbackWarning() if any route.isFallback
   ├── RouteCard: rank badge, mode chain, score, time, cost
   │   ├── RiskBadge (delay + crowding)
   │   └── CrowdingHeatmap (if MRT segment)
   └── TimeCompare panel (Feature 1)
       └── fetchCompare() × 3 departure slots
```


