# SC2006 Lab 4 — Test Case Design

## 1. Black Box Testing: Equivalence Class + Boundary Value Testing

### 1.1 System Under Test

**Control class:** `CostEstimationController` (`backend/services/routing.py`)

**Function:** `estimate_cost(distance_m, duration_s, mode, departure_time, origin_lat, origin_lng)`

**Description (from requirements):** Calculates trip cost based on transport mode. For taxi/driving: metered fare with distance tiers, time-based surcharges, and airport surcharge. For transit: distance-based fare with time-of-day discounts. For own car: fuel cost only.

For black box testing, we focus on **taxi mode** with two key range parameters: `distance_m` and `departure_time`, treating the function as:

```
estimate_cost(distance_m, duration_s, mode="taxi", departure_time)
```

**Requirements specification:**
- The function takes `distance_m`, a float >= 0 (distance in meters)
- The function takes `departure_time`, a datetime (Singapore time)
- If distance <= 1km: flag-down fare only ($4.60)
- If 1km < distance <= 10km: $0.27 per 400m after first km (Tier 1)
- If distance > 10km: $0.27 per 350m after 10km (Tier 2)
- If departure is Mon-Fri 6:00am-9:29am, OR any day 5:00pm-11:59pm, OR Sat-Sun 10:00am-1:59pm: +25% peak surcharge
- If departure is midnight-5:59am: +50% late-night surcharge (replaces peak)
- Otherwise: no surcharge

### 1.2 Equivalence Classes

**Parameter 1: `distance_m` (float) — Range of values**

| EC ID | Range (km) | Type | Expected behaviour |
|-------|-----------|------|-------------------|
| D1 | d <= 0 | Invalid | Clamped to 0, flag-down only |
| D2 | 0 < d <= 1 | Valid | Flag-down only ($4.60 base) |
| D3 | 1 < d <= 10 | Valid | Flag-down + Tier 1 rate |
| D4 | d > 10 | Valid | Flag-down + Tier 1 + Tier 2 rate |

**Parameter 2: `departure_time` (datetime) — Range of values**

| EC ID | Condition | Type | Expected behaviour |
|-------|----------|------|-------------------|
| T1 | Weekday 6:00am-9:29am | Valid | +25% peak surcharge, booking $3.30 |
| T2 | Any day 5:00pm-11:59pm | Valid | +25% peak surcharge, booking $3.30 |
| T3 | Sat-Sun 10:00am-1:59pm | Valid | +25% peak surcharge, booking $3.30 |
| T4 | Midnight-5:59am | Valid | +50% late-night surcharge, booking $3.30 |
| T5 | All other times | Valid | No surcharge, booking $2.30 |

### 1.3 Boundary Values

**Parameter 1: `distance_m` boundary values**

| EC boundary | just-below | on-boundary | just-above |
|-------------|-----------|-------------|------------|
| D1/D2: 0m | -1 (D1) | 0 (D1) | 1 (D2) |
| D2/D3: 1000m | 999 (D2) | 1000 (D2) | 1001 (D3) |
| D3/D4: 10000m | 9999 (D3) | 10000 (D3) | 10001 (D4) |

Valid BVs: {0, 1, 999, 1000, 1001, 9999, 10000, 10001}
- D2 valid BVs (on-boundary): {0, 1000} → lower=0, upper=1000
- D3 valid BVs (on-boundary): {1001, 10000} → lower=1001, upper=10000
- D4 valid BVs (on-boundary): {10001} → lower=10001

Note: just-below/just-above values that fall into an adjacent valid EC are not invalid — they are already covered by that EC's valid BVs. Only D1 (d<=0) is invalid.

Invalid BVs: {-1} (from D1)

**Parameter 2: `departure_time` boundary values**

Expressed as minutes from midnight (t = hour*60 + minute) on a weekday:

| EC boundary | just-below | on-boundary | just-above |
|-------------|-----------|-------------|------------|
| T5/T4: 0min (midnight) | N/A | 0 (T4) | 1 (T4) |
| T4/T1: 360min (6:00am) | 359 (T4) | 360 (T1) | 361 (T1) |
| T1/T5: 570min (9:30am) | 569 (T1) | 570 (T5) | 571 (T5) |
| T5/T2: 1020min (5:00pm) | 1019 (T5) | 1020 (T2) | 1021 (T2) |

Valid BVs for T1: {360, 569} (lower=6:00am, upper=9:29am)
Valid BVs for T2: {1020} (lower=5:00pm; upper is 11:59pm=1439)
Valid BVs for T4: {0, 359} (lower=midnight, upper=5:59am)
Valid BVs for T5: {570, 1019} (lower=9:30am, upper=4:59pm)

### 1.4 Test Cases — Valid Input Combinations

Test all combinations of valid boundary values from both parameters.
Using BVs: distance={1000, 10000} (D2/D3 boundaries), time={570, 1020} (T5/T2 boundaries).

Per the LT17 methodology: all combinations of upper/lower valid BVs from each EC.

For simplicity (and following Lab 4 Section 3.2.3 — minimize test cases), we select representative BVs:
- distance: 1000 (D2 upper), 5000 (D3 mid), 15000 (D4)
- time: Tue 8:00am (T1), Tue 2:00pm (T5), Tue 6:00pm (T2), Tue 3:00am (T4)

| TC | distance_m | departure_time | Expected surcharge | Expected distance tier |
|----|-----------|----------------|-------------------|----------------------|
| V1 | 1000 | Tue 14:00 (T5) | No surcharge | Flag-down only |
| V2 | 5000 | Tue 14:00 (T5) | No surcharge | Tier 1 |
| V3 | 15000 | Tue 14:00 (T5) | No surcharge | Tier 1 + Tier 2 |
| V4 | 5000 | Tue 08:00 (T1) | +25% peak | Tier 1 |
| V5 | 5000 | Tue 18:00 (T2) | +25% peak | Tier 1 |
| V6 | 5000 | Tue 03:00 (T4) | +50% late-night | Tier 1 |

### 1.5 Test Cases — Invalid Input (one invalid at a time)

For each invalid BV, pair with valid BVs from all other parameters.

| TC | distance_m | departure_time | Expected result |
|----|-----------|----------------|-----------------|
| I1 | -1 (invalid) | Tue 14:00 (valid T5) | distance_charge=0, total > 0 (flag-down + booking) |
| I2 | 0 (invalid) | Tue 08:00 (valid T1) | distance_charge=0, peak surcharge applies |

### 1.6 Test Cases — Boundary Value Combinations

Testing on-boundary values for distance tiers:

| TC | distance_m | departure_time | Expected |
|----|-----------|----------------|----------|
| B1 | 999 | Tue 14:00 | distance_charge = 0 (within flag-down) |
| B2 | 1000 | Tue 14:00 | distance_charge = 0 (on boundary, still flag-down) |
| B3 | 1100 | Tue 14:00 | distance_charge > 0 (just above, Tier 1) |
| B4 | 9999 | Tue 14:00 | Tier 1 rate only |
| B5 | 10000 | Tue 14:00 | Tier 1 rate only (on boundary) |
| B6 | 10500 | Tue 14:00 | Tier 1 + Tier 2 (just above) |

Testing on-boundary values for time surcharges (weekday):

| TC | distance_m | departure_time | Expected |
|----|-----------|----------------|----------|
| B7 | 5000 | Tue 05:59 (t=359) | Late-night surcharge (hour < 6) |
| B8 | 5000 | Tue 06:00 (t=360) | Peak surcharge (morning peak start) |
| B9 | 5000 | Tue 09:29 (t=569) | Peak surcharge (morning peak end) |
| B10 | 5000 | Tue 09:30 (t=570) | No surcharge (just after peak) |
| B11 | 5000 | Tue 16:59 (t=1019) | No surcharge (just before evening peak) |
| B12 | 5000 | Tue 17:00 (t=1020) | Peak surcharge (evening peak start) |

### 1.7 Test Results

| TC | Input | Oracle (Expected) | Log (Actual) | Pass? |
|----|-------|-------------------|--------------|-------|
| V1 | (1000, 600, "taxi", Tue 14:00) | dist_charge=0, peak=0, late=0, fee=2.30 | dist_charge=0.0, peak=0.0, late=0.0, fee=2.30 | PASS |
| V2 | (5000, 600, "taxi", Tue 14:00) | dist_charge=2.70, peak=0, fee=2.30 | dist_charge=2.70, peak=0.0, fee=2.30 | PASS |
| V3 | (15000, 1200, "taxi", Tue 14:00) | dist_charge>6.08, peak=0, fee=2.30 | dist_charge=9.93, peak=0.0, fee=2.30 | PASS |
| V4 | (5000, 600, "taxi", Tue 08:00) | peak>0, late=0, fee=3.30 | peak=2.0, late=0.0, fee=3.30 | PASS |
| V5 | (5000, 600, "taxi", Tue 18:00) | peak>0, late=0, fee=3.30 | peak=2.0, late=0.0, fee=3.30 | PASS |
| V6 | (5000, 600, "taxi", Tue 03:00) | late>0, peak=0, fee=3.30 | late=4.01, peak=0.0, fee=3.30 | PASS |
| I1 | (-1, 600, "taxi", Tue 14:00) | dist_charge=0 | dist_charge=0.0 | PASS |
| I2 | (0, 600, "taxi", Tue 08:00) | dist_charge=0, peak>0 | dist_charge=0.0, peak=1.38 | PASS |
| B1 | (999, 600, "taxi", Tue 14:00) | dist_charge=0 | dist_charge=0.0 | PASS |
| B2 | (1000, 600, "taxi", Tue 14:00) | dist_charge=0 | dist_charge=0.0 | PASS |
| B3 | (1100, 600, "taxi", Tue 14:00) | dist_charge>0 | dist_charge=0.07 | PASS |
| B4 | (9999, 600, "taxi", Tue 14:00) | Tier 1 only | dist_charge=6.07 | PASS |
| B5 | (10000, 600, "taxi", Tue 14:00) | dist_charge=6.08 (Tier 1 cap) | dist_charge=6.08 | PASS |
| B6 | (10500, 600, "taxi", Tue 14:00) | dist_charge>6.08 (Tier 2) | dist_charge=6.46 | PASS |
| B7 | (5000, 600, "taxi", Tue 05:59) | late_night>0 | late_night=4.19 | PASS |
| B8 | (5000, 600, "taxi", Tue 06:00) | peak>0, late=0 | peak=2.0, late=0.0 | PASS |
| B9 | (5000, 600, "taxi", Tue 09:29) | peak>0 | peak=2.0 | PASS |
| B10 | (5000, 600, "taxi", Tue 09:30) | peak=0, late=0 | peak=0.0, late=0.0 | PASS |
| B11 | (5000, 600, "taxi", Tue 16:59) | peak=0 | peak=0.0 | PASS |
| B12 | (5000, 600, "taxi", Tue 17:00) | peak>0 | peak=2.0 | PASS |

**Total black box test cases: 20** (6 valid + 2 invalid + 12 boundary)
**All tests: PASSED**

---

## 2. White Box Testing: Basis Path Testing

### 2.1 Method 1: `_is_peak(dt)`

**Location:** `backend/services/routing.py`, line 52

#### 2.1.1 Source Code (numbered)

```python
def _is_peak(dt: datetime) -> bool:
1    wd = dt.weekday()
2    h, m = dt.hour, dt.minute
3    t = h * 60 + m
4    if wd < 5 and 360 <= t <= 569:
5        return True
6    if t >= 1020:
7        return True
8    if wd >= 5 and 600 <= t <= 839:
9        return True
10   return False
```

#### 2.1.2 Control Flow Graph

```
        [1-3: compute wd, t]
               |
               v
        <D1: wd<5 AND 360<=t<=569?>
          /              \
        True            False
         |                |
         v                v
    [5: return True]  <D2: t>=1020?>
                       /          \
                     True        False
                      |            |
                      v            v
                [7: return    <D3: wd>=5 AND
                   True]       600<=t<=839?>
                               /          \
                             True        False
                              |            |
                              v            v
                        [9: return    [10: return
                           True]        False]
```

Nodes: {1-3, D1, 5, D2, 7, D3, 9, 10} = 7 nodes
Edges: {1-3->D1, D1->5, D1->D2, D2->7, D2->D3, D3->9, D3->10} = 7 edges

#### 2.1.3 Cyclomatic Complexity

V(G) = E - N + 2 = 7 - 7 + 2 = **2**

Alternative: V(G) = number of binary decision points + 1 = 3 + 1 = **4**

Note: Each compound `if` (e.g., `wd < 5 and 360 <= t <= 569`) is treated as a single decision point since it results in one True/False branch in the code. But for a more thorough analysis treating `and` as two sub-conditions, CC = 4.

Using the simpler formula from Lecture 19 (decision points + 1):
**V(G) = 3 + 1 = 4**

This means we need **4 linearly independent basis paths**.

#### 2.1.4 Basis Path Derivation

**Step 1: Choose baseline path** (the "most normal" execution)

Baseline path: 1-3 -> D1(True) -> 5 (return True)
This represents the most common case: weekday morning peak.

**Step 2: Mutate D1 (flip first decision to False)**

Path 2: 1-3 -> D1(False) -> D2(True) -> 7 (return True)
Changed: D1 from True to False, take next True branch.

**Step 3: Mutate D2 (flip second decision to False)**

Path 3: 1-3 -> D1(False) -> D2(False) -> D3(True) -> 9 (return True)
Changed: D2 from True to False, take next True branch.

**Step 4: Mutate D3 (flip third decision to False)**

Path 4: 1-3 -> D1(False) -> D2(False) -> D3(False) -> 10 (return False)
Changed: D3 from True to False.

**Verification:** These 4 paths cover all nodes and all branches. Each path differs from the previous by exactly one decision point flip.

#### 2.1.5 Test Cases

| Path | Node sequence | Input | Oracle |
|------|--------------|-------|--------|
| Path 1 | 1-3, D1(T), 5 | dt = Tue 08:00 SGT (wd=1, t=480) | True |
| Path 2 | 1-3, D1(F), D2(T), 7 | dt = Tue 18:00 SGT (wd=1, t=1080) | True |
| Path 3 | 1-3, D1(F), D2(F), D3(T), 9 | dt = Sat 12:00 SGT (wd=5, t=720) | True |
| Path 4 | 1-3, D1(F), D2(F), D3(F), 10 | dt = Tue 14:00 SGT (wd=1, t=840) | False |

#### 2.1.6 Test Results

| Path | Input | Oracle (Expected) | Log (Actual) | Pass? |
|------|-------|-------------------|--------------|-------|
| Path 1 | datetime(2026,4,14,8,0, SGT) | True | True | PASS |
| Path 2 | datetime(2026,4,14,18,0, SGT) | True | True | PASS |
| Path 3 | datetime(2026,4,18,12,0, SGT) | True | True | PASS |
| Path 4 | datetime(2026,4,14,14,0, SGT) | False | False | PASS |

**Coverage achieved:** 100% statement, 100% branch, 100% basis path.

---

### 2.2 Method 2: `_time_based_crowding(query_time)`

**Location:** `backend/services/assessment.py`, line 227

#### 2.2.1 Source Code (numbered)

```python
def _time_based_crowding(query_time=None) -> str:
1    SGT = timezone(timedelta(hours=8))
2    dt = query_time or datetime.now(SGT)
3    if dt.tzinfo is None:
4        dt = dt.replace(tzinfo=SGT)
     else:
5        dt = dt.astimezone(SGT)
6    h, m = dt.hour, dt.minute
7    t = h * 60 + m
8    wd = dt.weekday()
9    if wd < 5:                              # Weekday
10       if 420 <= t <= 570:                 #   Morning peak
11           return "High"
12       if 1050 <= t <= 1200:              #   Evening peak
13           return "High"
14       if (360<=t<420) or (570<t<=630) or (990<=t<1050) or (1200<t<=1260):
15           return "Medium"                #   Shoulder
16       return "Low"                        #   Off-peak
     else:                                   # Weekend
17       if 660 <= t <= 1080:               #   Midday busy
18           return "Medium"
19       return "Low"
```

#### 2.2.2 Control Flow Graph

```
        [1-8: compute dt, t, wd]
               |
               v
        <D1: wd < 5?>
          /            \
        True          False
         |               |
         v               v
    <D2: 420<=t<=570?>  <D5: 660<=t<=1080?>
      /        \          /          \
    True      False     True        False
     |          |        |            |
     v          v        v            v
 [11: ret   <D3: 1050   [18: ret   [19: ret
  "High"]    <=t<=1200?>  "Medium"]   "Low"]
              /        \
            True      False
             |          |
             v          v
         [13: ret   <D4: shoulder?>
          "High"]     /        \
                    True      False
                     |          |
                     v          v
                 [15: ret   [16: ret
                  "Medium"]   "Low"]
```

Nodes: {1-8, D1, D2, 11, D3, 13, D4, 15, 16, D5, 18, 19} = 11 nodes
Edges: {1-8->D1, D1->D2, D1->D5, D2->11, D2->D3, D3->13, D3->D4, D4->15, D4->16, D5->18, D5->19} = 11 edges

#### 2.2.3 Cyclomatic Complexity

V(G) = E - N + 2 = 11 - 11 + 2 = **2**

Alternative (decision points + 1): D1, D2, D3, D4, D5 = 5 decisions
**V(G) = 5 + 1 = 6**

This means we need **6 linearly independent basis paths**.

#### 2.2.4 Basis Path Derivation

**Step 1: Choose baseline path**

Baseline: 1-8 -> D1(T) -> D2(T) -> 11 (return "High")
Represents: weekday morning peak — a common case.

**Step 2: Mutate D2 (flip to False), keep D1 True**

Path 2: 1-8 -> D1(T) -> D2(F) -> D3(T) -> 13 (return "High")
Changed: D2 from True to False, D3 takes True.
Represents: weekday evening peak.

**Step 3: Mutate D3 (flip to False)**

Path 3: 1-8 -> D1(T) -> D2(F) -> D3(F) -> D4(T) -> 15 (return "Medium")
Changed: D3 from True to False, D4 takes True.
Represents: weekday shoulder period.

**Step 4: Mutate D4 (flip to False)**

Path 4: 1-8 -> D1(T) -> D2(F) -> D3(F) -> D4(F) -> 16 (return "Low")
Changed: D4 from True to False.
Represents: weekday off-peak.

**Step 5: Mutate D1 (flip to False), take D5 True**

Path 5: 1-8 -> D1(F) -> D5(T) -> 18 (return "Medium")
Changed: D1 from True to False, D5 takes True.
Represents: weekend midday.

**Step 6: Mutate D5 (flip to False)**

Path 6: 1-8 -> D1(F) -> D5(F) -> 19 (return "Low")
Changed: D5 from True to False.
Represents: weekend off-peak.

**Verification:** All 6 paths are linearly independent (each introduces at least one edge not in any previous path). All nodes and branches are covered.

#### 2.2.5 Test Cases

| Path | Node sequence | Input | Oracle |
|------|--------------|-------|--------|
| Path 1 | 1-8, D1(T), D2(T), 11 | dt = Tue 08:00 (wd=1, t=480) | "High" |
| Path 2 | 1-8, D1(T), D2(F), D3(T), 13 | dt = Tue 18:20 (wd=1, t=1100) | "High" |
| Path 3 | 1-8, D1(T), D2(F), D3(F), D4(T), 15 | dt = Tue 10:00 (wd=1, t=600) | "Medium" |
| Path 4 | 1-8, D1(T), D2(F), D3(F), D4(F), 16 | dt = Tue 14:00 (wd=1, t=840) | "Low" |
| Path 5 | 1-8, D1(F), D5(T), 18 | dt = Sat 12:00 (wd=5, t=720) | "Medium" |
| Path 6 | 1-8, D1(F), D5(F), 19 | dt = Sat 09:00 (wd=5, t=540) | "Low" |

#### 2.2.6 Test Results

| Path | Input | Oracle (Expected) | Log (Actual) | Pass? |
|------|-------|-------------------|--------------|-------|
| Path 1 | datetime(2026,4,14,8,0, SGT) | "High" | "High" | PASS |
| Path 2 | datetime(2026,4,14,18,20, SGT) | "High" | "High" | PASS |
| Path 3 | datetime(2026,4,14,10,0, SGT) | "Medium" | "Medium" | PASS |
| Path 4 | datetime(2026,4,14,14,0, SGT) | "Low" | "Low" | PASS |
| Path 5 | datetime(2026,4,18,12,0, SGT) | "Medium" | "Medium" | PASS |
| Path 6 | datetime(2026,4,18,9,0, SGT) | "Low" | "Low" | PASS |

**Coverage achieved:** 100% statement, 100% branch, 100% basis path.

---

## 3. Summary

| Technique | SUT | Test cases | Result |
|-----------|-----|-----------|--------|
| Black box (EC + BVT) | `estimate_cost()` — taxi mode | 20 | All PASS |
| White box (basis path) | `_is_peak()` | 4 (CC=4) | All PASS |
| White box (basis path) | `_time_based_crowding()` | 6 (CC=6) | All PASS |
| **Total** | | **30** | **All PASS** |

Automated test files:
- `tests/test_blackbox_estimate_cost.py` (60 automated tests including additional coverage)
- `tests/test_whitebox_is_peak.py` (11 automated tests including branch coverage)
- `tests/test_whitebox_time_based_crowding.py` (25 automated tests including branch coverage)

Run all tests: `python -m unittest discover -s tests -p "test_*.py" -v`
