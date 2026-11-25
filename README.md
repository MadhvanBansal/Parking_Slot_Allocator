# Smart Parking Slot Allocator

A web-based parking-lot simulator that combines three ideas:

- **First-Fit and Best-Fit allocation** to choose a parking location.
- **Buddy-inspired slot sharing** to use a larger slot only when a dedicated slot is unavailable.
- **Machine learning** to choose either First-Fit or Best-Fit from the current parking-lot state.

The project uses Flask for the backend, SQLite for live parking data, HTML/CSS/JavaScript for the interface, and scikit-learn for the ML model.

## Project idea

The lot has three abstract capacity sizes:

| Vehicle | Size | Meaning |
|---|---:|---|
| Bike | 1 | Occupies one capacity unit. |
| Car | 2 | Occupies two adjacent capacity units. |
| SUV | 3 | Occupies all three units of an SUV-sized slot. |

A vehicle first receives a free whole slot of its own size. A larger slot is shared only after no dedicated whole slot of that size remains free.

For example, if every bike slot is occupied but an SUV slot `A2` is free:

```text
Before: A2 = [ free | free | free ]

Bike arrives
After:  A2 = [ bike | free | free ]
          A2.1
```

If a car then arrives and there is no whole car slot available:

```text
A2 = [ bike | car | car ]
       A2.1   A2.2
```

When the final vehicle leaves `A2`, it merges back into one free size-3 slot.

## System flow

```text
Browser form
    ↓
script.js sends a request to Flask
    ↓
back.py validates the request and checks the SQLite database
    ↓
ML Model / manually selected algorithm chooses First-Fit or Best-Fit
    ↓
Allocation function finds an exact slot or safe split range
    ↓
Booking is saved in SQLite
    ↓
API response updates the parking grid
```

## File responsibilities

| File | Role |
|---|---|
| `index.html` | Parking dashboard, entry form, exit form, slot grid, and legends. |
| `style.css` | Visual layout, vehicle-size colors, occupied state, and split-slot display. |
| `script.js` | Calls the Flask API, refreshes the grid every three seconds, and fills the exit form when an occupied slot is clicked. |
| `back.py` | Flask server, API routes, allocation rules, validation, and database updates. |
| `buddy.py` | Reusable functions for split checks, split-part labels, and finding a free range without overlap. |
| `init_db.py` | Creates/resets the SQLite database and inserts the 30 default slots. |
| `generate_dataset.py` | Generates 3,000 labelled ML training examples. |
| `train.py` | Trains candidate classifiers, selects the best test-accuracy model, and saves it as `model.pkl`. |
| `ml_model.py` | Loads `model.pkl` and predicts First-Fit or Best-Fit during a parking request. |

## Buddy helper functions (`buddy.py`)

`buddy.py` does not update the database itself. It returns small values that `back.py` uses while allocating a vehicle.

### `can_split(slot_size, vehicle_size)`

```python
return slot_size > vehicle_size
```

**Purpose:** checks whether a whole free slot is larger than the arriving vehicle.

| Call | Return | Meaning |
|---|---|---|
| `can_split(3, 1)` | `True` | A bike can share an SUV slot. |
| `can_split(3, 2)` | `True` | A car can share an SUV slot. |
| `can_split(2, 2)` | `False` | A car slot is already an exact fit. |
| `can_split(1, 2)` | `False` | A bike slot cannot fit a car. |

### `slot_label(slot_id, part_number)`

```python
return f"{slot_id}.{part_number}"
```

**Purpose:** creates the label shown to the user for a split part.

```text
slot_label("A2", 1) → "A2.1"
slot_label("A2", 3) → "A2.3"
```

### `find_free_start(slot_size, active_parts, vehicle_size)`

**Purpose:** finds the first continuous free range large enough for the arriving vehicle. This prevents two vehicles from being placed in the same part of a split slot.

Inputs:

```python
slot_size = 3
active_parts = [(0, 1)]   # a bike occupies position 0
vehicle_size = 2          # a car needs two adjacent positions
```

The function first marks occupied positions:

```text
Position:  0      1      2
State:     bike   free   free
```

It then scans from left to right and returns:

```python
1
```

This means the car can safely start at position 1 and occupy positions 1 and 2. If no continuous range fits, the function returns `None`.

## What `back.py` checks during parking

The `POST /api/allocate` route is the main entry point for parking a vehicle.

### 1. Input validation

The server checks that:

- a plate number exists;
- vehicle size is `1`, `2`, or `3`;
- the same plate does not already have an active booking.

An invalid request receives HTTP `400`.

### 2. Algorithm selection

The user can select First-Fit, Best-Fit, or ML Model.

- With **First-Fit** or **Best-Fit**, `back.py` directly calls the selected allocation function.
- With **ML Model**, `back.py` calculates current lot features and calls `ml_model.predict(...)`.

### 3. Exact-size slot check

Both allocation methods check for a free whole slot of the exact required size first.

```text
Bike arrives → look for free size-1 slot first.
Car arrives  → look for free size-2 slot first.
SUV arrives  → look for free size-3 slot first.
```

This is the key rule that prevents unnecessary splitting.

### 4. Split-slot check

If no exact whole slot exists, the allocator checks whether an existing split slot has a continuous free range. It calls:

```python
find_free_start(slot_size, active_parts, vehicle_size)
```

If the return value is an integer, that number becomes `part_start` in the database. If the return value is `None`, that split slot cannot fit the vehicle.

### 5. Split a larger whole slot

If neither an exact whole slot nor an existing split range can be used, a bike or car can use a larger free slot. The parent slot changes from `free` to `split`, and the new booking stores the starting position and its size.

### 6. Save the booking

For a whole-slot allocation:

```text
Slots.status = occupied
Bookings.part_start = NULL
Bookings.part_size = NULL
```

For a split allocation:

```text
Slots.status = split
Bookings.part_start = 0, 1, or 2
Bookings.part_size = 1 or 2
```

## First-Fit and Best-Fit

| Algorithm | Selection rule after exact-size slots are checked |
|---|---|
| First-Fit | Scans locations in parking-lot position order and uses the first safe usable space. |
| Best-Fit | Reuses the smallest suitable split slot first; otherwise splits the smallest larger whole slot. |

Both algorithms preserve dedicated slots first. The difference begins only when a dedicated slot is unavailable.

## ML model

The ML model does **not** choose a parking slot itself. It chooses which allocator should run:

```text
Current lot state → ML model → First-Fit or Best-Fit → allocation function → assigned slot
```

### Inputs passed to `ml_model.predict()`

| Feature | Meaning |
|---|---|
| `occupancy_rate` | Fraction of parent slots that are occupied or split. |
| `vehicle_size` | Size of the arriving vehicle: 1, 2, or 3. |
| `free_exact_slots` | Number of usable spaces that fit the vehicle, including split slots with a usable free range. |
| `free_larger_slots` | Number of free whole slots larger than the vehicle. |
| `split_slots_count` | Number of parent slots currently marked as split. |

`ml_model.py` creates a one-row pandas DataFrame with these feature names and runs:

```python
model.predict(sample)[0]
```

The returned value is either `"First-Fit"` or `"Best-Fit"`.

### Training

`generate_dataset.py` creates 3,000 sample parking states. High occupancy, fewer exact slots, more split slots, and larger vehicles tend to be labelled Best-Fit. Lower pressure tends to be labelled First-Fit.

`train.py` compares four classifiers:

- Decision Tree
- Logistic Regression
- Random Forest
- Gradient Boosting

It saves the classifier with the highest test accuracy as `model.pkl`. The current generated dataset produced a best test score of about **95.7%** for Gradient Boosting.

Accuracy here means: **how often the trained model matches the labels in the generated test data**. It does not independently prove that the selected strategy is optimal in a real commercial parking lot.

## Database design

SQLite database: `parking_system.db`

| Table | Stores |
|---|---|
| `Slots` | Parent slot ID, capacity size, status, and lot position. |
| `Vehicles` | Plate number and requested vehicle size. |
| `Bookings` | Vehicle-to-slot booking, arrival/exit time, algorithm used, and split-range details. |

For a split booking, the crucial fields are:

```text
slot_id     = A2
part_start  = 1
part_size   = 2
end_time    = NULL  ← vehicle is currently parked
```

When a vehicle exits, `end_time` receives the current timestamp. The server then checks active bookings for that parent slot:

- bookings remain → parent slot stays `split`;
- no bookings remain → parent slot becomes `free` again.

## API endpoints

| Method and path | Purpose |
|---|---|
| `GET /` | Serves the application page. |
| `GET /api/status` | Returns whole occupied slots, split parts, and lot statistics. |
| `POST /api/allocate` | Parks a vehicle. Requires `plate_number`, `vehicle_size`, and optional `algo`. |
| `POST /api/exit` | Removes a vehicle using `slot_id`, such as `A4` or `A2.3`. |

Example allocation body:

```json
{
  "plate_number": "DL8C1234",
  "vehicle_size": 2,
  "algo": "ML Model"
}
```

## Run the project

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a fresh database. This resets existing parking and booking data:

```bash
python3 init_db.py
```

Generate training data and train the model:

```bash
python3 generate_dataset.py
python3 train.py
```

Start the server:

```bash
python3 back.py
```

Open the application at [http://127.0.0.1:5001](http://127.0.0.1:5001).
