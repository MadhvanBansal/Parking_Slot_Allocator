from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# ---- Database se connection lena ----
def connect():
    db = sqlite3.connect('parking_system.db')
    db.row_factory = sqlite3.Row
    return db


# ---- Saare occupied slots frontend ko bhejo ----
@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        db = connect()
        cur = db.cursor()
        cur.execute("SELECT slot_id FROM Slots WHERE status = 'occupied'")
        taken = [row['slot_id'] for row in cur.fetchall()]
        return jsonify({"success": True, "occupied_slots": taken}), 200
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if 'db' in locals():
            db.close()


# ---- Vehicle park karo - Best-Fit algorithm use karke ----
@app.route('/api/allocate', methods=['POST'])
def park_vehicle():
    data = request.json
    vsize = data.get('vehicle_size')
    plate = data.get('plate_number')

    if not plate or not vsize:
        return jsonify({"success": False, "message": "Plate number ya size missing hai"}), 400

    try:
        db = connect()
        cur = db.cursor()

        # Gaadi pehle se parked toh nahi check karo
        cur.execute('''
            SELECT b.slot_id FROM Bookings b
            JOIN Vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE v.plate_number = ? AND b.end_time IS NULL
        ''', (plate,))
        already_parked = cur.fetchone()
        if already_parked:
            return jsonify({"success": False, "message": f"Gaadi pehle se slot {already_parked['slot_id']} mein hai"}), 400

        # Best-Fit: sabse kam waste wala free slot dhundho
        cur.execute(
            "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size >= ? ORDER BY (size - ?) ASC, position ASC LIMIT 1",
            (vsize, vsize)
        )
        chosen = cur.fetchone()

        if not chosen:
            return jsonify({"success": False, "message": "Koi bhi slot available nahi hai"}), 404

        slot = chosen['slot_id']
        slot_size = chosen['size']

        # Purani gaadi hai ya nayi - check karo
        cur.execute("SELECT vehicle_id FROM Vehicles WHERE plate_number = ?", (plate,))
        old = cur.fetchone()

        if old:
            vid = old['vehicle_id']
        else:
            cur.execute("INSERT INTO Vehicles (plate_number, size_needed) VALUES (?, ?)", (plate, vsize))
            vid = cur.lastrowid

        # Slot occupy karo aur booking record daalo
        cur.execute("UPDATE Slots SET status = 'occupied' WHERE slot_id = ?", (slot,))
        cur.execute("INSERT INTO Bookings (vehicle_id, slot_id, strategy_used) VALUES (?, ?, ?)", (vid, slot, 'Best-Fit'))

        db.commit()
        return jsonify({"success": True, "message": "Gaadi park ho gayi", "slot": {"id": slot, "size": slot_size}}), 200

    except sqlite3.Error as e:
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


# ---- Vehicle nikalo aur slot free karo ----
@app.route('/api/exit', methods=['POST'])
def remove_vehicle():
    data = request.json
    slot = data.get('slot_id')

    if not slot:
        return jsonify({"success": False, "message": "Slot ID missing hai"}), 400

    try:
        db = connect()
        cur = db.cursor()

        cur.execute('''
            SELECT booking_id FROM Bookings
            WHERE slot_id = ? AND end_time IS NULL
        ''', (slot,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"success": False, "message": f"Slot {slot} mein koi gaadi nahi hai"}), 404

        cur.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (slot,))
        cur.execute("UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?", (booking['booking_id'],))

        db.commit()
        return jsonify({"success": True, "message": "Gaadi nikal gayi", "slot_id": slot}), 200

    except sqlite3.Error as e:
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


# ---- Server start karo ----
if __name__ == '__main__':
    app.run(debug=True, port=5001)
