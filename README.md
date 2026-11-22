# Smart Parking Slot Allocator — Buddy System & ML

A simple parking lot management system using the **OS Buddy System** for slot splitting and merging, with a **Machine Learning model** that selects between **First-Fit** and **Best-Fit**.

---

## Features

1. **Buddy System:**
   * Bike (Size 1) = 1 bay
   * Car (Size 2) = 2 bays
   * SUV (Size 3) = 4 bays
   * If a bike or car has no free slot of its own size, a larger slot splits in half (e.g. `B1.1`, `B1.2`).
   * When all parts of a split slot become free, they merge back into one whole slot.

2. **Algorithm Options:**
   * **ML Model:** Checks current lot occupancy and free slots to pick between First-Fit and Best-Fit.
   * **Best-Fit:** Selects the slot with minimum wasted space.
   * **First-Fit:** Selects the first available slot by position.

3. **Separate Dataset & Model Training:**
   * `generate_dataset.py`: Generates `parking_dataset.csv` using pandas.
   * `train.py`: Loads the CSV with pandas, trains a scikit-learn DecisionTreeClassifier, and saves `model.pkl` using pickle.
   * `ml_model.py`: Loads `model.pkl` and runs predictions during allocation requests.

---

## How to Run

1. **Initialize Database:**
   ```bash
   python init_db.py
   ```

2. **Train Model (Optional):**
   ```bash
   python generate_dataset.py
   python train.py
   ```

3. **Start Server:**
   ```bash
   python back.py
   ```

4. **Open in Browser:**
   Go to: `http://127.0.0.1:5001`
