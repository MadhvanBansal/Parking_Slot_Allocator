# Parking Slot Allocator — Best-Fit

A smart parking lot management system that uses the **Best-Fit algorithm** to allocate slots to vehicles. Slots are mixed sizes so the algorithm visibly picks the tightest fit instead of just the first available one.

---

## How It Works

When a vehicle arrives, the system finds the free slot with the **minimum wasted space** after parking:

```
waste = slot_size - vehicle_size
```

The slot with the lowest waste is chosen. This is Best-Fit. First-Fit would just pick the first available slot regardless of size.

---

## Project Structure

```
├── back.py                      # Flask API server (Best-Fit logic lives here)
├── init_db.py                   # Run once to create the database and 30 slots
├── index.html                   # Frontend UI
├── style.css                    # Styling
├── script.js                    # Frontend logic (API calls, slot highlight)
├── requirements.txt             # Python dependencies
└── parking_system_simulator.sql # SQL schema reference (MySQL version)
```

---

## Setup & Run

### 1. Clone the repo

```bash
git clone https://github.com/MadhvanBansal/Parking_Slot_Allocator.git
cd Parking_Slot_Allocator
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Initialize the database (run only once)

```bash
python init_db.py
```

This creates `parking_system.db` with 30 mixed-size parking slots across 3 zones.

### 4. Start the backend server

```bash
python back.py
```

Server runs at `http://localhost:5001`

### 5. Open the frontend

Open `index.html` directly in your browser (no build step needed).

---

## Slot Layout

All 3 zones have mixed slot sizes so Best-Fit can visibly demonstrate choosing the tightest fit:

| Size | Represents | Visual |
|------|-----------|--------|
| 1    | Bike      | Small green slot |
| 2    | Car       | Medium blue slot |
| 3    | SUV       | Large purple slot |

When a vehicle is parked, the chosen slot gets a **golden glow** — this is visual proof that Best-Fit selected the slot with minimum waste, not just the first available one.

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/status` | Returns all currently occupied slot IDs |
| POST | `/api/allocate` | Parks a vehicle using Best-Fit |
| POST | `/api/exit` | Frees a slot when vehicle leaves |

### Example — Park a vehicle

```bash
curl -X POST http://localhost:5001/api/allocate \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "DL 8C 1234", "vehicle_size": 1}'
```

### Example — Exit a vehicle

```bash
curl -X POST http://localhost:5001/api/exit \
  -H "Content-Type: application/json" \
  -d '{"slot_id": "A1"}'
```

---

## Tech Stack

- **Backend:** Python, Flask, Flask-CORS, SQLite
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Algorithm:** Best-Fit (minimize waste = `slot_size - vehicle_size`)
